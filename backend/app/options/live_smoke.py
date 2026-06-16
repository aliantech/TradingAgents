import argparse
import json
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from app.core.config import settings

UrlOpener = Callable[..., Any]


def _fetch_json(url: str, *, opener: UrlOpener, timeout: int) -> dict[str, Any]:
    with opener(url, timeout=timeout) as response:
        payload = response.read().decode()
    decoded = json.loads(payload)
    return decoded if isinstance(decoded, dict) else {}


def _endpoint_status(payload: dict[str, Any]) -> tuple[str, int]:
    results = payload.get("results")
    if isinstance(results, list):
        return ("succeeded", len(results)) if results else ("empty", 0)
    return "succeeded", 0


def _safe_error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPError):
        return f"HTTP Error {exc.code}: {exc.reason}"
    if isinstance(exc, URLError):
        return f"URL Error: {exc.reason}"
    return str(exc)


def _request_url(base_url: str, path: str, query: dict[str, str | int]) -> str:
    return f"{base_url.rstrip('/')}{path}?{urlencode(query)}"


def smoke_options_entitlement(
    *,
    underlyings: list[str],
    api_key: str | None,
    base_url: str,
    opener: UrlOpener = urlopen,
    timeout: int = 20,
) -> dict[str, Any]:
    normalized_underlyings = [symbol.strip().upper() for symbol in underlyings if symbol.strip()]
    missing = []
    if not api_key:
        missing.append("AQUANTLENS_POLYGON_API_KEY")
    if not base_url:
        missing.append("AQUANTLENS_POLYGON_BASE_URL")
    if not normalized_underlyings:
        missing.append("underlyings")
    if missing:
        return {
            "status": "not_ready",
            "readiness_ready": False,
            "missing": missing,
            "checks": [],
            "error_message": None,
        }

    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for underlying in normalized_underlyings:
        check: dict[str, Any] = {
            "underlying": underlying,
            "contracts_status": "not_run",
            "contracts_count": 0,
            "chain_snapshot_status": "not_run",
            "chain_snapshot_count": 0,
            "error_message": None,
        }
        try:
            contracts_url = _request_url(
                base_url,
                "/v3/reference/options/contracts",
                {"underlying_ticker": underlying, "limit": 1, "apiKey": api_key or ""},
            )
            contracts_payload = _fetch_json(contracts_url, opener=opener, timeout=timeout)
            contracts_status, contracts_count = _endpoint_status(contracts_payload)
            check["contracts_status"] = contracts_status
            check["contracts_count"] = contracts_count

            snapshot_url = _request_url(
                base_url,
                f"/v3/snapshot/options/{underlying}",
                {"limit": 1, "apiKey": api_key or ""},
            )
            snapshot_payload = _fetch_json(snapshot_url, opener=opener, timeout=timeout)
            snapshot_status, snapshot_count = _endpoint_status(snapshot_payload)
            check["chain_snapshot_status"] = snapshot_status
            check["chain_snapshot_count"] = snapshot_count
        except Exception as exc:  # noqa: BLE001 - smoke output must report vendor/runtime failures.
            message = _safe_error_message(exc)
            check["error_message"] = message
            errors.append(f"{underlying}: {message}")
        checks.append(check)

    failed = [check for check in checks if check["error_message"]]
    empty = [
        check
        for check in checks
        if check["contracts_status"] == "empty" or check["chain_snapshot_status"] == "empty"
    ]
    if failed:
        status = "failed"
    elif empty:
        status = "partial"
    else:
        status = "succeeded"
    return {
        "status": status,
        "readiness_ready": True,
        "missing": [],
        "checks": checks,
        "error_message": "; ".join(errors) if errors else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a guarded options entitlement smoke check.")
    parser.add_argument("--underlyings", default="SPY,SPX")
    parser.add_argument("--base-url", default=settings.polygon_base_url)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    result = smoke_options_entitlement(
        underlyings=args.underlyings.split(","),
        api_key=settings.polygon_api_key,
        base_url=args.base_url,
        timeout=args.timeout,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
