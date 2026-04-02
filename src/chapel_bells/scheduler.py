"""
Scheduling engine for bell playback.
Uses the 'schedule' library for simple, reliable time-based scheduling.
"""

import json
import logging
import threading
import time as _time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

import schedule
import yaml

logger = logging.getLogger(__name__)


class BellScheduler:
    """
    Loads a JSON/YAML config and schedules bell events using the
    `schedule` library.  Call `run_pending()` from the main loop.
    """

    def __init__(self, config_path: str, play_callback: Callable[[str], bool]):
        self.config_path = Path(config_path)
        self.play_callback = play_callback
        self.config: Dict = {}
        self.history: deque = deque(maxlen=100)
        self._history_lock = threading.Lock()
        self._scheduler = schedule.Scheduler()
        self._quiet_cache: Optional[tuple] = None  # (start_time, end_time)
        self._load_config()

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        with open(self.config_path) as f:
            if self.config_path.suffix == ".json":
                self.config = json.load(f)
            else:
                self.config = yaml.safe_load(f)
        self._cache_quiet_hours()

    def reload_config(self) -> None:
        """Re-read config file and reschedule all events."""
        self._load_config()
        self.schedule_all()

    def _cache_quiet_hours(self) -> None:
        """Pre-parse quiet hours times so is_quiet_now() avoids per-call strptime."""
        qh = self.quiet_hours
        if qh.get("enabled") and "start" in qh and "end" in qh:
            self._quiet_cache = (
                datetime.strptime(qh["start"], "%H:%M").time(),
                datetime.strptime(qh["end"], "%H:%M").time(),
            )
        else:
            self._quiet_cache = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def bells(self) -> List[Dict]:
        return self.config.get("bells", [])

    @property
    def volume(self) -> int:
        return int(self.config.get("volume", 80))

    @property
    def audio_dir(self) -> str:
        raw = self.config.get("audio_dir", "audio_samples")
        p = Path(raw)
        if not p.is_absolute():
            p = self.config_path.parent / p
        return str(p.resolve())

    @property
    def quiet_hours(self) -> Dict:
        return self.config.get("quiet_hours", {"enabled": False})

    # ------------------------------------------------------------------
    # Quiet hours
    # ------------------------------------------------------------------

    def is_quiet_now(self) -> bool:
        qh = self.quiet_hours
        if not qh.get("enabled", False) or self._quiet_cache is None:
            return False
        start, end = self._quiet_cache
        now = datetime.now().time()
        if start > end:          # spans midnight (e.g. 21:00 → 07:00)
            return now >= start or now <= end
        return start <= now <= end

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    # Map weekday numbers (Monday=0) to 3-letter abbreviations
    _WDAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    ALL_DAYS = _WDAY_ABBR  # ["Mon", ... "Sun"]

    def schedule_all(self) -> None:
        """Clear and rebuild the full schedule from config."""
        self._scheduler.clear()
        for bell in self.bells:
            t = bell.get("time", "")
            if not t:
                logger.warning("Bell entry missing 'time', skipping: %s", bell)
                continue
            # Always use every().day so the job fires today if the time
            # hasn't passed yet.  Day-of-week filtering happens in
            # _ring_sequence().
            self._scheduler.every().day.at(t).do(self._trigger, bell=bell)
            days = bell.get("days")
            if days and set(days) < set(self.ALL_DAYS):
                logger.info("Scheduled: %s at %s (%s)", bell.get("sound", "?"), t, ",".join(days))
            else:
                logger.info("Scheduled: %s at %s (every day)", bell.get("sound", "?"), t)

    def run_pending(self) -> None:
        """Run any jobs whose time has come.  Call this every second."""
        self._scheduler.run_pending()

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _trigger(self, bell: Dict) -> None:
        """Fire bell sequence in a background thread so the scheduler loop is not blocked."""
        t = threading.Thread(
            target=self._ring_sequence,
            args=(bell,),
            daemon=True,
            name=f"bell-{bell.get('time', 'manual')}",
        )
        t.start()

    def _ring_sequence(self, bell: Dict) -> None:
        """Play a multi-ring sequence (runs in a daemon thread)."""
        # Day-of-week filter (jobs fire every day; we skip wrong days here)
        days = bell.get("days")
        if days and self._WDAY_ABBR[datetime.now().weekday()] not in days:
            return

        if self.is_quiet_now():
            logger.info("Bell suppressed (quiet hours): %s", bell.get("sound"))
            return

        sound = bell.get("sound", "")
        count = max(1, int(bell.get("count", 1)))
        interval = float(bell.get("interval", 2.0))

        logger.info("Ringing: %s × %d", sound, count)

        try:
            for i in range(count):
                self.play_callback(sound)
                if i < count - 1:
                    _time.sleep(interval)
        except Exception:
            logger.exception("Error during bell sequence for %s", sound)
            return

        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sound": sound,
            "count": count,
        }
        with self._history_lock:
            self.history.appendleft(entry)

    def trigger_sound(self, sound: str) -> bool:
        """Manually trigger a sound by filename (used by web UI).

        Plays in a background thread so the HTTP request returns immediately.
        """
        if not sound:
            return False
        logger.info("Manual trigger: %s", sound)
        bell = {"sound": sound, "count": 1, "interval": 2.0, "time": "manual"}
        self._trigger(bell)
        return True

    # ------------------------------------------------------------------
    # History / status
    # ------------------------------------------------------------------

    def get_history(self, limit: int = 20) -> List[Dict]:
        with self._history_lock:
            return list(self.history)[:limit]

    def get_status(self) -> Dict:
        return {
            "scheduled_bells": len(self.bells),
            "quiet_hours_enabled": self.quiet_hours.get("enabled", False),
            "quiet_hours": {
                "start": self.quiet_hours.get("start", ""),
                "end": self.quiet_hours.get("end", ""),
            },
            "is_quiet_now": self.is_quiet_now(),
            "current_time": datetime.now().strftime("%H:%M:%S"),
        }

    # ------------------------------------------------------------------
    # Schedule mutations
    # ------------------------------------------------------------------

    def _save_config(self) -> None:
        """Persist the current config dict back to the config file, preserving format."""
        with open(self.config_path, "w") as f:
            if self.config_path.suffix in (".yaml", ".yml"):
                yaml.dump(self.config, f, default_flow_style=False,
                          allow_unicode=True, sort_keys=False)
            else:
                json.dump(self.config, f, indent=2)
        logger.info("Config saved: %s", self.config_path)

    def add_bell(self, bell: Dict) -> None:
        """Append a new bell entry and reschedule."""
        self.config.setdefault("bells", []).append(bell)
        self._save_config()
        self.schedule_all()

    def update_bell(self, index: int, bell: Dict) -> None:
        """Replace the bell at *index* and reschedule."""
        bells = self.config.get("bells", [])
        if not 0 <= index < len(bells):
            raise IndexError(f"Bell index {index} out of range")
        bells[index] = bell
        self._save_config()
        self.schedule_all()

    def update_quiet_hours(self, enabled: bool, start: str, end: str) -> None:
        """Update quiet hours settings and persist to config."""
        qh = self.config.setdefault("quiet_hours", {})
        qh["enabled"] = enabled
        qh["start"] = start
        qh["end"] = end
        self._cache_quiet_hours()
        self._save_config()
        logger.info("Quiet hours updated: enabled=%s %s–%s", enabled, start, end)

    def delete_bell(self, index: int) -> None:
        """Remove the bell at *index* and reschedule."""
        bells = self.config.get("bells", [])
        if not 0 <= index < len(bells):
            raise IndexError(f"Bell index {index} out of range")
        bells.pop(index)
        self._save_config()
        self.schedule_all()
