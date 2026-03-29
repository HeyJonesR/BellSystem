# ChapelBells - Automated Church Bell System

A production-ready, modern automated church bell system for Linux/Raspberry Pi deployment. Built with Python, featuring intelligent scheduling, DST awareness, web administration, and hardware integration for GPIO button control and external triggering.

## Features

- **🔔 Intelligent Scheduling** - Natural language and cron-based event rules with DST support
- **🌅 Sunrise/Sunset Awareness** - Automatic quiet hours based on astronomical calculations
- **🔊 Multi-Backend Audio** - ALSA, PulseAudio, and FFplay support with graceful fallback
- **🌐 Web Admin UI** - Flask-based dashboard and REST API for remote management
- **🖲️ Hardware Integration** - GPIO button input and relay control for Raspberry Pi
- **📡 External Triggers** - FIFO interface for shell scripts and external systems
- **📊 Event History** - Logging and playback tracking
- **🔒 Secure Systemd Services** - Hardened service definitions with auto-restart

## Quick Start

For a 5-minute setup, see [QUICKSTART.md](./QUICKSTART.md)

For complete installation and deployment details, see [docs/INSTALLATION.md](./docs/INSTALLATION.md)

### Basic Installation

```bash
# Clone and setup
git clone https://github.com/HeyJonesR/BellSystem.git
cd BellSystem

# Install dependencies (requires Python 3.9+)
pip install -r requirements.txt

# Copy and configure
cp config/schedule.yaml config/schedule.yaml.local
# Edit config/schedule.yaml.local with your location and events

# Run
python -m chapel_bells
```

### Using Docker

```bash
docker build -t chapel-bells .
docker run -d --name chapel-bells \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/audio_samples:/app/audio_samples \
  chapel-bells
```

## Hardware Integration (Optional)

### GPIO Control

Connect buttons and relays to Raspberry Pi GPIO pins for physical control:

```bash
# Hardware requirements
- Raspberry Pi (any model)
- Push buttons for manual bell triggers
- Relays for high-power bell strikers
- Status LEDs for visual feedback

# Install GPIO support
pip install RPi.GPIO

# Configure pins in src/chapel_bells/gpio.py or create a GPIO config file
```

### FIFO External Triggers

Trigger bells from shell scripts or external systems:

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

## Configuration

### Schedule Format

Define bell events in `config/schedule.yaml`:

```yaml
location:
  name: My Church
  latitude: 40.7128
  longitude: -74.0060
  timezone: America/New_York

events:
  - name: "Sunday Service"
    rule: "sunday at 10:00"
    audio_profile: "church_bells"
    duration_seconds: 60
    
  - name: "Hourly Chimes"
    rule: "every hour"
    audio_profile: "chimes"
    duration_seconds: 15
    quiet_hours: true

audio_profiles:
  church_bells:
    type: sequence
    duration: 60

quiet_hours:
  start_time: "22:00"
  end_time: "06:00"
  override_dates:
    - "2024-12-24"
```

See [config/schedule.yaml](./config/schedule.yaml) for a complete example.

## System Architecture

The system consists of:

1. **Scheduler Engine** - Evaluates rules at 100ms intervals, thread-safe
2. **Audio Engine** - Multi-backend playback with profile management
3. **Astronomical Calculator** - Sunrise/sunset with DST support
4. **Web UI** - Flask dashboard and REST API
5. **GPIO Controller** - Raspberry Pi hardware interface (optional)
6. **FIFO Interface** - Named pipe for external event triggers (optional)
7. **systemd Services** - Service management and auto-restart

For detailed architecture, see [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

## API Endpoints

The web UI provides REST API endpoints for programmatic access:

```
GET  /api/status              - System status
GET  /api/events              - List all events
POST /api/events              - Create new event
GET  /api/events/<id>         - Get event details
PUT  /api/events/<id>         - Update event
DELETE /api/events/<id>       - Delete event
POST /api/test-audio          - Test audio playback
GET  /api/history             - Playback history
```

For complete API reference, see [docs/API.md](./docs/API.md)

## Deployment on Raspberry Pi

```bash
# Copy systemd service files
sudo cp systemd/chapel-bells.service /etc/systemd/system/
sudo cp systemd/chapel-bells-web.service /etc/systemd/system/
sudo cp systemd/chapel-bells-web.socket /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable chapel-bells
sudo systemctl enable chapel-bells-web.socket
sudo systemctl start chapel-bells
sudo systemctl start chapel-bells-web

# Check status
sudo systemctl status chapel-bells
```

## Development

### Running Tests

```bash
python -m pytest tests/test_chapel_bells.py -v
```

### Project Structure

```
ChurchBell/
├── docs/
│   ├── ARCHITECTURE.md       # System design
│   ├── INSTALLATION.md       # Deployment guide
│   ├── API.md               # REST API reference
│   ├── OPTIMIZATIONS.md     # Performance tuning guide
│   └── UI_WIREFRAME.md      # Web UI specs
├── src/chapel_bells/        # Main application
│   ├── scheduler.py         # Scheduling engine
│   ├── audio.py             # Audio playback
│   ├── astro.py             # Astronomy calculations
│   ├── gpio.py              # GPIO hardware control
│   ├── fifo.py              # FIFO event interface
│   └── web/app.py           # Flask web UI
├── config/                  # Configuration examples
├── systemd/                 # Service definitions
├── tests/                   # Test suite
└── audio_samples/           # WAV/FLAC bell sounds
```

## Documentation

- **[docs/INSTALLATION.md](./docs/INSTALLATION.md)** - Complete installation and deployment guide
- **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - System design and architecture
- **[docs/API.md](./docs/API.md)** - REST API reference
- **[docs/OPTIMIZATIONS.md](./docs/OPTIMIZATIONS.md)** - Performance tuning and best practices
- **[QUICKSTART.md](./QUICKSTART.md)** - 5-minute setup guide
- **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** - Project status and deliverables

## Requirements

- **Python:** 3.9 or later
- **OS:** Linux (Ubuntu, Debian, Raspberry Pi OS recommended)
- **Audio:** ALSA or PulseAudio
- **Optional:** RPi.GPIO (for Raspberry Pi GPIO support)

## Installation

```bash
# Install system dependencies
sudo apt-get install -y python3.9 python3-pip alsa-utils

# Clone repository
git clone https://github.com/HeyJonesR/BellSystem.git
cd BellSystem

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install RPi.GPIO for Raspberry Pi
pip install RPi.GPIO
```

## Security Considerations

- The systemd service runs with minimal privileges
- No new privileges flag prevents privilege escalation
- Service is sandboxed with memory and CPU limits
- Web UI includes basic authentication framework
- FIFO interface should be protected with proper file permissions

For security hardening, see [docs/INSTALLATION.md#Security](./docs/INSTALLATION.md)

## Troubleshooting

### Audio not playing?
- Check ALSA settings: `alsamixer`
- Verify audio device: `aplay -l`
- Check logs: `sudo journalctl -u chapel-bells -f`

### Bells not triggering?
- Verify schedule configuration syntax
- Check timezone settings: `timedatectl`
- Review NTP sync: `ntpstat` or `timedatectl show`
- Check logs for rule evaluation errors

### GPIO not working?
- Verify RPi.GPIO installation: `pip list | grep RPi`
- Check GPIO pin configuration in config
- Verify sudo/permissions for GPIO access

See [docs/INSTALLATION.md#Troubleshooting](./docs/INSTALLATION.md) for more help.

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add or update tests
5. Submit a pull request

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review test cases for usage examples

---

**Built with ❤️ by [HeyJonesR](https://github.com/HeyJonesR)**
