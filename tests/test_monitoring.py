from app.core.monitoring import setup_monitoring


def test_setup_monitoring_disabled_without_dsn():
    assert setup_monitoring() is False
