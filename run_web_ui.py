#!/usr/bin/env python3
"""Run the ChapelBells web UI locally."""

import logging
import sys
import threading
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chapel_bells.audio import AudioPlayer
from chapel_bells.scheduler import BellScheduler
from chapel_bells.web.app import create_web_app

config_path = Path(__file__).parent / "config" / "schedule.json"

scheduler = BellScheduler(config_path=str(config_path), play_callback=lambda _s: False)
player = AudioPlayer(audio_dir=scheduler.audio_dir, volume=scheduler.volume)
scheduler.play_callback = player.play
scheduler.schedule_all()


def _scheduler_loop():
    """Background thread that fires scheduled bells."""
    while True:
        scheduler.run_pending()
        time.sleep(1)


threading.Thread(target=_scheduler_loop, daemon=True, name="scheduler").start()

flask_app = create_web_app(scheduler, player)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Midway UMC Bells Web UI")
    print("=" * 60)
    print(f"Config: {config_path}")
    print(f"Audio:  {player.audio_dir}")
    print("\nOpen browser to: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    flask_app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
