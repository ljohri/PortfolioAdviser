from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from app.adapters.current_market import CurrentMarketAdapter
from app.adapters.datalake import DatalakeAdapter, DatalakeBar
from app.models import ScreenRequest, ScreenResponse, ScreenedSymbol, SymbolEvidence, ValidationResponse
from app.services.rules import (
    evaluate_average_volume,
    evaluate_drawdown,
    evaluate_momentum,
    evaluate_moving_average_relationship,
    evaluate_price_range,
)


class ScreenerEngine:
    def __init__(self, *, datalake_adapter: DatalakeAdapter, current_market_adapter: CurrentMarketAdapter) -> None:
        self._datalake = datalake_adapter
        self._current_market = current_market_adapter

    def parse_criteria(self, payload: dict) -> ScreenRequest:
        return ScreenRequest.model_validate(payload)

    def required_history_days(self, request: ScreenRequest) -> int:
        windows = [2]
        rules = request.rules
        if rules.average_volume:
            windows.append(rules.average_volume.window_days)
        if rules.momentum:
            windows.append(rules.momentum.window_days + 1)
        if rules.drawdown:
            windows.append(rules.drawdown.window_days)
        if rules.moving_average:
            windows.append(rules.moving_average.long_window_days)
        return max(windows)

    def validate_criteria(self, request: ScreenRequest) -> ValidationResponse:
        required_days = self.required_history_days(request)
        range_days = (request.end_date - request.start_date).days + 1
        warnings: list[str] = []
        if range_days < required_days:
            warnings.append(
                "Requested date range may not contain enough bars for all rules; symbols may be filtered out."
            )
        return ValidationResponse(
            valid=True,
            required_history_days=required_days,
            parsed_rules=request.rules,
            warnings=warnings,
        )

    def run(self, request: ScreenRequest) -> ScreenResponse:
        normalized_symbols = self._datalake.normalize_symbol_universe(
            symbols=request.symbols,
            source=request.source.model_dump(by_alias=True),
        )
        if not normalized_symbols:
            return ScreenResponse(
                screened_symbols=[],
                selected_symbols=[],
                universe_size=0,
                selected_count=0,
                required_history_days=self.required_history_days(request),
            )

        required_days = self.required_history_days(request)
        query_start = request.start_date - timedelta(days=max(required_days * 2, required_days + 30))
        bars = self._datalake.load_bars(
            symbols=normalized_symbols,
            start_date=query_start,
            end_date=request.end_date,
            source=request.source.model_dump(by_alias=True),
        )
        bars_by_symbol: dict[str, list[DatalakeBar]] = defaultdict(list)
        for bar in bars:
            bars_by_symbol[bar.symbol].append(bar)

        current_prices = {symbol.upper(): float(price) for symbol, price in request.current_prices.items()}
        missing_for_current = [symbol for symbol in normalized_symbols if symbol not in current_prices]
        if request.current_api_base_url and missing_for_current:
            fetched = self._current_market.get_current_prices(
                symbols=missing_for_current,
                base_url=request.current_api_base_url,
            )
            current_prices.update(fetched)

        screened: list[ScreenedSymbol] = []
        selected: list[str] = []
        for symbol in normalized_symbols:
            symbol_bars = [bar for bar in bars_by_symbol.get(symbol, []) if request.start_date <= bar.trading_date <= request.end_date]
            if not symbol_bars:
                if request.include_failed_symbols:
                    screened.append(
                        ScreenedSymbol(
                            symbol=symbol,
                            passed=False,
                            evidence=SymbolEvidence(rule_results={"insufficient_history": False}),
                        )
                    )
                continue

            prices = [bar.close_price for bar in symbol_bars]
            volumes = [bar.volume for bar in symbol_bars if bar.volume is not None]
            evidence = SymbolEvidence(rule_results={})
            passed = True

            latest_price = current_prices.get(symbol, prices[-1])
            evidence.latest_price = latest_price

            if request.rules.price_range:
                result = evaluate_price_range(
                    price=latest_price,
                    min_price=request.rules.price_range.min_price,
                    max_price=request.rules.price_range.max_price,
                )
                evidence.rule_results["price_range"] = result
                passed = passed and result

            if request.rules.average_volume:
                lookback = request.rules.average_volume.window_days
                if len(volumes) < lookback:
                    result = False
                    average_volume = 0.0
                else:
                    result, average_volume = evaluate_average_volume(
                        volumes=volumes[-lookback:],
                        min_average_volume=request.rules.average_volume.min_average_volume,
                    )
                evidence.average_volume = average_volume
                evidence.rule_results["average_volume"] = result
                passed = passed and result

            if request.rules.momentum:
                lookback = request.rules.momentum.window_days + 1
                if len(prices) < lookback:
                    result = False
                    momentum = 0.0
                else:
                    result, momentum = evaluate_momentum(
                        prices=prices[-lookback:],
                        min_return=request.rules.momentum.min_return,
                        max_return=request.rules.momentum.max_return,
                    )
                evidence.momentum_return = momentum
                evidence.rule_results["momentum"] = result
                passed = passed and result

            if request.rules.drawdown:
                lookback = request.rules.drawdown.window_days
                if len(prices) < lookback:
                    result = False
                    max_drawdown_pct = 1.0
                else:
                    result, max_drawdown_pct = evaluate_drawdown(
                        prices=prices[-lookback:],
                        max_drawdown_pct=request.rules.drawdown.max_drawdown_pct,
                    )
                evidence.max_drawdown_pct = max_drawdown_pct
                evidence.rule_results["drawdown"] = result
                passed = passed and result

            if request.rules.moving_average:
                short_window = request.rules.moving_average.short_window_days
                long_window = request.rules.moving_average.long_window_days
                if len(prices) < long_window:
                    result = False
                    short_ma = 0.0
                    long_ma = 0.0
                else:
                    result, short_ma, long_ma = evaluate_moving_average_relationship(
                        prices=prices,
                        short_window_days=short_window,
                        long_window_days=long_window,
                        relation=request.rules.moving_average.relation,
                    )
                evidence.short_moving_average = short_ma
                evidence.long_moving_average = long_ma
                evidence.moving_average_relation = request.rules.moving_average.relation
                evidence.rule_results["moving_average"] = result
                passed = passed and result

            screened_symbol = ScreenedSymbol(symbol=symbol, passed=passed, evidence=evidence)
            if passed:
                selected.append(symbol)
            if passed or request.include_failed_symbols:
                screened.append(screened_symbol)

        return ScreenResponse(
            screened_symbols=screened,
            selected_symbols=selected,
            universe_size=len(normalized_symbols),
            selected_count=len(selected),
            required_history_days=required_days,
        )
