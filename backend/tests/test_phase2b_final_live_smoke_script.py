from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "phase2b_final_live_smoke.sh"


def test_phase2b_final_live_smoke_script_uses_guarded_gate_only():
    content = SCRIPT.read_text()

    assert "final-live-smoke-gate" in content
    assert "--provider" in content
    assert "--symbol" in content
    assert "--timeframe" in content
    assert "--start" in content
    assert "--end" in content
    assert "provider-readiness" not in content
    assert "live-provider-smoke" not in content
    assert "list-sync-runs" not in content


def test_phase2b_final_live_smoke_script_does_not_read_or_print_secrets():
    content = SCRIPT.read_text()

    assert "source .env" not in content
    assert ". .env" not in content
    assert "cat .env" not in content
    assert "AQUANTLENS_POLYGON_API_KEY" not in content
    assert "printenv" not in content
    assert "env |" not in content
