from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "phase8_real_runner_smoke.sh"


def test_phase8_real_runner_smoke_script_uses_guarded_analysis_cli_only():
    content = SCRIPT.read_text()

    assert "real-runner-smoke" in content
    assert "--i-understand-this-calls-a-real-llm-provider" in content
    assert "--require-option-chain-context" in content
    assert "python -m app.analysis.cli" in content
    assert "app.market_data.cli" not in content


def test_phase8_real_runner_smoke_script_does_not_read_or_print_secrets():
    content = SCRIPT.read_text()

    assert "source .env" not in content
    assert ". .env" not in content
    assert "cat .env" not in content
    assert "OPENAI_API_KEY" not in content
    assert "ANTHROPIC_API_KEY" not in content
    assert "GOOGLE_API_KEY" not in content
    assert "printenv" not in content
    assert "env |" not in content
