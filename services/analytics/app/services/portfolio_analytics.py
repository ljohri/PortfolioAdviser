from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from app.adapters.datalake import DatalakeAdapter
from app.exports.parquet_export import export_rows_to_parquet
from app.models import MetricRow, PortfolioReport
from app.services.metrics import daily_returns, max_drawdown, rolling_return, rolling_volatility


class PortfolioAnalyticsService:
    def __init__(self, *, adapter: DatalakeAdapter, artifacts_dir: str) -> None:
        self._adapter = adapter
        self._artifacts_dir = Path(artifacts_dir)

    def normalize_universe(self, *, symbols: list[str], source: dict) -> list[str]:
        return self._adapter.normalize_symbol_universe(symbols=symbols, source=source)

    def analyze(
        self,
        *,
        job_id: str,
        symbols: list[str],
        source: dict,
        start_date: date,
        end_date: date,
        rolling_window_days: int,
        top_n: int,
        data_mode: str,
        current_prices: dict[str, float],
        export_parquet: bool,
    ) -> PortfolioReport:
        prices_by_symbol: dict[str, list[float]] = defaultdict(list)
        data_sources_used: list[str] = []
        current_prices_used = 0
        if data_mode in {"historical", "blended"}:
            bars = self._adapter.load_bars(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                source=source,
            )
            for bar in bars:
                prices_by_symbol[bar.symbol].append(bar.close_price)
            if bars:
                data_sources_used.append("historical")
        if data_mode in {"current", "blended"}:
            normalized_prices = {symbol.upper(): float(price) for symbol, price in current_prices.items()}
            for symbol in symbols:
                if symbol not in normalized_prices:
                    continue
                if data_mode == "current":
                    prices_by_symbol[symbol] = [normalized_prices[symbol]]
                else:
                    prices_by_symbol[symbol].append(normalized_prices[symbol])
                current_prices_used += 1
            if current_prices_used > 0:
                data_sources_used.append("current")

        metrics_rows: list[MetricRow] = []
        for symbol, prices in prices_by_symbol.items():
            if data_mode == "current":
                current_price = prices[-1]
                metrics_rows.append(
                    MetricRow(
                        symbol=symbol,
                        latest_rolling_return=0.0,
                        latest_rolling_volatility=0.0,
                        max_drawdown=0.0,
                        momentum_rank=0,
                        risk_adjusted_rank=0,
                        composite_score=current_price,
                        composite_rank=0,
                    )
                )
                continue
            if len(prices) < rolling_window_days + 1:
                continue
            returns = daily_returns(prices)
            symbol_rolling_return = rolling_return(prices, window=rolling_window_days)
            symbol_rolling_volatility = rolling_volatility(returns, window=rolling_window_days)
            if not symbol_rolling_return or not symbol_rolling_volatility:
                continue
            latest_return = symbol_rolling_return[-1]
            latest_vol = symbol_rolling_volatility[-1]
            drawdown = max_drawdown(prices)
            risk_adjusted = latest_return / latest_vol if latest_vol > 0 else latest_return
            composite = (0.5 * latest_return) + (0.3 * risk_adjusted) + (0.2 * drawdown)
            metrics_rows.append(
                MetricRow(
                    symbol=symbol,
                    latest_rolling_return=latest_return,
                    latest_rolling_volatility=latest_vol,
                    max_drawdown=drawdown,
                    momentum_rank=0,
                    risk_adjusted_rank=0,
                    composite_score=composite,
                    composite_rank=0,
                )
            )

        if not metrics_rows:
            return PortfolioReport(
                job_id=job_id,
                generated_at=datetime.now(timezone.utc).isoformat(),
                analysis_mode=data_mode,
                source_mode=source.get("mode", "unknown"),
                data_sources_used=data_sources_used,
                current_prices_used=current_prices_used,
                start_date=start_date,
                end_date=end_date,
                rolling_window_days=rolling_window_days,
                symbols=symbols,
                ranking=[],
                portfolio_input_rows=[],
                parquet_path=None,
            )

        momentum_order = sorted(metrics_rows, key=lambda item: item.latest_rolling_return, reverse=True)
        risk_adjusted_order = sorted(
            metrics_rows,
            key=lambda item: item.latest_rolling_return / item.latest_rolling_volatility
            if item.latest_rolling_volatility > 0
            else item.latest_rolling_return,
            reverse=True,
        )
        composite_order = sorted(metrics_rows, key=lambda item: item.composite_score, reverse=True)
        for rank, row in enumerate(momentum_order, start=1):
            row.momentum_rank = rank
        for rank, row in enumerate(risk_adjusted_order, start=1):
            row.risk_adjusted_rank = rank
        for rank, row in enumerate(composite_order, start=1):
            row.composite_rank = rank

        top_rows = composite_order[:top_n]
        portfolio_input_rows = [
            {
                "symbol": row.symbol,
                "latest_rolling_return": row.latest_rolling_return,
                "latest_rolling_volatility": row.latest_rolling_volatility,
                "max_drawdown": row.max_drawdown,
                "momentum_rank": float(row.momentum_rank),
                "risk_adjusted_rank": float(row.risk_adjusted_rank),
                "composite_score": row.composite_score,
                "composite_rank": float(row.composite_rank),
            }
            for row in top_rows
        ]

        parquet_path: str | None = None
        if export_parquet:
            parquet_path = export_rows_to_parquet(
                self._adapter.connection,
                rows=portfolio_input_rows,
                output_path=str(self._artifacts_dir / f"{job_id}-portfolio-input.parquet"),
            )

        return PortfolioReport(
            job_id=job_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            analysis_mode=data_mode,
            source_mode=source.get("mode", "unknown"),
            data_sources_used=data_sources_used,
            current_prices_used=current_prices_used,
            start_date=start_date,
            end_date=end_date,
            rolling_window_days=rolling_window_days,
            symbols=symbols,
            ranking=top_rows,
            portfolio_input_rows=portfolio_input_rows,
            parquet_path=parquet_path,
        )
