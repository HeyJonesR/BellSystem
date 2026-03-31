# Midway UMC Bells — Raspberry Pi 5 Deployment Guide

Complete instructions for setting up a dedicated Raspberry Pi 5 to run the
Midway UMC Bells automated church bell system.

---

## What You Need

### Hardware
| Item | Notes |
|------|-------|
| **Raspberry Pi 5** (4 GB or 8 GB) | 2 GB works but 4 GB recommended |
| **microSD card** (32 GB+) | Use a quality card (SanDisk Extreme, Samsung EVO) |
| **USB-C power supply** (27 W / 5.1 V 5 A) | Official Pi 5 PSU recommended |
| **Audio output** — pick one | See "Audio Setup" below |
| **Amplifier + speakers** | Connected to the audio output |
| **Ethernet cable** or Wi-Fi | For time sync and web dashboard access |
| **Case** (optional) | Official Pi 5 case or Argon ONE |

### Audio Output Options

The Pi 5 has **no 3.5 mm headphone jack**. Choose one:

| Option | Pros | Setup Difficulty |
|--------|------|-----------------|
| **USB DAC / sound card** | Plug-and-play, cheap ($10–30) | Easy |
| **I2S DAC HAT** (HiFiBerry DAC+, IQaudio DAC+) | Best audio quality | Medium |
| **HDMI audio extractor** | Uses existing HDMI port | Easy |

---

## Step 1 — Flash Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Choose **Raspberry Pi OS Lite (64-bit)** — Bookworm or newer.
3. Click the gear icon and pre-configure:
   - **Hostname**: `midway-bells`
   - **Enable SSH**: yes (use password or key)
   - **Set username**: `pi` (or your preference)
   - **Wi-Fi** (if not using Ethernet): enter your network SSID/password
   - **Locale / timezone**: set to your church's timezone
4. Flash to the microSD card and boot the Pi.

---

## Step 2 — Initial Pi Setup

SSH into the Pi (or connect a keyboard):

```bash
ssh pi@midway-bells.local
```

Update the system:

```bash
sudo apt update && sudo apt upgrade -y
```

Install dependencies:

```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    pipewire pipewire-pulse pipewire-alsa alsa-utils \
    git libsdl2-mixer-2.0-0 libsdl2-2.0-0
```

Set the timezone (if not already correct):

```bash
sudo timedatectl set-timezone America/New_York
timedatectl status   # verify "NTP service: active"
```

---

## Step 3 — Audio Setup

### Option A: USB DAC (easiest)

1. Plug in the USB sound card.
2. Verify it appears:

```bash
aplay -l
```

You should see something like `card 1: Device [USB Audio Device]`.

3. Set it as the default output:

```bash
sudo tee /etc/asound.conf << 'EOF'
pcm.!default {
    type hw
    card 1
}
ctl.!default {
    type hw
    card 1
}
EOF
```

> **Replace `card 1`** with the card number from `aplay -l`.

### Option B: I2S DAC HAT

1. Attach the HAT to the Pi's GPIO header.
2. Edit the boot config:

```bash
sudo nano /boot/firmware/config.txt
```

Add the overlay for your HAT (uncomment one):

```ini
# HiFiBerry DAC+ / DAC2 Pro
dtoverlay=hifiberry-dacplus

# IQaudio DAC+ (Raspberry Pi official)
# dtoverlay=iqaudio-dacplus
```

3. Reboot and verify:

```bash
sudo reboot
# after reboot:
aplay -l
```

4. Create `/etc/asound.conf` pointing to card 0 (the HAT).

### Test Audio

```bash
# Generate a test tone (5 seconds)
speaker-test -t sine -f 440 -l 1 -D default
```

You should hear a 440 Hz tone through your amplifier/speakers.

---

## Step 4 — Install the Bell System

### Create a dedicated user

```bash
sudo useradd -r -m -d /opt/bells -s /bin/bash bells
sudo usermod -aG audio bells
sudo mkdir -p /var/log/bells
sudo chown bells:bells /var/log/bells
```

### Clone the repository

```bash
sudo -u bells git clone https://github.com/HeyJonesR/BellSystem.git /opt/bells
```

> If the repo is private, use a personal access token:
> `https://<TOKEN>@github.com/HeyJonesR/BellSystem.git`

### Set up Python virtual environment

```bash
cd /opt/bells
sudo -u bells python3 -m venv venv
sudo -u bells venv/bin/pip install -r requirements.txt
```

### Test that it runs

```bash
sudo -u bells venv/bin/python run_web_ui.py &
# Open http://midway-bells.local:5000 in a browser
# Press Ctrl+C to stop
```

---

## Step 5 — Install systemd Services

The repo includes ready-to-use service files:

```bash
# Copy service files
sudo cp /opt/bells/systemd/chapel-bells-web.service /etc/systemd/system/midway-bells.service

# Reload systemd
sudo systemctl daemon-reload

# Enable on boot and start now
sudo systemctl enable midway-bells.service
sudo systemctl start midway-bells.service
```

Check status:

```bash
sudo systemctl status midway-bells.service
```

View logs:

```bash
journalctl -u midway-bells -f
```

> **Note**: The web service runs the scheduler AND the dashboard together
> via `run_web_ui.py`. For a dedicated Pi this is the simplest setup.
> If you prefer to run the scheduler separately (headless, no web UI),
> use `chapel-bells.service` instead, which runs `python -m chapel_bells`.

---

## Step 6 — Access the Dashboard

From any device on the same network, open a browser to:

```
http://midway-bells.local:5000
```

Or use the Pi's IP address:

```bash
# Find the IP on the Pi
hostname -I
```

Then go to `http://<IP>:5000`.

### What you can do from the dashboard:
- **View / add / edit / delete** scheduled bells
- **Pick any sound** from the 16 audio files (carillon hymns, traditional, westminster)
- **Trigger a sound manually** with the Play button
- **Stop playback** instantly with the Stop button
- **Adjust volume**
- **Configure quiet hours** (click ✏ Edit on the Quiet Hours badge)
- **View recent playback** history

---

## Step 7 — Connect Amplifier & Speakers

Typical church setup:

```
Pi 5 → USB DAC (or DAC HAT) → 3.5mm/RCA cable → Amplifier → Speakers
```

Recommended:
- **Outdoor/tower speakers**: weather-rated horn speakers (Atlas, Bogen)
- **Amplifier**: 70V commercial amp for long cable runs, or a standard
  home amp for short runs
- **Volume**: set digital volume to ~80% in the dashboard, adjust the
  physical amp to your desired loudness

---

## Maintenance

### Update the software

```bash
cd /opt/bells
sudo -u bells git pull
sudo -u bells venv/bin/pip install -r requirements.txt
sudo systemctl restart midway-bells.service
```

### Edit the schedule without the web UI

```bash
sudo -u bells nano /opt/bells/config/schedule.json
sudo systemctl restart midway-bells.service
```

### Check logs

```bash
# Live log stream
journalctl -u midway-bells -f

# Last 50 lines
journalctl -u midway-bells -n 50 --no-pager
```

### Backup the configuration

```bash
cp /opt/bells/config/schedule.json ~/schedule-backup-$(date +%F).json
```

### Reboot the Pi

The service starts automatically on boot — no action needed after a
power outage or reboot.

---

## Troubleshooting

### No sound

```bash
# 1. Check audio devices
aplay -l

# 2. Test with a direct file
sudo -u bells aplay /opt/bells/config/audio_samples/westminster/bell.wav

# 3. Check the user is in the audio group
groups bells    # should show "audio"

# 4. Verify ALSA config
cat /etc/asound.conf

# 5. Check pygame can initialize (from the venv)
sudo -u bells /opt/bells/venv/bin/python -c "import pygame; pygame.mixer.init(); print('OK')"
```

### Web dashboard not loading

```bash
# Check service status
sudo systemctl status midway-bells.service

# Check if port 5000 is open
ss -tlnp | grep 5000

# Check firewall (if UFW is installed)
sudo ufw allow 5000/tcp
```

### Wrong time / bells ringing at wrong time

```bash
# Verify timezone
timedatectl

# Fix timezone
sudo timedatectl set-timezone America/New_York

# Verify NTP sync
timedatectl timesync-status
```

### Service won't start after update

```bash
# Check for Python errors
journalctl -u midway-bells -n 30 --no-pager

# Reinstall dependencies
cd /opt/bells
sudo -u bells venv/bin/pip install -r requirements.txt

# Restart
sudo systemctl restart midway-bells.service
```
