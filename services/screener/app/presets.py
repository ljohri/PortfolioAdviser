from __future__ import annotations

from app.models import PresetDefinition, ScreenRules


def get_presets() -> list[PresetDefinition]:
    return [
        PresetDefinition(
            key="liquid_momentum",
            name="Liquid Momentum",
            description="Price and volume constrained momentum screen.",
            rules=ScreenRules.model_validate(
                {
                    "price_range": {"min_price": 10, "max_price": 500},
                    "average_volume": {"min_average_volume": 1_000_000, "window_days": 20},
                    "momentum": {"window_days": 20, "min_return": 0.03},
                    "moving_average": {"short_window_days": 20, "long_window_days": 50, "relation": "above"},
                }
            ),
        ),
        PresetDefinition(
            key="steady_uptrend",
            name="Steady Uptrend",
            description="Trend-following candidates with controlled drawdown.",
            rules=ScreenRules.model_validate(
                {
                    "momentum": {"window_days": 60, "min_return": 0.05},
                    "drawdown": {"window_days": 60, "max_drawdown_pct": 0.2},
                    "moving_average": {"short_window_days": 20, "long_window_days": 100, "relation": "above"},
                }
            ),
        ),
    ]
