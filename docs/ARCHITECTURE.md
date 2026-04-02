# Architecture

## Overview

Midway UMC Bells is a single-process Python application that runs a Flask
web server and an in-process scheduler. It plays audio files through
pygame.mixer (SDL2) via ALSA to a USB sound card.

```
┌──────────────────────────────────────────────┐
│           Linux (Ubuntu 24.04 / Pi OS)       │
│                                              │
│  run_web_ui.py                               │
│  ┌────────────────────────────────────────┐  │
│  │                                        │  │
│  │  BellScheduler        AudioPlayer      │  │
│  │  (schedule lib)       (pygame.mixer)   │  │
│  │       │                    │           │  │
│  │       ▼                    ▼           │  │
│  │  schedule.json        ALSA / SDL2      │  │
│  │                            │           │  │
│  │  Flask (:5000)             │           │  │
│  │  ├─ dashboard.html         │           │  │
│  │  └─ /api/*                 │           │  │
│  └────────────────────────────┼───────────┘  │
│                               ▼              │
│                          USB DAC             │
│                            │                 │
│  systemd (midway-bells)    ▼                 │
│                       Amp → Speakers         │
└──────────────────────────────────────────────┘

        Browser ──HTTP──▶ :5000
```

## Components

### Scheduler (`scheduler.py`)

- Reads `config/schedule.json` for bell times, sounds, quiet hours
- Uses the `schedule` library to fire events at HH:MM times
- Runs playback in background threads (non-blocking)
- Keeps recent history in a `deque(maxlen=100)`
- Saves config changes back to JSON (or YAML if `.yaml` extension)

### Audio Player (`audio.py`)

- Wraps pygame.mixer for audio playback
- Driver probe chain: `pipewire → pulseaudio → alsa → coreaudio`
- Caches loaded `Sound` objects to avoid repeated disk reads
- 512-sample buffer (~12ms latency at 44.1kHz)
- Supports WAV and MP3 files

### Web UI (`web/app.py` + `dashboard.html`)

- Flask app with Jinja2 templates
- REST API for all operations (schedule CRUD, trigger, volume, quiet hours)
- Sound file discovery — scans `audio_samples/` for `.wav`/`.mp3` files
- `sound_label` Jinja2 filter for human-readable file names

### Astro Calculator (`astro.py`)

- Sunrise/sunset calculations for a configured location
- `is_daytime()` helper (not currently used for scheduling, available for future use)

## Configuration Format

Single JSON file (`config/schedule.json`):

```json
{
  "audio_dir": "audio_samples",
  "volume": 80,
  "quiet_hours": { "enabled": true, "start": "22:00", "end": "07:00" },
  "bells": [
    { "time": "09:00", "sound": "carillon-bells/westminster-chimes-full.mp3" },
    { "time": "12:00", "sound": "carillon-bells/noon-hour-bell-strike.mp3", "count": 1 }
  ]
}
```

`audio_dir` is resolved relative to the config file's parent directory.

## Deployment

- **systemd** manages the process (`midway-bells.service`)
- Runs as dedicated `bells` user (home: `/opt/bells`)
- `SDL_AUDIODRIVER=alsa` set in the service file
- `SupplementaryGroups=audio` for device access
- Security hardening: `NoNewPrivileges`, `ProtectSystem=strict`, `MemoryMax=128M`

## Dependencies

| Package | Purpose |
|---------|---------|
| Flask | Web server and API |
| schedule | Time-based job scheduling |
| pygame | Audio playback (SDL2_mixer) |
| PyYAML | YAML config support |
