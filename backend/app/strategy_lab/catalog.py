from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StrategyCatalogEntry:
    strategy_id: str
    name: str
    description: str
    scope: str
    default_parameters: dict[str, Any]
    parameter_schema: dict[str, dict[str, Any]]


STRATEGY_CATALOG: dict[str, StrategyCatalogEntry] = {
    "ma-cross-research": StrategyCatalogEntry(
        strategy_id="ma-cross-research",
        name="MA Cross Research",
        description="Research-only moving average signal contract.",
        scope="research_only",
        default_parameters={
            "fast_window": 2,
            "slow_window": 3,
        },
        parameter_schema={
            "fast_window": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "label": "Fast Window",
            },
            "slow_window": {
                "type": "integer",
                "minimum": 1,
                "maximum": 200,
                "label": "Slow Window",
            },
        },
    )
}


def list_strategy_catalog() -> list[StrategyCatalogEntry]:
    return list(STRATEGY_CATALOG.values())


def get_strategy_catalog_entry(strategy_id: str) -> StrategyCatalogEntry | None:
    return STRATEGY_CATALOG.get(strategy_id)
