# ChapelBells Installation & Deployment Guide

## Overview
ChapelBells is a lightweight church bell automation system for Linux.
This guide covers setup on Ubuntu Server 24.04 LTS or Raspberry Pi 5 (Bookworm).

## System Requirements

### Hardware
- **Raspberry Pi 5** (recommended) or x86 Linux machine
- **2GB+ RAM** (4GB+ recommended)
- **100MB disk space** (+ audio samples)
- **Audio output** — one of:
  - USB sound card / DAC
  - I2S DAC HAT (HiFiBerry DAC+, IQaudio DAC+, Adafruit I2S)
  - 3.5mm headphone jack (Pi 5 has no onboard jack — use a HAT or USB)
- **Amplifier + speaker** connected to audio output
- **Network connectivity** (for NTP time sync)

### Sound Board / DAC HAT Setup (Raspberry Pi 5)

The Pi 5 has **no onboard 3.5mm audio jack**. You need an external audio device:

#### Option A: USB DAC (easiest)
```bash
# Plug in USB sound card, verify it appears
aplay -l
# Look for "USB Audio Device" — note the card number
```

#### Option B: I2S DAC HAT (best quality)
Supported HATs (all Pi 5 compatible):
- **HiFiBerry DAC+ / DAC2 Pro** — high-quality stereo DAC
- **IQaudio DAC+** — Raspberry Pi official
- **Adafruit I2S Audio Bonnet** — budget option

```bash
# Edit boot config for your HAT
sudo nano /boot/firmware/config.txt

# Add ONE of these lines (depending on your HAT):
dtoverlay=hifiberry-dacplus
# dtoverlay=iqaudio-dacplus
# dtoverlay=adafruit-i2s

# Disable onboard audio (if present)
# dtparam=audio=off

sudo reboot

# Verify DAC appears
aplay -l
# Set as default ALSA device
sudo nano /etc/asound.conf
```

Example `/etc/asound.conf` for HiFiBerry:
```
pcm.!default {
    type hw
    card 0
}
ctl.!default {
    type hw
    card 0
}
```

### Software Prerequisites

```bash
# Ubuntu 24.04 LTS / Raspberry Pi OS Bookworm
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
    pipewire pipewire-pulse pipewire-alsa alsa-utils \
    libsdl2-mixer-2.0-0 libsdl2-2.0-0 git
```

> **Note**: Ubuntu 24.04 uses PipeWire as the default audio stack.
> The `pipewire-pulse` package provides PulseAudio compatibility.
> ChapelBells will try PipeWire → PulseAudio → ALSA automatically.

## Installation Steps

### 1. Create System User

```bash
# Create dedicated user
sudo useradd -r -m -d /opt/bells -s /bin/bash bells
sudo usermod -aG audio bells

# Create log directory
sudo mkdir -p /var/log/bells
sudo chown bells:bells /var/log/bells
```

### 2. Install ChapelBells

```bash
# Clone repository
sudo -u bells git clone https://github.com/HeyJonesR/BellSystem.git /opt/bells
cd /opt/bells

# Create Python virtual environment
sudo -u bells python3 -m venv venv
sudo -u bells venv/bin/pip install -r requirements.txt
```

### 3. Audio Samples

The repo ships with 16 audio files in `config/audio_samples/`:

```
config/audio_samples/
├── carillon/
│   └── bell.wav
├── carillon-bells/
│   ├── america-the-beautiful.mp3
│   ├── ave-maria.mp3
│   ├── carillon-peal.mp3
│   ├── god-rest-ye-merry-gentlemen.mp3
│   ├── hallelujah-chorus.mp3
│   ├── hark-the-herald-angels-sing.mp3
│   ├── jesu-joy-of-mans-desiring.mp3
│   ├── joyful-joyful.mp3
│   ├── morning-has-broken.mp3
│   ├── noon-hour-bell-strike.mp3
│   ├── swinging-english-tuned-bell.mp3
│   ├── swinging-flemish-bell.mp3
│   └── westminster-chimes-full.mp3
├── traditional/
│   └── bell.wav
└── westminster/
    └── bell.wav
```

To **add your own sounds**, drop `.wav` or `.mp3` files into any subfolder
under `config/audio_samples/`. They appear in the web UI automatically.

Audio requirements:
- Format: **WAV** or **MP3**
- Sample rate: 44.1 kHz or 48 kHz
- Channels: Mono or Stereo

### 4. Configure

Edit `config/schedule.json`:

```bash
sudo -u bells nano /opt/bells/config/schedule.json
```

The config schema:

```json
{
  "audio_dir": "audio_samples",
  "volume": 80,
  "quiet_hours": {
    "enabled": true,
    "start": "21:00",
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
      "count": 1,
      "interval": 2.0
    },
    {
      "time": "18:00",
      "sound": "carillon-bells/joyful-joyful.mp3"
    }
  ]
}
```

Fields:
- **`audio_dir`** — path to audio samples (relative to config directory)
- **`volume`** — master volume 0–100
- **`quiet_hours`** — suppress all bells between `start` and `end`
- **`bells[]`** — scheduled events:
  - `time` — HH:MM (24-hour, required)
  - `sound` — file path relative to `audio_dir` (required)
  - `count` — number of rings (default 1)
  - `interval` — seconds between rings when count > 1 (default 2.0)

You can also use `config/schedule.yaml` — the scheduler auto-detects
the format by file extension.

### 5. Install systemd Services

```bash
# Copy service files
sudo cp /opt/bells/systemd/chapel-bells-web.service /etc/systemd/system/midway-bells.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable midway-bells.service
sudo systemctl start midway-bells.service
```

> The web service (`run_web_ui.py`) runs the scheduler AND the dashboard
> together. For a dedicated Pi this is the simplest setup.
>
> If you prefer to run the scheduler headless (no web UI), use
> `chapel-bells.service` instead, which runs `python -m chapel_bells`.

### 6. Enable Audio at Boot

```bash
# Verify the bells user is in the audio group
groups bells   # should show "audio"

# Test audio output
sudo -u bells aplay /opt/bells/config/audio_samples/westminster/bell.wav

# Check PipeWire is running
systemctl --user status pipewire

# Check ALSA device list
aplay -l
```

### 7. Configure NTP (Time Sync)

```bash
# Verify NTP is running
timedatectl status

# If not synced:
sudo systemctl restart systemd-timesyncd

# Check sync status (may take a few minutes)
timedatectl timesync-status
```

## Configuration

### Editing Schedule

Modify `/opt/bells/config/schedule.json` directly or use the web dashboard:

```bash
sudo -u bells nano /opt/bells/config/schedule.json
sudo systemctl restart midway-bells
```

Or use the web UI at `http://<ip>:5000` — changes are saved to the
config file automatically, no restart needed.

### Quiet Hours

Suppress all bell playback during a time window:

```json
"quiet_hours": {
  "enabled": true,
  "start": "21:00",
  "end": "07:00"
}
```

The window spans midnight when `start` > `end` (e.g., 21:00–07:00).

### Web Dashboard

Access at: `http://<ip>:5000`

Features:
- View / add / edit / delete scheduled bells
- Pick any sound from available audio files
- Manual trigger and stop playback
- Adjust volume
- Configure quiet hours
- View recent playback history

## Troubleshooting

### Audio Not Playing

```bash
# Check audio devices
aplay -l

# Test playback
sudo -u bells aplay /opt/bells/config/audio_samples/westminster/bell.wav

# Check ALSA mixer
alsamixer

# Verify user is in audio group
groups bells   # should include 'audio'

# Test pygame initialisation
sudo -u bells /opt/bells/venv/bin/python -c "import pygame; pygame.mixer.init(); print('OK')"
```

### Service Not Starting

```bash
# Check service status
sudo systemctl status midway-bells

# View detailed logs
journalctl -u midway-bells -n 50 --no-pager

# Check Python errors
journalctl -u midway-bells -n 30 --no-pager | grep -i error
```

### Time Not Syncing

```bash
# Check NTP status
timedatectl

# Fix timezone
sudo timedatectl set-timezone America/New_York

# Restart time sync
sudo systemctl restart systemd-timesyncd
timedatectl timesync-status
```

### Bell Ringing at Wrong Time

```bash
# Check system time
date

# Verify config
cat /opt/bells/config/schedule.json

# Check logs for trigger events
journalctl -u midway-bells | grep -i "ringing\|trigger"
```

## Maintenance

### Log Rotation

Logs go to systemd journal by default:
```bash
# Live log stream
journalctl -u midway-bells -f

# Last 100 lines
journalctl -u midway-bells -n 100 --no-pager
```

If `--log-file` is used, logs are auto-rotated at 5 MB (3 backups).

### Backup Configuration

```bash
cp /opt/bells/config/schedule.json ~/schedule-backup-$(date +%F).json
```

### Update ChapelBells

```bash
cd /opt/bells
sudo -u bells git pull
sudo -u bells venv/bin/pip install -r requirements.txt
sudo systemctl restart midway-bells
```

### Memory Usage

```bash
# Monitor resource usage
ps aux | grep bells
free -h
top -p $(pgrep -f chapel_bells)
```

## Security Considerations

### Network Access

- Web UI listens on all interfaces by default (port 5000)
- Use firewall rules to restrict access:

```bash
sudo ufw allow 5000/tcp from 192.168.1.0/24   # local subnet only
```

### User Permissions

```bash
# Verify bells user is non-privileged
id bells

# Check file permissions
ls -la /opt/bells/config/
```

### Logs & Audit

```bash
# Review recent activity
journalctl -u midway-bells -S "1 day ago"
```

## Systemd Service Commands

```bash
# Start/stop
sudo systemctl start midway-bells
sudo systemctl stop midway-bells
sudo systemctl restart midway-bells

# Check status
sudo systemctl status midway-bells

# View logs
journalctl -u midway-bells -n 100
journalctl -u midway-bells -f   # follow

# Enable/disable auto-start
sudo systemctl enable midway-bells
sudo systemctl disable midway-bells
```

## Adding New Audio Files

Drop any `.wav` or `.mp3` file into `config/audio_samples/` (or a
subfolder). The web UI discovers new files automatically via a directory
scan — no code changes or restart required.

## Uninstallation

```bash
# Stop service
sudo systemctl stop midway-bells
sudo systemctl disable midway-bells

# Remove systemd files
sudo rm /etc/systemd/system/midway-bells.service
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/bells

# Remove user
sudo userdel -r bells

# Remove logs
sudo rm -rf /var/log/bells
```

---

For additional support, check logs or visit the project repository.
