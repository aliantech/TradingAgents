import argparse
import json
import os
from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from app.analysis.schemas import AnalysisDepth, AnalysisRequest, AssetType, ReportLanguage, ResearchTemplate
from app.analysis.tradingagents_adapter import build_tradingagents_request, map_tradingagents_error
from app.analysis.tradingagents_runner import REAL_TRADINGAGENTS_MODE, ensure_tradingagents_import_path, run_configured_research
from app.core.config import Settings
from app.db.session import SessionLocal, initialize_database
from app.settings.runtime import resolve_runtime_settings


@dataclass(frozen=True)
class RealRunnerSmokeResult:
    symbol: str
    status: str
    runner_mode: str
    llm_provider: str
    model: str
    missing: list[str]
    progress: list[dict[str, str]]
    report_generated: bool
    evidence_labels: list[str]
    error_message: str | None = None


def run_real_runner_smoke(
    *,
    runtime_settings: Settings,
    request: AnalysisRequest,
    explicit_confirmation: bool,
    environ: dict[str, str] | None = None,
) -> RealRunnerSmokeResult:
    environ = environ if environ is not None else os.environ
    normalized_request = request.model_copy(update={"symbol": request.symbol.upper()})
    missing = real_runner_smoke_missing_prerequisites(
        runtime_settings=runtime_settings,
        explicit_confirmation=explicit_confirmation,
        environ=environ,
    )
    provider = runtime_settings.tradingagents_llm_provider or normalized_request.llm_provider
    model = runtime_settings.tradingagents_deep_think_llm or normalized_request.model
    if missing:
        return RealRunnerSmokeResult(
            symbol=normalized_request.symbol,
            status="not_ready",
            runner_mode=runtime_settings.tradingagents_runner_mode,
            llm_provider=provider,
            model=model,
            missing=missing,
            progress=[],
            report_generated=False,
            evidence_labels=[],
            error_message="Manual real-runner smoke prerequisites are incomplete.",
        )

    execution_request = build_tradingagents_request(uuid4(), normalized_request)
    try:
        result = run_configured_research(execution_request, runtime_settings)
    except Exception as error:
        event = map_tradingagents_error(error)
        return RealRunnerSmokeResult(
            symbol=normalized_request.symbol,
            status="failed",
            runner_mode=runtime_settings.tradingagents_runner_mode,
            llm_provider=provider,
            model=model,
            missing=[],
            progress=[event.model_dump()],
            report_generated=False,
            evidence_labels=[],
            error_message=event.message,
        )

    return RealRunnerSmokeResult(
        symbol=normalized_request.symbol,
        status="succeeded",
        runner_mode=runtime_settings.tradingagents_runner_mode,
        llm_provider=provider,
        model=model,
        missing=[],
        progress=[event.model_dump() for event in result.progress],
        report_generated=True,
        evidence_labels=result.report.evidence_labels,
    )


def real_runner_smoke_missing_prerequisites(
    *,
    runtime_settings: Settings,
    explicit_confirmation: bool,
    environ: dict[str, str],
) -> list[str]:
    missing: list[str] = []
    if not explicit_confirmation:
        missing.append("--i-understand-this-calls-a-real-llm-provider")
    if runtime_settings.tradingagents_runner_mode != REAL_TRADINGAGENTS_MODE:
        missing.append("AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=real-tradingagents")

    provider = runtime_settings.tradingagents_llm_provider
    env_var = api_key_env_for_provider(provider)
    if env_var == "__unknown_provider__":
        missing.append(f"known LLM provider mapping for {provider}")
    elif env_var and not environ.get(env_var):
        missing.append(env_var)
    return missing


def api_key_env_for_provider(provider: str) -> str | None:
    ensure_tradingagents_import_path()
    from tradingagents.llm_clients.api_key_env import PROVIDER_API_KEY_ENV, get_api_key_env

    normalized_provider = provider.lower()
    if normalized_provider not in PROVIDER_API_KEY_ENV:
        return "__unknown_provider__"
    return get_api_key_env(normalized_provider)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aquantlens-analysis")
    subparsers = parser.add_subparsers(dest="command", required=True)
    smoke_parser = subparsers.add_parser("real-runner-smoke")
    smoke_parser.add_argument("--symbol", default="SPY")
    smoke_parser.add_argument("--asset-type", default=AssetType.etf.value, choices=[item.value for item in AssetType])
    smoke_parser.add_argument("--analysis-date", default=date.today(), type=date.fromisoformat)
    smoke_parser.add_argument("--language", default=ReportLanguage.zh.value, choices=[item.value for item in ReportLanguage])
    smoke_parser.add_argument("--depth", default=AnalysisDepth.standard.value, choices=[item.value for item in AnalysisDepth])
    smoke_parser.add_argument("--analyst-set", default="macro-options")
    smoke_parser.add_argument(
        "--research-template",
        default=ResearchTemplate.general.value,
        choices=[item.value for item in ResearchTemplate],
    )
    smoke_parser.add_argument("--llm-provider", default=None)
    smoke_parser.add_argument("--model", default=None)
    smoke_parser.add_argument("--i-understand-this-calls-a-real-llm-provider", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "real-runner-smoke":
        initialize_database()
        session = SessionLocal()
        try:
            runtime_settings = resolve_runtime_settings(session)
        finally:
            session.close()
        request = AnalysisRequest(
            symbol=args.symbol,
            asset_type=AssetType(args.asset_type),
            analysis_date=args.analysis_date,
            language=ReportLanguage(args.language),
            llm_provider=args.llm_provider or runtime_settings.tradingagents_llm_provider,
            model=args.model or runtime_settings.tradingagents_deep_think_llm,
            depth=AnalysisDepth(args.depth),
            analyst_set=args.analyst_set,
            research_template=ResearchTemplate(args.research_template),
        )
        result = run_real_runner_smoke(
            runtime_settings=runtime_settings,
            request=request,
            explicit_confirmation=args.i_understand_this_calls_a_real_llm_provider,
        )
        print(json.dumps(result.__dict__, ensure_ascii=False))
        return 0 if result.status == "succeeded" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
