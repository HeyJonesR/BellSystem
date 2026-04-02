# Installation Guide

## System Requirements

- **OS**: Ubuntu 24.04 LTS or Raspberry Pi OS Bookworm (64-bit)
- **Python**: 3.9+
- **RAM**: 2 GB minimum (4 GB recommended)
- **Disk**: 100 MB + audio files
- **Audio**: USB sound card or DAC HAT
- **Network**: For NTP time sync and web dashboard access

> For Raspberry Pi-specific setup (flashing OS, audio HATs, hardware),
> see [RASPBERRY_PI_SETUP.md](./RASPBERRY_PI_SETUP.md).

## Install System Packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    pipewire pipewire-pulse pipewire-alsa alsa-utils \
    git libsdl2-mixer-2.0-0 libsdl2-2.0-0
```

## Create Dedicated User

```bash
sudo useradd -r -s /bin/bash bells
sudo usermod -aG audio bells
sudo mkdir -p /opt/bells /var/log/bells
sudo chown bells:bells /opt/bells /var/log/bells
```

## Clone and Install

```bash
sudo -u bells git clone https://github.com/HeyJonesR/BellSystem.git /opt/bells
cd /opt/bells
sudo -u bells python3 -m venv venv
sudo -u bells venv/bin/pip install -r requirements.txt
```

## Configure Audio

See [AUDIO.md](./AUDIO.md) for detailed audio setup.

Quick version:

```bash
# Find your sound card
cat /proc/asound/cards

# Set ALSA default (replace S3 with your card name)
sudo tee /etc/asound.conf << 'EOF'
pcm.!default {
    type plug
    slave.pcm "dmix:S3,0"
}
ctl.!default {
    type hw
    card S3
}
EOF

# Test
sudo -u bells aplay /usr/share/sounds/alsa/Front_Center.wav
```

## Configure Schedule

Edit `/opt/bells/config/schedule.json` or use the web dashboard:

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
    }
  ]
}
```

## Set Timezone

```bash
sudo timedatectl set-timezone America/New_York
timedatectl status   # verify NTP active
```

## Test Run

```bash
sudo -u bells /opt/bells/venv/bin/python /opt/bells/run_web_ui.py &
curl -s http://localhost:5000/api/status
kill %1
```

## Install systemd Service

```bash
sudo cp /opt/bells/systemd/chapel-bells-web.service /etc/systemd/system/midway-bells.service
sudo systemctl daemon-reload
sudo systemctl enable --now midway-bells.service
```

Verify:

```bash
sudo systemctl status midway-bells.service
journalctl -u midway-bells -f
```

## Access the Dashboard

From any device on the same network:

```
http://<machine-ip>:5000
```

Find the IP:

```bash
hostname -I
```

## Maintenance

### Update

```bash
sudo -u bells git -C /opt/bells pull
sudo systemctl restart midway-bells.service
```

### View Logs

```bash
journalctl -u midway-bells -f
journalctl -u midway-bells --since "1 hour ago"
```

### Restart / Stop

```bash
sudo systemctl restart midway-bells.service
sudo systemctl stop midway-bells.service
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| No audio | Check `aplay -l`, verify `asound.conf` card name, check `audio` group |
| "Bell suppressed (quiet hours)" | Adjust quiet hours in the dashboard |
| Web UI not loading | `sudo systemctl status midway-bells`, check port 5000 |
| Service won't start | `journalctl -u midway-bells --no-pager -n 30` |
| Config changes lost | Dashboard saves to `schedule.json` automatically |

## Uninstall

```bash
sudo systemctl stop midway-bells.service
sudo systemctl disable midway-bells.service
sudo rm /etc/systemd/system/midway-bells.service
sudo systemctl daemon-reload
sudo userdel -r bells
sudo rm -rf /var/log/bells
```
