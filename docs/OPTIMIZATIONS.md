# ChapelBells vs bell-controller: Analysis & Optimization Recommendations

## Overview

The **Rocco83/bell-controller** is a simpler, GPIO-focused bell controller (~10 years old, Python 2→3.9). Our **ChapelBells** is more feature-rich with web UI, scheduling, and astronomy. Here's a detailed comparison.

---

## Side-by-Side Comparison

| Feature | bell-controller | ChapelBells | Winner |
|---------|---|---|---|
| **Scheduling** | Cron-based (hardcoded) | Flexible rules + cron | ✅ ChapelBells |
| **Web Admin UI** | None (TODO) | Full Flask dashboard | ✅ ChapelBells |
| **Configuration** | Hardcoded pins/files | JSON/YAML + database | ✅ ChapelBells |
| **Audio Formats** | WAV files | WAV/FLAC + profiles | ✅ ChapelBells |
| **DST Handling** | Manual | Automatic (system time) | ✅ ChapelBells |
| **Quiet Hours** | No | Yes, configurable | ✅ ChapelBells |
| **Sunrise/Sunset** | No | Yes, astronomical calc | ✅ ChapelBells |
| **GPIO Control** | Yes, built-in | Framework only (stub) | ✅ bell-controller |
| **FIFO Interface** | Yes (`/var/run/bell.fifo`) | No | ✅ bell-controller |
| **API** | No | REST (15+ endpoints) | ✅ ChapelBells |
| **Event Logging** | No | Database + journalctl | ✅ ChapelBells |
| **Security (non-root)** | No (runs as root) | Yes (systemd user) | ✅ ChapelBells |
| **Codebase Size** | ~200 lines | ~2500 lines | ✅ bell-controller (simple) |
| **Dependencies** | Minimal | Flask, PyYAML | ✅ bell-controller (lean) |

---

## Key Optimizations to Adopt from bell-controller

### 1. **FIFO Interface for External Control** ⭐ RECOMMENDED
**Why:** Allows external processes (cron jobs, other apps) to trigger bells without API calls.

**Current:** Not implemented
**Their approach:**
```bash
echo "filename" > /var/run/bell.fifo
```

**Add to ChapelBells:**
```python
# src/chapel_bells/fifo.py
import os
import threading

class FIFOInterface:
    """Allow external programs to trigger bells via FIFO."""
    
    def __init__(self, scheduler, fifo_path="/var/run/chapel_bells.fifo"):
        self.scheduler = scheduler
        self.fifo_path = fifo_path
        self.running = False
    
    def start(self):
        """Start listening on FIFO."""
        if not os.path.exists(self.fifo_path):
            os.mkfifo(self.fifo_path)
            os.chmod(self.fifo_path, 0o666)
        
        thread = threading.Thread(target=self._listen, daemon=True)
        thread.start()
    
    def _listen(self):
        """Listen for commands on FIFO."""
        while self.running:
            try:
                with open(self.fifo_path, 'r') as fifo:
                    for line in fifo:
                        event_name = line.strip()
                        # Trigger event by name
                        event = self.scheduler.find_event_by_name(event_name)
                        if event:
                            self.scheduler.trigger_event(event)
            except Exception as e:
                logger.error(f"FIFO error: {e}")
```

Usage:
```bash
echo "Sunday Service" > /var/run/chapel_bells.fifo
```

---

### 2. **GPIO Integration (Complete Implementation)** ⭐ RECOMMENDED
**Why:** Direct hardware control for buttons/relays (they do this well).

**Current:** We have framework but no actual GPIO code

**Add actual GPIO support:**
```python
# src/chapel_bells/gpio.py
import RPi.GPIO as GPIO
import threading
from datetime import datetime

class GPIOController:
    """Manage GPIO pins for buttons and relays."""
    
    def __init__(self, scheduler, config: dict = None):
        self.scheduler = scheduler
        self.config = config or {}
        self.running = False
        self.pin_map = self._load_pin_config()
    
    def _load_pin_config(self):
        """Load pin configuration from config file."""
        return {
            'FESTA': {'pin': 17, 'event': 'Play FESTA'},
            'FUNERALE': {'pin': 27, 'event': 'Play FUNERALE'},
            'ORA_PIA': {'pin': 22, 'event': 'Play ORA_PIA'},
            'STOP': {'pin': 13, 'type': 'button'},
            'SHUTDOWN': {'pin': 19, 'type': 'button'},
        }
    
    def start(self):
        """Initialize GPIO and start listening."""
        GPIO.setmode(GPIO.BCM)
        
        for pin_name, config in self.pin_map.items():
            pin = config['pin']
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(
                pin, 
                GPIO.FALLING,
                callback=lambda ch, name=pin_name: self._on_button_press(name),
                bouncetime=200
            )
        
        logger.info(f"GPIO initialized: {len(self.pin_map)} pins")
    
    def _on_button_press(self, button_name):
        """Handle button press."""
        logger.info(f"Button pressed: {button_name}")
        
        if button_name == 'STOP':
            self.scheduler.audio_engine.stop_playback()
        elif button_name == 'SHUTDOWN':
            logger.info("Shutdown button pressed")
            self.scheduler.running = False
        else:
            # Trigger associated event
            event_name = self.pin_map[button_name].get('event')
            if event_name:
                event = self.scheduler.find_event_by_name(event_name)
                if event:
                    self.scheduler.trigger_event(event)
    
    def cleanup(self):
        """Cleanup GPIO on shutdown."""
        GPIO.cleanup()
```

---

### 3. **Simplify Cron Parsing** (OPTIONAL)
**Current:** We support both natural language AND cron

**Option:** Make cron the primary interface (simpler, more familiar)

```python
# Simplified scheduler using APScheduler instead of custom loop
from apscheduler.schedulers.background import BackgroundScheduler

class SimplifiedScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
    
    def add_cron_job(self, event: BellEvent):
        """Add job using cron-like syntax."""
        # Parse rule: "0 12 * * *" → noon daily
        self.scheduler.add_job(
            self.trigger_event,
            trigger="cron",
            **self._parse_cron(event.rule),
            args=[event]
        )
```

**Pros:** Reusable library (APScheduler), less code to maintain
**Cons:** Extra dependency, less control

---

### 4. **Status LED Indicator** (NICE-TO-HAVE)
**Why:** Visual feedback that system is running

```python
class StatusLED:
    def __init__(self, pin=4):
        self.pin = pin
        GPIO.setup(pin, GPIO.OUT)
    
    def blink(self, count=1):
        """Blink LED to indicate activity."""
        for _ in range(count):
            GPIO.output(self.pin, True)
            time.sleep(0.1)
            GPIO.output(self.pin, False)
            time.sleep(0.1)
    
    def on(self):
        GPIO.output(self.pin, True)
    
    def off(self):
        GPIO.output(self.pin, False)
```

---

### 5. **Lean Dependencies** (CONSIDERATION)
Their project:
- `python3`
- `python3-rpi.gpio`
- `python3-pygame`

Our project:
- Flask, PyYAML, PyEphem, pytest, etc.

**Trade-off:** We're more feature-rich but heavier. For a Pi Zero, this matters.

**Option:** Make Flask/web UI optional:
```python
# In __main__.py
if not HAS_FLASK:
    logger.warning("Flask not installed - web UI disabled")
    # Continue with CLI-only scheduler
```

---

## Recommended Implementation Priority

### 🔴 **Critical** (Do First)
1. **GPIO Integration** - Direct hardware compatibility
2. **FIFO Interface** - External trigger capability
3. Add `find_event_by_name()` method to scheduler

### 🟡 **Important** (Nice to Have)
4. Status LED support
5. Optional Flask (for Pi Zero support)
6. Privilege separation improvements

### 🟢 **Optional** (Future)
7. APScheduler migration
8. Simplified cron-only mode
9. Direct button/relay configuration in JSON

---

## Code Changes Needed

Add to `requirements.txt`:
```txt
RPi.GPIO==0.7.0  # For Raspberry Pi GPIO
apscheduler==3.10.1  # Optional: simpler scheduling
```

Add to `src/chapel_bells/scheduler.py`:
```python
def find_event_by_name(self, name: str) -> Optional[BellEvent]:
    """Find event by name."""
    events = self.get_events()
    return next((e for e in events if e.name.lower() == name.lower()), None)
```

---

## Summary

| Component | ChapelBells Strength | bell-controller Lesson |
|-----------|---|---|
| **Architecture** | Modern, distributed | Simple works |
| **Features** | Rich, configurable | Less is more |
| **Extensibility** | APIs, plugins | Direct control (GPIO) |
| **User Experience** | Web UI | Hardware integration |
| **Maintenance** | Documented | Minimal deps |

**Verdict:** ChapelBells is superior for modern deployments. Adopt GPIO + FIFO from bell-controller for hardware integration.

---

## Next Steps

1. ✅ Keep ChapelBells architecture (better)
2. 🔧 Add GPIO module (from bell-controller pattern)
3. 🔧 Add FIFO interface (from bell-controller pattern)
4. ✅ Keep web UI (better than nothing)
5. 📋 Document hardware integration

**Estimated effort:** 2-3 hours for core GPIO + FIFO implementation.
