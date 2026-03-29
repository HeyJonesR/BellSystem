"""
GPIO interface for Raspberry Pi hardware control.
Integrates physical buttons, relays, and status LEDs.

Note: Only works on Raspberry Pi with RPi.GPIO installed.
Gracefully degrades on non-Pi systems.
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)

# Try to import GPIO library (only available on Raspberry Pi)
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    logger.warning("RPi.GPIO not available - GPIO features disabled")


class GPIOConfig:
    """GPIO pin configuration."""
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            "mode": "BCM",  # BCM or BOARD
            "buttons": {
                "FESTA": {"pin": 17, "event": "Play FESTA"},
                "FUNERALE": {"pin": 27, "event": "Play FUNERALE"},
                "ORA_PIA": {"pin": 22, "event": "Play ORA_PIA"},
                "STOP": {"pin": 13, "function": "stop"},
                "SHUTDOWN": {"pin": 19, "function": "shutdown"},
            },
            "relays": {
                "AMPLIFIER": {"pin": 26, "active_high": True},
                "EXTERIOR_BELL": {"pin": 16, "active_high": False},
            },
            "leds": {
                "STATUS": {"pin": 4, "blink_on_trigger": True},
            }
        }
    
    def get_button_pins(self) -> Dict:
        """Get button pin mappings."""
        return {
            name: config["pin"]
            for name, config in self.config.get("buttons", {}).items()
        }


class GPIOController:
    """
    Manage Raspberry Pi GPIO for buttons, relays, and LEDs.
    
    Allows physical hardware (buttons) to trigger bells and control system.
    """
    
    def __init__(self, scheduler, config: GPIOConfig = None):
        """
        Initialize GPIO controller.
        
        Args:
            scheduler: BellScheduler instance
            config: GPIOConfig object
        """
        if not HAS_GPIO:
            logger.warning("GPIO not available - hardware control disabled")
            self.available = False
            return
        
        self.available = True
        self.scheduler = scheduler
        self.config = config or GPIOConfig()
        self.running = False
        self._setup_done = False
    
    def start(self):
        """Initialize GPIO and start listening for button presses."""
        if not self.available or self._setup_done:
            return
        
        try:
            # Set GPIO mode
            mode = self.config.config["mode"]
            if mode == "BCM":
                GPIO.setmode(GPIO.BCM)
            else:
                GPIO.setmode(GPIO.BOARD)
            
            # Setup button inputs
            buttons = self.config.config.get("buttons", {})
            for button_name, button_config in buttons.items():
                pin = button_config["pin"]
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
                # Add event detection (falling edge = button pressed)
                GPIO.add_event_detect(
                    pin,
                    GPIO.FALLING,
                    callback=lambda ch, name=button_name: self._on_button_press(name),
                    bouncetime=200  # Debounce 200ms
                )
                logger.info(f"Button '{button_name}' configured on pin {pin}")
            
            # Setup relay outputs
            relays = self.config.config.get("relays", {})
            for relay_name, relay_config in relays.items():
                pin = relay_config["pin"]
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
                logger.info(f"Relay '{relay_name}' configured on pin {pin}")
            
            # Setup status LED
            leds = self.config.config.get("leds", {})
            for led_name, led_config in leds.items():
                pin = led_config["pin"]
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
                logger.info(f"LED '{led_name}' configured on pin {pin}")
            
            self.running = True
            self._setup_done = True
            logger.info("GPIO controller started successfully")
        
        except Exception as e:
            logger.error(f"Failed to setup GPIO: {e}")
            self.available = False
    
    def _on_button_press(self, button_name: str):
        """
        Handle button press event.
        
        Args:
            button_name: Name of button that was pressed
        """
        logger.info(f"Button pressed: {button_name}")
        
        buttons = self.config.config.get("buttons", {})
        button_config = buttons.get(button_name, {})
        
        # Blink status LED
        self._blink_led("STATUS", 1)
        
        # Handle button functions or trigger events
        if "function" in button_config:
            function = button_config["function"]
            
            if function == "stop":
                logger.info("Stop button - halting playback")
                self.scheduler.audio_engine.stop_playback()
            
            elif function == "shutdown":
                logger.info("Shutdown button - stopping service")
                self.scheduler.running = False
        
        elif "event" in button_config:
            # Trigger associated event
            event_name = button_config["event"]
            event = self.scheduler.find_event_by_name(event_name)
            
            if event:
                logger.info(f"Triggering event: {event_name}")
                self.scheduler.trigger_event(event)
            else:
                logger.warning(f"Event not found: {event_name}")
    
    def _blink_led(self, led_name: str, count: int = 1, duration: float = 0.1):
        """
        Blink an LED to indicate activity.
        
        Args:
            led_name: Name of LED to blink
            count: Number of blinks
            duration: Duration of each blink in seconds
        """
        if not self.available:
            return
        
        leds = self.config.config.get("leds", {})
        led_config = leds.get(led_name)
        
        if not led_config:
            return
        
        pin = led_config["pin"]
        
        try:
            for _ in range(count):
                GPIO.output(pin, GPIO.HIGH)
                time.sleep(duration)
                GPIO.output(pin, GPIO.LOW)
                time.sleep(duration)
        except Exception as e:
            logger.warning(f"Error blinking LED: {e}")
    
    def set_relay(self, relay_name: str, state: bool):
        """
        Control a relay output.
        
        Args:
            relay_name: Name of relay
            state: True to activate, False to deactivate
        """
        if not self.available:
            return
        
        relays = self.config.config.get("relays", {})
        relay_config = relays.get(relay_name)
        
        if not relay_config:
            logger.warning(f"Relay not found: {relay_name}")
            return
        
        pin = relay_config["pin"]
        active_high = relay_config.get("active_high", True)
        
        # Invert logic if active_low
        gpio_state = GPIO.HIGH if state else GPIO.LOW
        if not active_high:
            gpio_state = GPIO.LOW if state else GPIO.HIGH
        
        try:
            GPIO.output(pin, gpio_state)
            logger.debug(f"Relay '{relay_name}' set to {state}")
        except Exception as e:
            logger.error(f"Error controlling relay: {e}")
    
    def get_status_led(self) -> Optional[str]:
        """Get name of status LED if configured."""
        leds = self.config.config.get("leds", {})
        if "STATUS" in leds:
            return "STATUS"
        return None
    
    def cleanup(self):
        """Cleanup GPIO on shutdown."""
        if not self.available or not self._setup_done:
            return
        
        try:
            GPIO.cleanup()
            logger.info("GPIO cleanup completed")
        except Exception as e:
            logger.warning(f"Error during GPIO cleanup: {e}")


class LEDIndicator:
    """
    Visual status indicator using LED.
    
    Patterns:
    - Single blink: Bell triggered
    - Double blink: Event started
    - Rapid blink: Error/warning
    - Solid: System running
    """
    
    def __init__(self, gpio_controller: GPIOController):
        self.gpio = gpio_controller
        self.led_name = gpio_controller.get_status_led()
    
    def bell_triggered(self):
        """Indicate bell was triggered."""
        if self.led_name:
            self.gpio._blink_led(self.led_name, count=1, duration=0.1)
    
    def event_started(self):
        """Indicate event started."""
        if self.led_name:
            self.gpio._blink_led(self.led_name, count=2, duration=0.1)
    
    def warning(self):
        """Indicate warning/error."""
        if self.led_name:
            self.gpio._blink_led(self.led_name, count=5, duration=0.05)
