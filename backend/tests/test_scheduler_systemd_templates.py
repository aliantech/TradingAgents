from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_scheduler_systemd_service_runs_loop_command():
    service = (ROOT / "infra" / "systemd" / "aquantlens-market-data-scheduler.service").read_text()

    assert "WorkingDirectory=/home/yasin/workspace/TradingAgents/backend" in service
    assert "EnvironmentFile=-/home/yasin/workspace/TradingAgents/backend/.env" in service
    assert "ExecStart=" in service
    assert "python -m app.market_data.cli run-scheduler-loop" in service
    assert "--targets ${AQUANTLENS_SCHEDULER_TARGETS}" in service
    assert "--interval-seconds ${AQUANTLENS_SCHEDULER_INTERVAL_SECONDS}" in service
    assert "Restart=on-failure" in service


def test_scheduler_systemd_timer_runs_daily_service():
    timer = (ROOT / "infra" / "systemd" / "aquantlens-market-data-scheduler.timer").read_text()

    assert "OnCalendar=Mon..Fri 22:10:00" in timer
    assert "Unit=aquantlens-market-data-scheduler.service" in timer
    assert "Persistent=true" in timer
