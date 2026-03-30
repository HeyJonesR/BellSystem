"""
Scheduling engine for bell playback.
Uses the 'schedule' library for simple, reliable time-based scheduling.
"""

import json
import logging
import time as _time
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
        self.history: List[Dict] = []   # recent playback log (in-memory)
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

    def reload_config(self) -> None:
        """Re-read config file and reschedule all events."""
        self._load_config()
        self.schedule_all()

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
        return self.config.get("audio_dir", "audio_samples")

    @property
    def quiet_hours(self) -> Dict:
        return self.config.get("quiet_hours", {"enabled": False})

    # ------------------------------------------------------------------
    # Quiet hours
    # ------------------------------------------------------------------

    def is_quiet_now(self) -> bool:
        qh = self.quiet_hours
        if not qh.get("enabled", False):
            return False
        now = datetime.now().time()
        start = datetime.strptime(qh["start"], "%H:%M").time()
        end = datetime.strptime(qh["end"], "%H:%M").time()
        if start > end:          # spans midnight (e.g. 21:00 → 07:00)
            return now >= start or now <= end
        return start <= now <= end

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    def schedule_all(self) -> None:
        """Clear and rebuild the full schedule from config."""
        schedule.clear()
        for bell in self.bells:
            t = bell.get("time", "")
            if not t:
                logger.warning("Bell entry missing 'time', skipping: %s", bell)
                continue
            # schedule.every().day.at() needs HH:MM format
            schedule.every().day.at(t).do(self._trigger, bell=bell)
            logger.info("Scheduled: %s at %s", bell.get("sound", "?"), t)

    def run_pending(self) -> None:
        """Run any jobs whose time has come.  Call this every second."""
        schedule.run_pending()

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _trigger(self, bell: Dict) -> None:
        if self.is_quiet_now():
            logger.info("Bell suppressed (quiet hours): %s", bell.get("sound"))
            return

        sound = bell.get("sound", "")
        count = max(1, int(bell.get("count", 1)))
        interval = float(bell.get("interval", 2.0))

        logger.info("Ringing: %s × %d", sound, count)

        for i in range(count):
            self.play_callback(sound)
            if i < count - 1:
                _time.sleep(interval)

        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sound": sound,
            "count": count,
        }
        self.history.insert(0, entry)
        self.history = self.history[:100]   # keep last 100

    def trigger_sound(self, sound: str) -> bool:
        """Manually trigger a sound by filename (used by web UI)."""
        if not sound:
            return False
        logger.info("Manual trigger: %s", sound)
        return bool(self.play_callback(sound))

    # ------------------------------------------------------------------
    # History / status
    # ------------------------------------------------------------------

    def get_history(self, limit: int = 20) -> List[Dict]:
        return self.history[:limit]

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
        """Persist the current config dict back to the JSON file."""
        with open(self.config_path, "w") as f:
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
