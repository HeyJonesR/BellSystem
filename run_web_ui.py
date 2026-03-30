#!/usr/bin/env python3
"""Run the ChapelBells web UI locally."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from chapel_bells.audio import AudioPlayer
from chapel_bells.scheduler import BellScheduler
from chapel_bells.web.app import create_web_app

config_path = Path(__file__).parent / "config" / "schedule.json"
audio_dir = Path(__file__).parent / "audio_samples"

player = AudioPlayer(audio_dir=str(audio_dir), volume=80)
scheduler = BellScheduler(config_path=str(config_path), play_callback=player.play)

flask_app = create_web_app(scheduler, player)

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Midway UMC Bells Web UI")
    print("=" * 60)
    print(f"Config: {config_path}")
    print(f"Audio:  {audio_dir}")
    print("\nOpen browser to: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    flask_app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
