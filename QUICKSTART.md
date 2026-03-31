# ChapelBells - Quick Start Guide

Get your church bell system running in 15 minutes!

## Prerequisites

- Raspberry Pi 4/5 or Ubuntu Server 24.04 machine
- Python 3.9+
- Audio output device (speakers/amplifier)

## 5-Minute Setup

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/HeyJonesR/BellSystem.git
cd BellSystem

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

Edit `config/schedule.json` (or `config/schedule.yaml`):

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
    }
  ]
}
```

Key settings:
- **`bells`** — list of scheduled events (`time` in HH:MM, `sound` relative to `audio_dir`)
- **`quiet_hours`** — suppress all bells between `start` and `end`
- **`volume`** — master volume 0–100
- **`audio_dir`** — path to audio samples (relative to config directory)

### 3. Test Audio

The repo ships with 16 audio files in `config/audio_samples/`:

```bash
# List available sounds
ls config/audio_samples/carillon-bells/
ls config/audio_samples/westminster/

# Test playback directly
aplay config/audio_samples/westminster/bell.wav
```

### 4. Run Application

```bash
# Start with web UI (test mode)
python3 run_web_ui.py

# Or start headless (scheduler only)
python3 -m chapel_bells --config config/schedule.json
```

### 5. Access Web UI

Open browser: `http://localhost:5000`

- **View / add / edit / delete** scheduled bells
- **Pick any sound** from the available audio files
- **Trigger a sound manually** with the Play button
- **Stop playback** instantly with the Stop button
- **Adjust volume** with the slider
- **Configure quiet hours** (click ✏ Edit on the Quiet Hours badge)
- **View recent playback** history

## Common Tasks

### Add a Bell via Web UI

1. Click **"+ Add Bell"**
2. Set the time (e.g., 10:00)
3. Pick a sound from the dropdown
4. Optionally set count (rings) and interval (seconds between rings)
5. Click **Save**

### Change Quiet Hours

1. On the dashboard, click **✏ Edit** next to "Quiet Hours"
2. Toggle enabled, set start and end times
3. Click **Save**

### Add New Audio Files

Drop any `.wav` or `.mp3` file into `config/audio_samples/` (or a subfolder).
It will appear in the web UI automatically — no restart needed.

## Install as System Service

```bash
# Create dedicated user
sudo useradd -r -m -d /opt/bells -s /bin/bash bells
sudo usermod -aG audio bells

# Clone to /opt/bells
sudo -u bells git clone https://github.com/HeyJonesR/BellSystem.git /opt/bells
cd /opt/bells
sudo -u bells python3 -m venv venv
sudo -u bells venv/bin/pip install -r requirements.txt

# Install systemd service
sudo cp systemd/chapel-bells-web.service /etc/systemd/system/midway-bells.service
sudo systemctl daemon-reload
sudo systemctl enable midway-bells
sudo systemctl start midway-bells

# Check status
sudo systemctl status midway-bells

# View logs
journalctl -u midway-bells -f
```

## Troubleshooting

### Audio Not Working
```bash
# List audio devices
aplay -l

# Test simple playback
speaker-test -c2 -t sine -f 1000

# Check volume
alsamixer
```

### Bell Not Ringing
```bash
# Check time and timezone
date
timedatectl

# Verify config is loaded
cat config/schedule.json

# Check for quiet hours in the web UI dashboard
```

### Web UI Not Accessible
```bash
# Check if service is running
sudo systemctl status midway-bells

# Check port is listening
ss -tlnp | grep 5000

# Try starting manually
python3 run_web_ui.py
```
sudo cp systemd/chapel-bells-web.service /etc/systemd/system/
sudo cp systemd/chapel-bells-web.socket /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable chapel-bells
sudo systemctl enable chapel-bells-web

# Start services
sudo systemctl start chapel-bells
sudo systemctl start chapel-bells-web

# Check status
sudo systemctl status chapel-bells
journalctl -u chapel-bells -f
```

### Access From Network

```bash
# From any device on network
# Open: http://192.168.1.100:5000

# Edit config remotely
ssh -L 5000:localhost:5000 pi@192.168.1.100
# Then open: http://localhost:5000
```

## Example Schedules

### Basic Church Services

```yaml
events:
  - name: "Sunday Service"
    rule: "sunday at 10:00"
    profile: "carillon"
  
  - name: "Wednesday Service"
    rule: "wednesday at 19:00"
    profile: "traditional"
  
  - name: "Daily Noon Chime"
    rule: "* 12 * * *"
    profile: "light"
    active_after: "07:00"
    active_before: "21:00"
```

### Westminster Quarters (Every Hour)

```yaml
events:
  - name: "Hourly Westminster"
    rule: "every hour"
    profile: "westminster"
    active_after: "07:00"
    active_before: "21:00"
```

### Festival Bell Schedule

```yaml
events:
  - name: "Christmas Eve Special"
    rule: "* 16 25 12 *"  # Dec 25, 4 PM
    profile: "carillon"
    description: "Christmas service bell"

  - name: "New Year's Bell"
    rule: "* 23 1 1 *"  # Jan 1, 11 PM
    profile: "traditional"
```

## Next Steps

- Read [Full Installation Guide](./docs/INSTALLATION.md)
- Check [Architecture Documentation](./docs/ARCHITECTURE.md)
- Review [Configuration Options](./config/schedule.yaml)
- Explore [API Reference](./docs/API.md)

## Support

- Check logs: `journalctl -u chapel-bells`
- Issues: GitHub Issues
- Documentation: `/docs` folder

---

Happy chiming! 🔔
