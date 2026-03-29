# ChapelBells Installation & Deployment Guide

## Overview
ChapelBells is a modern, lightweight church bell system designed for Linux/Raspberry Pi. This guide covers setup on Ubuntu Server 22.04 LTS or Raspbian Bullseye+.

## System Requirements

### Hardware
- **Raspberry Pi 4/5** (or x86 Linux machine, Ubuntu Server 20.04+)
- **2GB+ RAM** (4GB+ recommended)
- **100MB disk space** (+ audio samples)
- **Audio jack** or USB audio device
- **Network connectivity** (for NTP time sync)

### Software Prerequisites
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
    alsa-utils pulseaudio git ntp \
    build-essential libopenjp2-7 libtiff5 libjasper1 libharfbuzz0b \
    libwebp6 libtk8.6 libqtgui4 libqt4-test libhogweed4 libgmp10

# For Raspberry Pi audio support
sudo apt install -y libasound2-plugins alsa-ucm-conf
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
sudo git clone https://github.com/your-org/chapel-bells.git
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

# Test audio on Raspberry Pi
speaker-test -c2 -t sine -f 1000

# Check ALSA configuration
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

## GPIO Hardware Integration (Raspberry Pi)

### Optional: Install GPIO Support

For physical button control and relay activation on Raspberry Pi:

```bash
# Install GPIO library
pip install RPi.GPIO

# Verify installation
python3 -c "import RPi.GPIO; print(f'RPi.GPIO {RPi.GPIO.__version__} installed')"
```

### GPIO Wiring Guide

**Physical Button (Manual Trigger)**
```
GPIO 17 (Pin 11) ----[ Button ]---- GND (Pin 9)
                      [ 10kΩ resistor to 3.3V (Pin 1) ]
```

**Relay Control (Bell Striker)**
```
GPIO 22 (Pin 15) ---- [ Transistor/Relay Driver ] ---- Bell Striker Coil
GND (Pin 9) ---- Relay GND
```

**Status LED Indicators**
```
GPIO 23 (Pin 16) ---- [ 470Ω Resistor ] ---- LED Anode ---- GND (Pin 9)
GPIO 24 (Pin 18) ---- [ 470Ω Resistor ] ---- LED Anode ---- GND (Pin 9)
```

### Raspberry Pi GPIO Pinout

```
    ┌─────────────────────┐
  1 │ 3.3V        GND 6   │
  3 │ GPIO2       GPIO27 13│
  5 │ GPIO3       GPIO17  11│
  7 │ GPIO4       GPIO26  37│
  9 │ GND         GPIO20  38│
 10 │ GPIO10      GPIO21  40│
 12 │ GPIO9       GPIO7   26│
 14 │ GND         GPIO8   24│
 16 │ GPIO25      GND 20  │
 17 │ 3.3V        GPIO12  32│
 19 │ GPIO10      GPIO13  33│
 21 │ GPIO22      GND 34  │
 23 │ GPIO27      GPIO17  11│
 25 │ GND         GPIO4    7│
    └─────────────────────┘
```

### Configure GPIO Pins

Edit GPIO configuration in `src/chapel_bells/gpio.py`:

```python
class GPIOConfig:
    # Button inputs
    BUTTON_MANUAL_TRIGGER = 17  # Pin 11
    BUTTON_SYSTEM_RESET = 27    # Pin 13
    
    # Relay outputs
    RELAY_BELL_STRIKER = 22     # Pin 15
    
    # LED status indicators
    LED_STATUS = 23             # Pin 16 - Green status
    LED_ERROR = 24              # Pin 18 - Red error
    
    # Button debounce (milliseconds)
    DEBOUNCE_MS = 200
```

### GPIO Features

**Manual Button Control:**
- Press button to trigger current/next scheduled bell
- Useful for testing and manual operation
- Debouncing prevents accidental double-triggers

**Relay Control:**
- Activate bell striker electromagnet on scheduled events
- Supports audible feedback without audio system
- Thread-safe relay state management

**Status LEDs:**
- Green LED: System running normally
- Red LED: Error or fault condition
- Blinking patterns indicate different states

### Running with GPIO

```bash
# Ensure service user has GPIO permissions
sudo usermod -a -G gpio chapel-bells

# Start service (GPIO modules load automatically)
sudo systemctl start chapel-bells

# Check GPIO initialization
journalctl -u chapel-bells | grep "GPIO\|gpio"
```

## FIFO External Triggers

Enable external systems to trigger bells via shell commands.

### Enable FIFO Interface

The FIFO interface is enabled by default and creates a named pipe at:

```
/var/run/chapel_bells.fifo
```

### Trigger Bells

```bash
# Trigger a bell event by name
echo "Sunday Service" > /var/run/chapel_bells.fifo

# List available events
echo "list" > /var/run/chapel_bells.fifo

# Stop current playback
echo "stop" > /var/run/chapel_bells.fifo

# Get system status
echo "status" > /var/run/chapel_bells.fifo
```

### Cron Integration Example

```bash
# Edit crontab
crontab -e

# Add custom bell triggers
# Ring at 8 AM daily
0 8 * * * echo "Morning Chime" > /var/run/chapel_bells.fifo

# Ring noon on weekdays
0 12 * * 1-5 echo "Noon Bell" > /var/run/chapel_bells.fifo

# Ring special event
0 15 * * 0 echo "Afternoon Service" > /var/run/chapel_bells.fifo
```

### Shell Script Integration

```bash
#!/bin/bash
# trigger_bells.sh - Trigger bells from shell script

FIFO="/var/run/chapel_bells.fifo"

# Check if FIFO exists
if [ ! -p "$FIFO" ]; then
    echo "ERROR: FIFO not found at $FIFO"
    exit 1
fi

# Trigger bell
EVENT_NAME="${1:-Sunday Service}"
echo "$EVENT_NAME" > "$FIFO"

echo "Triggered: $EVENT_NAME"
```

Usage:
```bash
chmod +x trigger_bells.sh
./trigger_bells.sh "Wedding Bell"
```

### Custom Monitoring Integration

Example Python script to monitor and trigger:

```python
import os
import sys

FIFO = "/var/run/chapel_bells.fifo"

def trigger_bell(event_name):
    try:
        with open(FIFO, 'w') as f:
            f.write(event_name + '\n')
        print(f"✓ Triggered: {event_name}")
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    return True

if __name__ == "__main__":
    # Trigger Sunday Service if it's Sunday
    import datetime
    today = datetime.date.today()
    
    if today.weekday() == 6:  # Sunday
        trigger_bell("Sunday Service")
    else:
        trigger_bell("Hourly Chimes")
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

### Astronomical Calculations

Fine-tune sunrise/sunset for quiet hours:

```yaml
location:
  latitude: 40.7128
  longitude: -74.0060
  # System uses these to calculate sunrise/sunset automatically
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
