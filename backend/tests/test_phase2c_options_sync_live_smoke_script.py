from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "phase2c_options_sync_live_smoke.sh"


def test_phase2c_options_sync_live_smoke_script_uses_options_cli():
    content = SCRIPT.read_text()

    assert "python3" in content
    assert "python -m app.options.cli" in content or "app.options.cli" in content
    assert "sync-chain" in content
    assert "--underlying" in content
    assert "--expiry" in content
    assert "--limit" in content


def test_phase2c_options_sync_live_smoke_script_does_not_read_or_print_secrets():
    content = SCRIPT.read_text()

    assert "source .env" not in content
    assert ". .env" not in content
    assert "cat .env" not in content
    assert "AQUANTLENS_POLYGON_API_KEY" not in content
    assert "printenv" not in content
    assert "env |" not in content
