"""
Scheduling engine for bell playback.
Handles DST, quiet hours, and calendar-based schedules.
"""

import logging
import json
import sqlite3
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import re
import threading

logger = logging.getLogger(__name__)


class DayOfWeek(Enum):
    """Days of the week."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class BellEvent:
    """Represents a scheduled bell event."""
    name: str
    rule: str  # e.g., "every hour", "sunday 10:00", "first sunday 10:00"
    profile: str = "westminster"
    tone: str = "bell"
    active_after: Optional[str] = None  # Time like "07:00" (respects quiet hours)
    active_before: Optional[str] = None  # Time like "21:00"
    description: str = ""
    repeat_interval: int = 1  # For recurring events
    
    def to_dict(self):
        return asdict(self)


@dataclass
class QuietHours:
    """Configuration for quiet hours."""
    enabled: bool = True
    start: str = "21:00"  # 9 PM
    end: str = "07:00"    # 7 AM
    override_dates: List[str] = field(default_factory=list)  # Dates to override quiet hours (YYYY-MM-DD)
    
    def is_quiet_now(self, dt: datetime = None) -> bool:
        """Check if current time is within quiet hours."""
        if not self.enabled:
            return False
        
        if dt is None:
            dt = datetime.now()
        
        start_parts = self.start.split(":")
        end_parts = self.end.split(":")
        
        start_time = time(int(start_parts[0]), int(start_parts[1]))
        end_time = time(int(end_parts[0]), int(end_parts[1]))
        
        # Check overrides (no quiet hours on these dates)
        date_str = dt.strftime("%Y-%m-%d")
        if date_str in self.override_dates:
            return False
        
        current_time = dt.time()
        
        # Handle case where quiet hours span midnight
        if start_time < end_time:
            # e.g., 07:00 - 21:00 doesn't make sense for quiet hours
            # So assume it's actually a daytime range
            return start_time <= current_time <= end_time
        else:
            # Quiet hours span midnight (e.g., 21:00 - 07:00)
            return current_time >= start_time or current_time <= end_time
    
    def to_dict(self):
        return asdict(self)


@dataclass  
class ScheduleRule:
    """Represents a scheduling rule."""
    name: str
    cron_expr: Optional[str] = None  # Standard cron format
    hour: Optional[int] = None  # 0-23
    minute: Optional[int] = 0  # 0-59
    day_of_week: Optional[List[int]] = None  # 0=Monday ... 6=Sunday
    day_of_month: Optional[int] = None
    month: Optional[int] = None
    events: List[BellEvent] = field(default_factory=list)
    
    def matches(self, dt: datetime) -> bool:
        """Check if rule matches given datetime."""
        # Hour check
        if self.hour is not None and dt.hour != self.hour:
            return False
        
        # Minute check
        if self.minute is not None and dt.minute != self.minute:
            return False
        
        # Day of week check
        if self.day_of_week is not None:
            if dt.weekday() not in self.day_of_week:
                return False
        
        # Day of month check
        if self.day_of_month is not None and dt.day != self.day_of_month:
            return False
        
        # Month check
        if self.month is not None and dt.month != self.month:
            return False
        
        return True


class BellScheduler:
    """
    Main scheduling engine.
    
    Evaluates bell events at regular intervals and triggers playback.
    Handles DST automatically via system time (NTP-synced).
    """
    
    def __init__(self, db_path: str = ":memory:", config_file: str = None):
        """
        Initialize scheduler.
        
        Args:
            db_path: Path to SQLite database (":memory:" for in-memory)
            config_file: Optional JSON/YAML config file to load
        """
        self.db_path = db_path
        self.quiet_hours = QuietHours()
        self.rules: List[ScheduleRule] = []
        self.callbacks: List[Callable] = []
        self.lock = threading.Lock()
        self.running = False
        
        self._init_db()
        
        if config_file:
            self.load_config(config_file)
    
    def _init_db(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    rule TEXT NOT NULL,
                    profile TEXT DEFAULT 'westminster',
                    tone TEXT DEFAULT 'bell',
                    active_after TEXT,
                    active_before TEXT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS playback_log (
                    id INTEGER PRIMARY KEY,
                    event_name TEXT NOT NULL,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    profile TEXT,
                    tone TEXT
                );
                
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
    
    def add_event(self, event: BellEvent):
        """Add an event to the schedule (skips if name already exists)."""
        with self.lock:
            # Validate rule format
            if not self._validate_rule(event.rule):
                raise ValueError(f"Invalid rule format: {event.rule}")
            
            # Store in database (skip duplicates by name)
            with sqlite3.connect(self.db_path) as conn:
                existing = conn.execute(
                    "SELECT 1 FROM events WHERE name = ?", (event.name,)
                ).fetchone()
                if existing:
                    logger.debug(f"Event already exists, skipping: {event.name}")
                    return
                conn.execute("""
                    INSERT INTO events (name, rule, profile, tone, active_after, active_before, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (event.name, event.rule, event.profile, event.tone, 
                      event.active_after, event.active_before, event.description))
                conn.commit()
            
            logger.info(f"Added event: {event.name}")
    
    def get_events(self) -> List[BellEvent]:
        """Get all scheduled events."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name, rule, profile, tone, active_after, active_before, description FROM events")
            events = []
            for row in cursor:
                event = BellEvent(
                    name=row[0],
                    rule=row[1],
                    profile=row[2],
                    tone=row[3],
                    active_after=row[4],
                    active_before=row[5],
                    description=row[6]
                )
                events.append(event)
            return events
    
    def delete_event(self, event_name: str):
        """Delete an event by name."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM events WHERE name = ?", (event_name,))
                conn.commit()
            logger.info(f"Deleted event: {event_name}")
    
    def set_quiet_hours(self, quiet_hours: QuietHours):
        """Update quiet hours configuration."""
        with self.lock:
            self.quiet_hours = quiet_hours
            
            # Persist to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM settings WHERE key = 'quiet_hours'")
                conn.execute(
                    "INSERT INTO settings (key, value) VALUES ('quiet_hours', ?)",
                    (json.dumps(quiet_hours.to_dict()),)
                )
                conn.commit()
    
    def register_callback(self, callback: Callable):
        """
        Register callback for when bell should ring.
        
        Callback signature: callback(event: BellEvent) -> None
        """
        self.callbacks.append(callback)
    
    def _validate_rule(self, rule: str) -> bool:
        """Validate scheduling rule format."""
        # Simple validation - actual rules use natural language or patterns
        # Examples: "every hour", "sunday at 10:00", "every * * * *" (cron)
        return len(rule) > 0
    
    def _parse_rule(self, rule: str) -> Optional[ScheduleRule]:
        """
        Parse natural language rule into ScheduleRule.
        
        Examples:
        - "every hour" -> hour matches, minute=0
        - "sunday 10:00" -> sunday, 10:00
        - "0 10 * * 0" -> cron format (10 AM on Sundays)
        """
        rule = rule.strip().lower()
        
        # "every hour" pattern
        if "every hour" in rule:
            return ScheduleRule(
                name="hourly",
                minute=0
            )
        
        # "sunday at HH:MM" pattern
        match = re.match(r"(\w+)\s+at\s+(\d{1,2}):(\d{2})", rule)
        if match:
            day_name = match.group(1)
            hour = int(match.group(2))
            minute = int(match.group(3))
            
            day_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2,
                "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
            }
            
            if day_name in day_map:
                return ScheduleRule(
                    name=rule,
                    hour=hour,
                    minute=minute,
                    day_of_week=[day_map[day_name]]
                )
        
        # Cron format: "minute hour day month weekday"
        parts = rule.split()
        if len(parts) == 5:
            try:
                minute = int(parts[0]) if parts[0] != "*" else 0
                hour = int(parts[1]) if parts[1] != "*" else None
                day_of_month = int(parts[2]) if parts[2] != "*" else None
                month = int(parts[3]) if parts[3] != "*" else None
                # day_of_week in cron: 0=Sunday, we use 0=Monday
                dow_str = parts[4]
                day_of_week = None
                if dow_str != "*":
                    try:
                        dow_val = int(dow_str)
                        day_of_week = [(dow_val + 6) % 7]  # Convert cron format
                    except ValueError:
                        pass
                
                return ScheduleRule(
                    name=rule,
                    minute=minute,
                    hour=hour,
                    day_of_month=day_of_month,
                    month=month,
                    day_of_week=day_of_week
                )
            except (ValueError, IndexError):
                pass
        
        return None
    
    def evaluate_events(self, dt: datetime = None) -> List[BellEvent]:
        """
        Evaluate which events should trigger at given time.
        
        Args:
            dt: datetime to evaluate (uses current time if None)
        
        Returns:
            List of events that match current time
        """
        if dt is None:
            dt = datetime.now()
        
        # Check quiet hours first
        if self.quiet_hours.is_quiet_now(dt):
            return []
        
        matching_events = []
        
        with self.lock:
            for event in self.get_events():
                # Parse rule
                rule = self._parse_rule(event.rule)
                if not rule:
                    continue
                
                # Check if rule matches
                if not rule.matches(dt):
                    continue
                
                # Check active_after and active_before
                if event.active_after:
                    after_time = datetime.strptime(event.active_after, "%H:%M").time()
                    if dt.time() < after_time:
                        continue
                
                if event.active_before:
                    before_time = datetime.strptime(event.active_before, "%H:%M").time()
                    if dt.time() > before_time:
                        continue
                
                matching_events.append(event)
        
        return matching_events
    
    def trigger_event(self, event: BellEvent):
        """Trigger an event (call registered callbacks)."""
        logger.info(f"Triggering event: {event.name}")
        
        # Log to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO playback_log (event_name, profile, tone) VALUES (?, ?, ?)",
                (event.name, event.profile, event.tone)
            )
            conn.commit()
        
        # Call registered callbacks
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def get_playback_history(self, limit: int = 100) -> List[Dict]:
        """Get recent bell playback history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT event_name, triggered_at, profile, tone FROM playback_log ORDER BY triggered_at DESC LIMIT ?",
                (limit,)
            )
            return [{"event": row[0], "time": row[1], "profile": row[2], "tone": row[3]} for row in cursor]
    
    def load_config(self, config_file: str):
        """Load configuration from JSON/YAML file."""
        config_path = Path(config_file)
        
        if config_path.suffix in [".json"]:
            with open(config_path) as f:
                config = json.load(f)
        elif config_path.suffix in [".yaml", ".yml"]:
            try:
                import yaml
                with open(config_path) as f:
                    config = yaml.safe_load(f)
            except ImportError:
                logger.warning("PyYAML not available, skipping YAML config")
                return
        else:
            raise ValueError(f"Unsupported config format: {config_path.suffix}")
        
        # Load quiet hours
        if "quiet_hours" in config:
            qh = config["quiet_hours"]
            self.set_quiet_hours(QuietHours(
                enabled=qh.get("enabled", True),
                start=qh.get("start", "21:00"),
                end=qh.get("end", "07:00"),
                override_dates=qh.get("override_dates", [])
            ))
        
        # Load events
        if "events" in config:
            for event_config in config["events"]:
                event = BellEvent(
                    name=event_config["name"],
                    rule=event_config["rule"],
                    profile=event_config.get("profile", "westminster"),
                    tone=event_config.get("tone", "bell"),
                    active_after=event_config.get("active_after"),
                    active_before=event_config.get("active_before"),
                    description=event_config.get("description", "")
                )
                self.add_event(event)
    
    def to_json(self) -> str:
        """Export configuration to JSON."""
        config = {
            "quiet_hours": self.quiet_hours.to_dict(),
            "events": [e.to_dict() for e in self.get_events()]
        }
        return json.dumps(config, indent=2)
    
    def find_event_by_name(self, name: str) -> Optional[BellEvent]:
        """
        Find a scheduled event by name (case-insensitive).
        
        Args:
            name: Event name to search for
        
        Returns:
            BellEvent if found, None otherwise
        """
        events = self.get_events()
        # Case-insensitive search
        name_lower = name.lower()
        for event in events:
            if event.name.lower() == name_lower:
                return event
        return None
