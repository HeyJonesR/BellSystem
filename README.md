# Midway UMC Bells — Automated Church Bell System

A lightweight church bell automation system for Raspberry Pi / Linux.
Web dashboard for scheduling, manual playback, and quiet hours.

## Features

- **Scheduled bells** — set daily bell times via the web UI
- **16 built-in sounds** — carillon hymns, Westminster chimes, traditional bells
- **Web dashboard** — add/edit/delete bells, trigger manually, adjust volume
- **Quiet hours** — automatically suppress bells overnight
- **Playback history** — see what played and when
- **systemd service** — starts on boot, auto-restarts on failure

## Quick Start

See [QUICKSTART.md](./QUICKSTART.md) for a 15-minute setup.

For Raspberry Pi deployment, see [docs/RASPBERRY_PI_SETUP.md](./docs/RASPBERRY_PI_SETUP.md).

## How It Works

```
schedule.json  →  Scheduler  →  pygame.mixer  →  USB DAC  →  Amp  →  Speakers
                      ↕
                  Flask Web UI (:5000)
```

- **Scheduler** reads `config/schedule.json`, fires bells at the configured times
- **Audio** plays MP3/WAV files via pygame.mixer through ALSA
- **Web UI** on port 5000 lets you manage everything from a browser

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.9+ |
| Web | Flask |
| Scheduling | `schedule` library |
| Audio | pygame.mixer (SDL2) → ALSA |
| Config | JSON (`config/schedule.json`) |
| Process | systemd |

## Configuration

Edit `config/schedule.json`:

```json
{
  "audio_dir": "audio_samples",
  "volume": 80,
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "07:00"
  },
  "bells": [
    {
      "time": "09:00",
      "sound": "carillon-bells/westminster-chimes-full.mp3"
    },
    {
      "time": "12:00",
      "sound": "carillon-bells/noon-hour-bell-strike.mp3",
      "count": 1
    }
  ]
}
```

Or manage everything from the web dashboard — no file editing needed.

## API Endpoints

```
GET   /                        Dashboard
GET   /api/status              System status
GET   /api/schedule            List bells
POST  /api/schedule            Add bell
PUT   /api/schedule/<idx>      Update bell
DELETE /api/schedule/<idx>     Delete bell
GET   /api/sounds              List available sound files
POST  /api/trigger             Play a sound manually
POST  /api/stop                Stop playback
PUT   /api/volume              Set volume (0-100)
GET   /api/history             Playback history
PUT   /api/quiet_hours         Update quiet hours
```

See [docs/API.md](./docs/API.md) for full request/response details.

## Project Structure

```
ChurchBell/
├── run_web_ui.py              # Entry point (web UI + scheduler)
├── config/
│   ├── schedule.json          # Bell schedule and settings
│   └── audio_samples/         # Sound files (MP3/WAV)
│       ├── carillon-bells/    # 13 carillon hymn recordings
│       ├── traditional/       # Traditional bell sounds
│       └── westminster/       # Westminster chime
├── src/chapel_bells/
│   ├── scheduler.py           # Schedule engine
│   ├── audio.py               # Playback via pygame.mixer
│   ├── astro.py               # Sunrise/sunset calculations
│   └── web/
│       ├── app.py             # Flask routes and API
│       └── templates/
│           └── dashboard.html # Web UI
├── systemd/                   # Service files for deployment
├── requirements.txt           # Python dependencies
└── docs/                      # Documentation
```

## Documentation

- [QUICKSTART.md](./QUICKSTART.md) — 15-minute setup guide
- [docs/INSTALLATION.md](./docs/INSTALLATION.md) — Full installation reference
- [docs/RASPBERRY_PI_SETUP.md](./docs/RASPBERRY_PI_SETUP.md) — Pi 5 deployment guide
- [docs/API.md](./docs/API.md) — REST API reference
- [docs/AUDIO.md](./docs/AUDIO.md) — Audio setup and sound file info
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) — System design

## Requirements

- Python 3.9+
- Linux (Ubuntu 24.04 LTS or Raspberry Pi OS Bookworm)
- USB sound card or DAC HAT for Raspberry Pi 5
- Amplifier + speakers

## License

See audio file licenses in `config/audio_samples/carillon-bells/_readme_and_license.txt`.
