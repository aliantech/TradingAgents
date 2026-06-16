POLYGON_SYMBOL_MAP = {
    "SPX": "I:SPX",
}


def map_provider_symbol(symbol: str, provider_name: str) -> str:
    normalized_symbol = symbol.upper().strip()
    normalized_provider = provider_name.lower().strip()
    if normalized_provider == "polygon":
        return POLYGON_SYMBOL_MAP.get(normalized_symbol, normalized_symbol)
    return normalized_symbol
