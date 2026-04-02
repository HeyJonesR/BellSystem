# Quick Start Guide

Get the bell system running in 15 minutes.

## Prerequisites

- Raspberry Pi 5 (or Ubuntu 24.04 machine)
- Python 3.9+
- Audio output (USB sound card, DAC HAT, or speakers)

## 1. Clone and Install

```bash
git clone https://github.com/HeyJonesR/BellSystem.git
cd BellSystem
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure

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

Or skip this — you can configure everything from the web UI.

## 3. Test Audio

```bash
# List available sounds
ls config/audio_samples/carillon-bells/
```

## 4. Run

```bash
python3 run_web_ui.py
```

## 5. Open the Dashboard

Go to `http://localhost:5000` in a browser.

From the dashboard you can:
- Add / edit / delete scheduled bells
- Pick any sound from the dropdown
- Trigger a sound manually
- Stop playback
- Adjust volume
- Configure quiet hours
- View playback history

## Common Tasks

### Add a Bell

1. Click **"+ Add Bell"**
2. Set the time (HH:MM)
3. Pick a sound from the dropdown
4. Optionally set count (rings) and interval (seconds between rings)
5. Click **Save**

### Change Quiet Hours

1. Click **Edit** next to "Quiet Hours"
2. Toggle enabled, set start and end times
3. Click **Save**

### Add New Sound Files

Drop any `.wav` or `.mp3` file into `config/audio_samples/` (or a subfolder).
It appears in the web UI automatically — no restart needed.

## Install as a System Service

For a dedicated Pi that runs 24/7:

```bash
sudo useradd -r -m -d /opt/bells -s /bin/bash bells
sudo usermod -aG audio bells
sudo mkdir -p /opt/bells
sudo chown bells:bells /opt/bells
sudo -u bells git clone https://github.com/HeyJonesR/BellSystem.git /opt/bells
cd /opt/bells
sudo -u bells python3 -m venv venv
sudo -u bells venv/bin/pip install -r requirements.txt
sudo cp systemd/chapel-bells-web.service /etc/systemd/system/midway-bells.service
sudo systemctl daemon-reload
sudo systemctl enable --now midway-bells
```

Check status:
```bash
sudo systemctl status midway-bells
journalctl -u midway-bells -f
```

## Troubleshooting

### No Audio
```bash
aplay -l                    # list audio devices
speaker-test -c2 -t sine    # test speakers
amixer -c 0 scontrols       # check volume controls
```

### Bell Not Ringing
```bash
date                        # check time and timezone
timedatectl
```
Check quiet hours on the dashboard — bells are suppressed during quiet hours.

### Web UI Not Accessible
```bash
sudo systemctl status midway-bells
ss -tlnp | grep 5000
```

## Next Steps

- [Full Installation Guide](./docs/INSTALLATION.md)
- [Raspberry Pi Setup](./docs/RASPBERRY_PI_SETUP.md)
- [API Reference](./docs/API.md)
