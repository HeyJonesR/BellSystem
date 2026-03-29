#!/usr/bin/env python3
"""
Quick script to run the ChapelBells web UI locally for testing.
Uses local directories instead of system directories.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up local directories for testing
local_config = Path.home() / ".chapel_bells" / "config"
local_audio = Path.home() / ".chapel_bells" / "audio"
local_config.mkdir(parents=True, exist_ok=True)
local_audio.mkdir(parents=True, exist_ok=True)

# Create sample config if it doesn't exist
sample_config = local_config / "schedule.yaml"
if not sample_config.exists():
    sample_config.write_text("""location:
  name: Test Church
  latitude: 40.7128
  longitude: -74.0060
  timezone: America/New_York

events:
  - name: "Sunday Service"
    rule: "sunday at 10:00"
    profile: "westminster"
    tone: "bell"
    description: "Sunday morning service bell"

  - name: "Hourly Chimes"
    rule: "every hour"
    profile: "westminster"
    tone: "bell"
    description: "Hourly chime"
    active_after: "07:00"
    active_before: "21:00"

quiet_hours:
  enabled: true
  start: "21:00"
  end: "07:00"
""")

from chapel_bells import ChapelBells

# Create ChapelBells instance with local directories
app = ChapelBells(
    config_dir=str(local_config),
    audio_dir=str(local_audio)
)

# Import after ChapelBells is created
from chapel_bells.web.app import ChapelBellsWeb

# Create Flask app
web = ChapelBellsWeb(app)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ChapelBells Web UI - Test Mode")
    print("="*60)
    print(f"Config: {local_config}")
    print(f"Audio:  {local_audio}")
    print("\nStarting Flask development server...")
    print("Open browser to: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    web.app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
