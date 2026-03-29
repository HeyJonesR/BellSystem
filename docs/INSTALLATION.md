# ChapelBells Installation & Deployment Guide

## Overview
ChapelBells is a modern, lightweight church bell system designed for Linux. This guide covers setup on Raspberry Pi 5 (Bookworm) or Ubuntu Server 22.04+.

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
# Raspberry Pi OS Bookworm / Ubuntu 22.04+
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
    alsa-utils pipewire pipewire-alsa git \
    ffmpeg
```

## Installation Steps

### 1. Create System User

```bash
# Create dedicated user for chapel-bells
sudo useradd -r -s /bin/false -d /var/lib/chapel_bells chapel-bells

# Create necessary directories
sudo mkdir -p /etc/chapel_bells /var/lib/chapel_bells /var/log/chapel_bells
sudo mkdir -p /var/lib/chapel_bells/audio

# Set permissions
sudo chown -R chapel-bells:chapel-bells /etc/chapel_bells /var/lib/chapel_bells /var/log/chapel_bells
sudo chmod 755 /etc/chapel_bells /var/lib/chapel_bells
```

### 2. Install ChapelBells

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/HeyJonesR/BellSystem.git chapel-bells
cd chapel-bells

# Create Python virtual environment
sudo python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Deploy Audio Samples

Create directory structure for bell audio:

```
/var/lib/chapel_bells/audio/
├── westminster/
│   ├── bell.wav
│   ├── tone_1.wav
│   └── tone_2.wav
├── carillon/
│   └── bell.wav
└── traditional/
    └── bell.wav
```

Audio requirements:
- Format: WAV or FLAC
- Sample rate: 44.1kHz or 48kHz
- Channels: Mono or Stereo
- Duration: 2-5 seconds per tone

Generate sample tones:
```bash
# Use SoX to generate test tones
sox -n -r 44100 -c 1 -b 16 bell.wav synth 2 sine 440
```

### 4. Configure System

Copy and customize configuration file:

```bash
sudo cp config/schedule.yaml /etc/chapel_bells/schedule.yaml
sudo nano /etc/chapel_bells/schedule.yaml

# Set correct location (latitude/longitude)
# Configure quiet hours
# Add your church's service times
```

### 5. Install as systemd Service

```bash
# Copy systemd files
sudo cp systemd/chapel-bells.service /etc/systemd/system/
sudo cp systemd/chapel-bells-web.service /etc/systemd/system/
sudo cp systemd/chapel-bells-web.socket /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable chapel-bells.service
sudo systemctl enable chapel-bells-web.service
sudo systemctl start chapel-bells.service
sudo systemctl start chapel-bells-web.service
```

### 6. Enable Audio at Boot

Ensure audio works as non-root user:

```bash
# Add chapel-bells user to audio group
sudo usermod -a -G audio chapel-bells

# Test audio output
speaker-test -c2 -t sine -f 1000

# If using PipeWire (Pi 5 Bookworm default), verify service
systemctl --user status pipewire

# Check ALSA device list
aplay -l

# Test with a WAV file
aplay /var/lib/chapel_bells/audio/westminster/bell.wav
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

Modify `/etc/chapel_bells/schedule.yaml`:

```yaml
events:
  - name: "Morning Chime"
    rule: "every hour"
    profile: "westminster"
    active_after: "07:00"
    active_before: "21:00"
```

**Rule Format:**
- `every hour` - Ring at top of each hour
- `sunday at 10:00` - Ring on Sunday at 10 AM
- `* 12 * * *` - Cron format (noon every day)

Reload configuration:
```bash
sudo systemctl restart chapel-bells
```

### Web Admin Interface

Access at: `http://<pi-ip>:5000`

Features:
- Dashboard with system status
- Add/remove/edit events
- Configure quiet hours
- Test audio playback
- View playback history

### Quiet Hours

Prevent bell ringing during sleeping hours:

```yaml
quiet_hours:
  enabled: true
  start: "21:00"  # 9 PM
  end: "07:00"    # 7 AM
  override_dates:
    - "2024-12-25"  # Christmas - ring anyway
```

## Troubleshooting

### Audio Not Playing

```bash
# Check audio devices
aplay -l

# Test playback
aplay -D default /var/lib/chapel_bells/audio/westminster/bell.wav

# Check ALSA mixer
alsamixer

# Verify permissions
groups chapel-bells  # Should include 'audio'
```

### Service Not Starting

```bash
# Check service status
sudo systemctl status chapel-bells

# View detailed logs
journalctl -u chapel-bells -n 50 -f

# Check Python 3 location
which python3
```

### Time Not Syncing

```bash
# Check NTP status
timedatectl

# Manually sync (if needed)
sudo systemctl restart systemd-timesyncd
journalctl -u systemd-timesyncd

# Verify timezone
timedatectl list-timezones
sudo timedatectl set-timezone America/New_York
```

### Bell Ringing at Wrong Time

```bash
# Check system time
date

# Verify configuration is loaded
cat /etc/chapel_bells/schedule.yaml

# Check logs for rule matching
journalctl -u chapel-bells | grep "matches"
```

## Maintenance

### Log Rotation

Logs are automatically rotated:
```bash
# View current log
sudo tail -f /var/log/chapel_bells/chapel_bells.log

# Check rotation config
sudo cat /etc/logrotate.d/chapel-bells
```

### Backup Configuration

```bash
# Backup settings
sudo tar czf chapel_bells_backup.tar.gz /etc/chapel_bells

# Restore from backup
sudo tar xzf chapel_bells_backup.tar.gz -C /
sudo systemctl restart chapel-bells
```

### Update ChapelBells

```bash
cd /opt/chapel-bells
sudo git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart chapel-bells
```

## Performance Optimization

### For Raspberry Pi Zero/1

```bash
# Disable unnecessary services
sudo systemctl disable avahi-daemon motion
sudo systemctl stop avahi-daemon motion

# For minimal Pi, use smaller cron interval
# Edit /etc/chapel_bells/schedule.yaml
```

### Memory Usage

```bash
# Monitor resource usage
ps aux | grep chapel-bells
free -h
top -p $(pgrep -f chapel_bells)
```

## Security Considerations

### Network Access

- Web UI accessible only from local network by default
- Change default secret key in systemd service
- Use firewall rules to restrict access:

```bash
sudo ufw allow 5000/tcp from 192.168.1.0/24  # Allow only local subnet
```

### User Permissions

```bash
# Verify chapel-bells user is non-privileged
id chapel-bells

# Check file permissions
ls -la /etc/chapel_bells
```

### Logs & Audit

```bash
# Review recent activities
journalctl -u chapel-bells -S "1 day ago"

# Check failed playbacks
grep "error\|failed" /var/log/chapel_bells/chapel_bells.log
```

## Systemd Service Commands

```bash
# Start/stop
sudo systemctl start chapel-bells
sudo systemctl stop chapel-bells
sudo systemctl restart chapel-bells

# Check status
sudo systemctl status chapel-bells

# View logs
journalctl -u chapel-bells -n 100
journalctl -u chapel-bells -f  # Follow logs

# Enable/disable auto-start
sudo systemctl enable chapel-bells
sudo systemctl disable chapel-bells

# Check auto-start status
sudo systemctl is-enabled chapel-bells
```

## Network Deployment

### SSH Admin Access (Optional)

```bash
# Connect to Pi remotely
ssh chapel-bells@<pi-ip>

# Forward web UI port
ssh -L 5000:localhost:5000 pi@<pi-ip>
# Then access: http://localhost:5000
```

### Web UI Access from Another Computer

```bash
# On Pi: ensure service is running
sudo systemctl status chapel-bells-web

# From computer:
# http://<pi-ip-address>:5000
```

## Testing

### Test Bell Playback

```bash
# Manual test
python3 -c "
from chapel_bells.audio import AudioEngine, AudioConfig
engine = AudioEngine('/var/lib/chapel_bells/audio')
engine.play('westminster', 'bell', wait=True)
"

# Via web UI
# Go to Dashboard > Test Audio
```

### Test Schedule Rules

```bash
# Check if events match current time
python3 -c "
from chapel_bells.scheduler import BellScheduler
scheduler = BellScheduler()
scheduler.load_config('/etc/chapel_bells/schedule.yaml')
events = scheduler.evaluate_events()
print(f'Matching events: {[e.name for e in events]}')
"
```

## Advanced Configuration

### Custom Audio Profiles

Create new audio profile:

```bash
mkdir /var/lib/chapel_bells/audio/my_custom_profile
# Add *.wav files
```

Update schedule.yaml:
```yaml
events:
  - name: "Custom Bell"
    profile: "my_custom_profile"
    tone: "your_audio_file"  # .wav extension omitted
```

### Multiple Schedules

Create separate config files:
```bash
cp config/schedule.yaml /etc/chapel_bells/schedule_weekday.yaml
cp config/schedule.yaml /etc/chapel_bells/schedule_weekend.yaml
```

Load via environment variable:
```bash
CHAPEL_BELLS_CONFIG=/etc/chapel_bells/schedule_weekday.yaml systemctl restart chapel-bells
```

## Support & Debugging

### Enable Debug Logging

Edit systemd service:
```bash
sudo systemctl edit chapel-bells

# Add:
Environment="PYTHON_LOG_LEVEL=DEBUG"
```

Restart and check logs:
```bash
sudo systemctl restart chapel-bells
journalctl -u chapel-bells -f
```

### Report Issues

Collect diagnostic info:
```bash
# System info
uname -a
python3 --version

# Service logs
journalctl -u chapel-bells -n 200 > logs.txt

# Audio devices
aplay -l

# Configuration
cat /etc/chapel_bells/schedule.yaml
```

## Uninstallation

```bash
# Stop service
sudo systemctl stop chapel-bells chapel-bells-web

# Remove systemd files
sudo rm /etc/systemd/system/chapel-bells*.service /etc/systemd/system/chapel-bells*.socket
sudo systemctl daemon-reload

# Remove application files
sudo rm -rf /opt/chapel-bells

# Remove configuration & data
sudo rm -rf /etc/chapel_bells /var/lib/chapel_bells

# Remove user
sudo userdel chapel-bells

# Remove logs
sudo rm -rf /var/log/chapel_bells
```

---

For additional support, check logs or visit the project repository.
