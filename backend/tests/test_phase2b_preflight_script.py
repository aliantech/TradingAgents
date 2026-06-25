from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "phase2b_preflight.sh"


def test_phase2b_preflight_script_runs_non_live_checks_by_default():
    content = SCRIPT.read_text()

    assert "pytest -q" in content
    assert "npm run build" in content
    assert "RUN_LIVE_SMOKE" not in content
    assert "phase2b_final_live_smoke" not in content


def test_phase2b_preflight_script_does_not_read_or_print_secrets():
    content = SCRIPT.read_text()

    assert "source .env" not in content
    assert ". .env" not in content
    assert "cat .env" not in content
    assert "API_KEY" not in content
    assert "printenv" not in content
    assert "env |" not in content
