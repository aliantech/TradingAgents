from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "phase2c_options_live_smoke.sh"


def test_phase2c_options_live_smoke_script_checks_spy_and_spx_by_default():
    content = SCRIPT.read_text()

    assert "app.options.live_smoke" in content
    assert "python3" in content
    assert "SPY,SPX" in content
    assert "--timeout" in content
    assert "--retries" in content
    assert "reference/options/contracts" not in content
    assert "snapshot/options" not in content


def test_phase2c_options_live_smoke_script_does_not_read_or_print_secrets():
    content = SCRIPT.read_text()

    assert "source .env" not in content
    assert ". .env" not in content
    assert "cat .env" not in content
    assert "AQUANTLENS_POLYGON_API_KEY" not in content
    assert "printenv" not in content
    assert "env |" not in content
