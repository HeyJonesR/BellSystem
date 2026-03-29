# ChapelBells - Quick Start Guide

Get your church bell system running in 15 minutes!

## Prerequisites

- Raspberry Pi 4/5 or Ubuntu Server machine
- Python 3.9+
- Audio output device (speakers/amplifier)
- Bell audio files (optional - will generate test tones)

## 5-Minute Setup

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/your-org/chapel-bells.git
cd chapel-bells

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Config

```bash
# Copy example config
cp config/schedule.yaml ~/.chapel_bells.yaml

# Edit for your location & times
nano ~/.chapel_bells.yaml
```

Edit these key settings:
```yaml
location:
  latitude: 40.7128    # Your church latitude
  longitude: -74.0060  # Your church longitude
  timezone_offset: -5  # UTC offset

quiet_hours:
  start: "21:00"       # Stop ringing at 9 PM
  end: "07:00"         # Start ringing at 7 AM

events:
  - name: "Hourly Chimes"
    rule: "every hour"
    active_after: "07:00"
    active_before: "21:00"
```

### 3. Test Audio

```bash
# Generate test bell sound
sox -n -r 44100 -c 2 -b 16 bell.wav synth 2 sine 440

# Test playback
aplay bell.wav

# Create audio directories
mkdir -p ~/.chapel_bells/audio/westminster
mv bell.wav ~/.chapel_bells/audio/westminster/bell.wav
```

### 4. Run Application

```bash
# Start in foreground (test mode)
python3 -m chapel_bells --config ~/.chapel_bells.yaml

# You should see:
# [INFO] Starting ChapelBells...
# [INFO] Starting scheduler loop...
```

### 5. Access Web UI

Open browser: `http://localhost:5000`

- Dashboard shows next scheduled bells
- Add new events via the web UI
- Configure quiet hours
- Test audio playback

## Common Tasks

### Add a Sunday Service Bell

```bash
# Edit config or use web UI
# In browser:
# 1. Click "Add Event"
# 2. Name: "Sunday Service"
# 3. Rule: "sunday at 10:00"
# 4. Profile: "carillon"
# 5. Click Save
```

### Change Quiet Hours

Via web UI:
1. Dashboard → Settings → Quiet Hours
2. Set start time: 21:00 (9 PM)
3. Set end time: 07:00 (7 AM)
4. Save

### Test Bell Playback

Via web UI:
1. Dashboard → Audio Test
2. Select profile: "westminster"
3. Click "Play"

## Install as System Service

```bash
# Install as systemd service (Linux only)
./scripts/install_service.sh

# Start service
sudo systemctl start chapel-bells

# Check status
sudo systemctl status chapel-bells

# View logs
journalctl -u chapel-bells -f
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
cat ~/.chapel_bells.yaml

# Check for quiet hours
# Look at "Quiet Hours" section in web UI
```

### Web UI Not Accessible
```bash
# Check if service is running
ps aux | grep chapel_bells

# Check port is listening
netstat -tuln | grep 5000

# Try starting manually
python3 -m chapel_bells.web.app
```

## GPIO & Hardware Integration (Raspberry Pi)

### Optional: Add Physical Button Control

```bash
# Install GPIO library
pip install RPi.GPIO

# Wire a button to GPIO pin 17 (with pullup resistor)
# Connect button between GPIO 17 and GND

# Configure in gpio.py or create gpio_config.json:
{
  "button_pins": {
    "manual_trigger": 17,
    "system_reset": 27
  },
  "relay_pins": {
    "bell_striker": 22
  },
  "led_pins": {
    "status": 23,
    "error": 24
  }
}
```

### Optional: FIFO External Triggers

Trigger bells from shell scripts or cron jobs:

```bash
# Trigger a bell event by name
echo "Sunday Service" > /var/run/chapel_bells.fifo

# List all available events
echo "list" > /var/run/chapel_bells.fifo

# Stop current playback
echo "stop" > /var/run/chapel_bells.fifo

# Get system status
echo "status" > /var/run/chapel_bells.fifo

# Example: Cron job to ring at custom time
# Add to crontab (crontab -e):
# 0 14 * * * echo "Afternoon Bells" > /var/run/chapel_bells.fifo
```

## Deploy to Raspberry Pi

### Quick SSH Deploy

```bash
# On your development machine
scp -r BellSystem pi@192.168.1.100:/home/pi/

# Connect to Pi
ssh pi@192.168.1.100

# cd into directory
cd BellSystem

# Install dependencies
pip install -r requirements.txt

# On Raspberry Pi 4+, also install GPIO support
pip install RPi.GPIO

# Create config
cp config/schedule.yaml ~/chapel_bells.yaml
nano ~/chapel_bells.yaml
```

### Install System Service

```bash
# Copy systemd service files
sudo cp systemd/chapel-bells.service /etc/systemd/system/
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
