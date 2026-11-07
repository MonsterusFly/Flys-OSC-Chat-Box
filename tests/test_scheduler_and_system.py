from core.auto_sender import AutoSendScheduler
from integrations.system import SystemMonitor, SystemSnapshot


def test_auto_scheduler_repeats_and_skips_missed_ticks():
    s = AutoSendScheduler(10)
    s.configure(True, 10, now=100)
    assert s.seconds_remaining(now=105) == 5
    assert not s.advance(now=109.9)
    assert s.advance(now=110)
    assert not s.advance(now=110)
    assert s.advance(now=145)
    assert s.seconds_remaining(now=145) == 5


def test_auto_scheduler_interval_change_and_stop():
    s = AutoSendScheduler(10)
    s.configure(True, 10, now=100)
    s.configure(True, 30, now=105)
    assert s.seconds_remaining(now=110) == 25
    s.configure(False, 30, now=111)
    assert s.seconds_remaining(now=150) is None
    assert not s.advance(now=150)
    s.configure(True, 30, now=200)
    assert s.seconds_remaining(now=200) == 30


def test_system_sampler_reports_real_values():
    monitor = SystemMonitor()
    result = monitor.sample()
    assert 0 <= result.cpu <= 100
    assert 0 <= result.ram <= 100
    assert result.total_gib > 0
    assert 0 <= result.used_gib <= result.total_gib
    assert result.uptime_seconds >= 0
    assert "CPU " in result.display and "RAM " in result.display


def test_snapshot_backward_compatibility():
    s = SystemSnapshot(20, 35)
    assert s.display == "CPU 20% · RAM 35%"
