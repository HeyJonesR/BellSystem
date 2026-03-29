"""
Tests for ChapelBells core components.
Run with: pytest tests/
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, time
import json

# Import components
from chapel_bells.scheduler import BellScheduler, BellEvent, QuietHours, ScheduleRule
from chapel_bells.astro import AstronomicalCalculator
from chapel_bells.audio import AudioEngine, AudioConfig, AudioProfile


class TestScheduler:
    """Test scheduling engine."""
    
    def test_quiet_hours_enabled(self):
        """Test quiet hours detection."""
        qh = QuietHours(enabled=True, start="21:00", end="07:00")
        
        # During quiet hours
        quiet_time = datetime(2024, 1, 1, 22, 0, 0)
        assert qh.is_quiet_now(quiet_time) == True
        
        # Outside quiet hours
        daytime = datetime(2024, 1, 1, 12, 0, 0)
        assert qh.is_quiet_now(daytime) == False
    
    def test_quiet_hours_override(self):
        """Test override dates."""
        qh = QuietHours(
            enabled=True,
            start="21:00",
            end="07:00",
            override_dates=["2024-01-01"]
        )
        
        # Normally quiet time, but overridden
        quiet_time = datetime(2024, 1, 1, 22, 0, 0)
        assert qh.is_quiet_now(quiet_time) == False
    
    def test_schedule_rule_hourly(self):
        """Test hourly schedule rule."""
        scheduler = BellScheduler(db_path=":memory:")
        rule = scheduler._parse_rule("every hour")
        
        assert rule is not None
        assert rule.minute == 0
    
    def test_schedule_rule_weekday(self):
        """Test weekday-specific rule."""
        scheduler = BellScheduler(db_path=":memory:")
        rule = scheduler._parse_rule("sunday at 10:00")
        
        assert rule is not None
        assert rule.hour == 10
        assert rule.minute == 0
        assert rule.day_of_week == [6]  # Sunday
    
    def test_schedule_rule_cron(self):
        """Test cron format rule."""
        scheduler = BellScheduler(db_path=":memory:")
        rule = scheduler._parse_rule("0 12 * * *")  # Noon every day
        
        assert rule is not None
        assert rule.hour == 12
        assert rule.minute == 0
    
    def test_rule_matching(self):
        """Test rule matching against datetime."""
        rule = ScheduleRule(name="test", hour=10, minute=0, day_of_week=[0])  # Monday 10 AM
        
        # Monday 10:00 AM
        monday = datetime(2024, 1, 1, 10, 0, 0)  # Jan 1, 2024 is a Monday
        assert rule.matches(monday) == True
        
        # Monday 10:01 AM
        monday_late = datetime(2024, 1, 1, 10, 1, 0)
        assert rule.matches(monday_late) == False
        
        # Tuesday 10:00 AM
        tuesday = datetime(2024, 1, 2, 10, 0, 0)
        assert rule.matches(tuesday) == False
    
    def test_event_add_and_retrieve(self):
        """Test adding and retrieving events."""
        scheduler = BellScheduler(db_path=":memory:")
        
        event = BellEvent(
            name="Test Event",
            rule="every hour",
            profile="westminster"
        )
        scheduler.add_event(event)
        
        events = scheduler.get_events()
        assert len(events) == 1
        assert events[0].name == "Test Event"
    
    def test_event_deletion(self):
        """Test event deletion."""
        scheduler = BellScheduler(db_path=":memory:")
        
        event = BellEvent(name="To Delete", rule="every hour")
        scheduler.add_event(event)
        assert len(scheduler.get_events()) == 1
        
        scheduler.delete_event("To Delete")
        assert len(scheduler.get_events()) == 0
    
    def test_evaluate_events_empty(self):
        """Test evaluating events when none match."""
        scheduler = BellScheduler(db_path=":memory:")
        
        event = BellEvent(
            name="Morning Only",
            rule="* 08 * * *",  # 8 AM only
            profile="westminster"
        )
        scheduler.add_event(event)
        
        # Check at noon
        events = scheduler.evaluate_events(datetime(2024, 1, 1, 12, 0, 0))
        assert len(events) == 0
    
    def test_evaluate_events_with_quiet_hours(self):
        """Test that quiet hours prevent event evaluation."""
        scheduler = BellScheduler(db_path=":memory:")
        scheduler.set_quiet_hours(QuietHours(
            enabled=True,
            start="21:00",
            end="07:00"
        ))
        
        event = BellEvent(name="Quiet Hours Test", rule="every hour")
        scheduler.add_event(event)
        
        # Check during quiet hours (22:00)
        events = scheduler.evaluate_events(datetime(2024, 1, 1, 22, 0, 0))
        assert len(events) == 0
        
        # Check during allowed hours (12:00)
        events = scheduler.evaluate_events(datetime(2024, 1, 1, 12, 0, 0))
        assert len(events) == 1
    
    def test_playback_log(self):
        """Test logging of bell playback."""
        scheduler = BellScheduler(db_path=":memory:")
        
        event = BellEvent(name="Test", rule="every hour", profile="west")
        scheduler.trigger_event(event)
        
        history = scheduler.get_playback_history()
        assert len(history) > 0
        assert history[0]["event"] == "Test"


class TestAstronomicalCalculator:
    """Test astronomical calculations."""
    
    def test_calculator_initialization(self):
        """Test creating calculator."""
        calc = AstronomicalCalculator(40.7128, -74.0060)  # NYC
        assert calc.latitude == 40.7128
        assert calc.longitude == -74.0060
    
    def test_sunrise_sunset(self):
        """Test sunrise/sunset calculation."""
        calc = AstronomicalCalculator(40.7128, -74.0060)
        
        test_date = datetime(2024, 6, 21)  # Summer solstice
        sunrise, sunset = calc.get_sunrise_sunset(test_date)
        
        assert sunrise is not None
        assert sunset is not None
        assert sunrise < sunset
        
        # Summer sunrise should be early (around 5 AM-ish)
        assert sunrise.hour < 8
    
    def test_is_daytime(self):
        """Test daytime detection."""
        calc = AstronomicalCalculator(40.7128, -74.0060)
        
        # Noon should always be daytime
        noon = datetime(2024, 1, 1, 12, 0, 0)
        assert calc.is_daytime(noon) == True
        
        # Sunrise is around 7 AM in NYC in January
        morning = datetime(2024, 1, 1, 8, 0, 0)
        assert calc.is_daytime(morning) == True


class TestAudioEngine:
    """Test audio playback engine."""
    
    def test_audio_engine_init(self):
        """Test audio engine initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AudioEngine(tmpdir)
            assert engine.audio_dir == Path(tmpdir)
            assert engine.config.volume == 80
    
    def test_available_profiles(self):
        """Test getting available profiles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test profile
            profile_dir = Path(tmpdir) / "test_profile"
            profile_dir.mkdir()
            (profile_dir / "bell.wav").touch()
            
            engine = AudioEngine(tmpdir)
            profiles = engine.get_available_profiles()
            
            assert "test_profile" in profiles
    
    def test_volume_control(self):
        """Test volume setting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = AudioEngine(tmpdir)
            
            engine.set_volume(50)
            assert engine.config.volume == 50
            
            # Clamp to bounds
            engine.set_volume(150)
            assert engine.config.volume == 100
            
            engine.set_volume(-10)
            assert engine.config.volume == 0


class TestIntegration:
    """Integration tests."""
    
    def test_end_to_end_schedule(self):
        """Test complete scheduling flow."""
        scheduler = BellScheduler(db_path=":memory:")
        
        # Add event
        event = BellEvent(
            name="Test Event",
            rule="* 10 * * 1",  # Monday 10 AM
            profile="westminster"
        )
        scheduler.add_event(event)
        
        # Test with callback
        called = {"count": 0}
        
        def callback(e):
            called["count"] += 1
        
        scheduler.register_callback(callback)
        
        # Check and trigger at correct time
        test_time = datetime(2024, 1, 1, 10, 0, 0)  # Monday 10 AM
        events = scheduler.evaluate_events(test_time)
        
        assert len(events) == 1
        scheduler.trigger_event(events[0])
        assert called["count"] == 1
    
    def test_config_persistence(self):
        """Test saving/loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            
            # Create and save config
            scheduler1 = BellScheduler(db_path=str(Path(tmpdir) / "test.db"))
            event = BellEvent(name="Test", rule="every hour")
            scheduler1.add_event(event)
            
            config_json = scheduler1.to_json()
            config_file.write_text(config_json)
            
            # Load in new scheduler
            scheduler2 = BellScheduler(db_path=str(Path(tmpdir) / "test2.db"))
            # Parse config and verify structure
            config = json.loads(config_json)
            assert len(config["events"]) == 1
            assert config["events"][0]["name"] == "Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
