import json
from urllib.parse import parse_qs, urlparse

from app.options.live_smoke import smoke_options_entitlement


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_options_entitlement_smoke_checks_contracts_and_chain_for_each_underlying():
    requested: list[str] = []

    def opener(url: str, timeout: int = 20):
        requested.append(url)
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        assert query["apiKey"] == ["test-key"]
        if parsed.path == "/v3/reference/options/contracts":
            underlying = query["underlying_ticker"][0]
            return FakeResponse({"results": [{"ticker": f"O:{underlying}240621C00100000"}]})
        if parsed.path.startswith("/v3/snapshot/options/"):
            underlying = parsed.path.rsplit("/", 1)[-1]
            return FakeResponse({"results": [{"details": {"underlying_ticker": underlying}}]})
        raise AssertionError(f"Unexpected URL: {url}")

    result = smoke_options_entitlement(
        underlyings=["SPY", "SPX"],
        api_key="test-key",
        base_url="https://api.massive.test",
        opener=opener,
    )

    assert result["status"] == "succeeded"
    assert result["readiness_ready"] is True
    assert result["missing"] == []
    assert [check["underlying"] for check in result["checks"]] == ["SPY", "SPX"]
    assert all(check["contracts_status"] == "succeeded" for check in result["checks"])
    assert all(check["chain_snapshot_status"] == "succeeded" for check in result["checks"])
    assert len(requested) == 4


def test_options_entitlement_smoke_is_guarded_when_api_key_missing():
    result = smoke_options_entitlement(
        underlyings=["SPX"],
        api_key="",
        base_url="https://api.massive.test",
        opener=lambda url, timeout=20: (_ for _ in ()).throw(AssertionError("should not call network")),
    )

    assert result["status"] == "not_ready"
    assert result["readiness_ready"] is False
    assert result["missing"] == ["AQUANTLENS_POLYGON_API_KEY"]
    assert result["checks"] == []
