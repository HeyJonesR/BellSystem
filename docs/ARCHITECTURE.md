# ChapelBells - Modern Church Bell System Architecture

## System Overview

ChapelBells is a lightweight, automated church bell system designed for Linux/Raspberry Pi deployment. It provides reliable bell scheduling with DST awareness, quiet hours management, and web-based administration.

```
┌─────────────────────────────────────────────────────────┐
│              Linux Machine (Ubuntu/Raspbian)            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │         ChapelBells Core Application            │   │
│  │         (Python 3.9+)                           │   │
│  │                                                  │   │
│  │  ┌─────────────┐  ┌──────────────┐             │   │
│  │  │ Scheduler   │  │ Audio Engine │             │   │
│  │  │ Engine      │  │ (ALSA/Pulse) │             │   │
│  │  │             │  │              │             │   │
│  │  │ - DST       │  │ - WAV/FLAC   │             │   │
│  │  │ - Rules     │  │ - Volume     │             │   │
│  │  │ - Calendar  │  │ - Profiles   │             │   │
│  │  └─────────────┘  └──────────────┘             │   │
│  │         ↓              ↓                        │   │
│  │  ┌─────────────┐  ┌──────────────┐             │   │
│  │  │ Astro Calc  │  │ Config Store │             │   │
│  │  │             │  │ (SQLite/JSON)│             │   │
│  │  │ - Sunrise   │  │              │             │   │
│  │  │ - Sunset    │  │ - Schedules  │             │   │
│  │  │ - GeoLoc    │  │ - Settings   │             │   │
│  │  └─────────────┘  └──────────────┘             │   │
│  │         ↓                                       │   │
│  │  ┌─────────────────────────────────────┐       │   │
│  │  │ System Time (NTP-synced)            │       │   │
│  │  │ + DST Auto-adjustment               │       │   │
│  │  └─────────────────────────────────────┘       │   │
│  └─────────────────────────────────────────────────┘   │
│         ↓                      ↓                        │
│  ┌─────────────────┐  ┌──────────────────┐             │
│  │ Systemd Service │  │ Flask Web Admin  │             │
│  │ - Auto-start    │  │ - Dashboard      │             │
│  │ - Restart logic │  │ - Schedule edit  │             │
│  │ - Logging       │  │ - Settings       │             │
│  └─────────────────┘  └──────────────────┘             │
│                              ↓                         │
│                       ┌─────────────────┐              │
│                       │ HTTP:5000       │              │
│                       │ Local network   │              │
│                       └─────────────────┘              │
│                                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │ Hardware I/O                                 │    │
│  │ - Audio Jack → Amplifier                     │    │
│  │ - GPIO (optional) → Relays, lights           │    │
│  └──────────────────────────────────────────────┘    │
│                                                        │
└─────────────────────────────────────────────────────────┘

        ↓                              ↓
   
   ┌─────────────────┐    ┌──────────────────┐
   │ External Amp    │    │ Admin Workstation│
   │ + Speakers      │    │ or Mobile device │
   └─────────────────┘    └──────────────────┘
```

## Component Breakdown

### 1. **Scheduler Engine** (`scheduler.py`)
- Maintains in-memory schedule rules
- Evaluates rules at each check interval (1 second minimum)
- Supports: hourly chimes, call-to-service, special events
- DST-aware via system time
- Calendar-based rules (weekday patterns, seasonal overrides)

### 2. **Audio Engine** (`audio.py`)
- Abstracts audio playback (ALSA/PulseAudio)
- Loads WAV/FLAC samples
- Manages volume levels
- Profiles: traditional carillon, Westminster quarters, custom
- Graceful degradation if audio device unavailable

### 3. **Astronomical Calculator** (`astro.py`)
- Calculates sunrise/sunset for given location
- Powers quiet hours logic
- Location: configurable (lat/lon or city name)
- Uses ephem library or equivalent

### 4. **Configuration Store** (`config/`)
- SQLite database or JSON files
- Persistent: schedules, settings, event logs
- Human-editable YAML for initial setup
- Atomic writes for reliability

### 5. **Web Admin UI** (`web/app.py`)
- Flask or FastAPI server
- Dashboard with calendar/rule editor
- Location & quiet hours settings
- Audio profile selector
- Simple authentication (basic auth or local token)

### 6. **Systemd Service**
- Auto-starts on boot
- Restart on failure (exponential backoff)
- Integrated logging (journalctl)
- Graceful shutdown handling

### 7. **Logging & Events**
- journalctl integration
- Local event log (bell playback history)
- Configurable log rotation

## Data Flow

```
System Time (NTP)
      ↓
  ┌─────────────────────────────────────┐
  │ Scheduler Loop (1-second interval)  │
  │                                     │
  │ 1. Get current time (DST aware)     │
  │ 2. Load applicable rules            │
  │ 3. Check: event scheduled?          │
  │ 4. Check: within allowed hours?     │
  │    - Not in quiet hours?            │
  │    - Daylight/darkness rules?       │
  │ 5. For each valid event:            │
  │    - Trigger audio playback         │
  │    - Log event                      │
  │ 6. Sleep until next second          │
  └─────────────────────────────────────┘
      ↓
  Audio Playback
  + Event Logging
```

## Key Design Principles

1. **Simplicity**: No cloud dependency, minimal external services
2. **Resilience**: Survives power loss, network outage, clock skew
3. **Low resource**: Runs efficiently on Pi zero/3/4/5
4. **Time-aware**: Automatic DST, sunrise/sunset calculations
5. **Maintainability**: Clear separation of concerns, comprehensive logging

## Configuration Example

```yaml
location:
  latitude: 40.7128
  longitude: -74.0060
  timezone: America/New_York

quiet_hours:
  enabled: true
  start: "21:00"  # 9 PM
  end: "07:00"    # 7 AM

schedules:
  - name: "Hourly Chimes"
    rule: "every hour at :00"
    audio_profile: "westminster"
    active_hours: "07:00-21:00"
  
  - name: "Call to Service"
    rule: "sunday at 10:00"
    audio_profile: "traditional_carillon"
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.9+ |
| Scheduler | APScheduler or custom loop |
| Audio | PyAudio + ALSA/PulseAudio |
| Web UI | Flask + Bootstrap 5 |
| Database | SQLite3 |
| Logging | Python logging + journalctl |
| Astronomy | PyEphem or manual calculations |
| Init System | systemd |
| OS | Ubuntu Server 20.04+ / Raspbian Bullseye+ |

## Deployment Target

- **Raspberry Pi 5** (4GB RAM, 64-bit)
- **Raspberry Pi 4** (2GB+ RAM)
- **Ubuntu Server 22.04 LTS** (generic x86/ARM)
- **Estimated resource usage**:
  - CPU: <2% average
  - Memory: ~40-50 MB
  - Storage: ~100 MB (+ audio samples)
  - Uptime target: 99.9%
