"""
Main ChapelBells application.
Orchestrates scheduler, audio engine, and web UI.
"""

import logging
import logging.handlers
import signal
import sys
import time
from pathlib import Path
from typing import Optional
import threading
from datetime import datetime

from chapel_bells.scheduler import BellScheduler, BellEvent, QuietHours
from chapel_bells.audio import AudioEngine, AudioConfig

# Configure logging
def setup_logging(log_dir: Path = None, log_level: int = logging.INFO):
    """Configure logging to file and console."""
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "chapel_bells.log"
    else:
        log_file = None
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log_dir specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


logger = logging.getLogger(__name__)


class ChapelBells:
    """
    Main application controller.
    
    Manages:
    - Event scheduling
    - Audio playback
    - Background scheduler thread
    """
    
    def __init__(self, config_dir: str = None, audio_dir: str = None):
        """
        Initialize ChapelBells.
        
        Args:
            config_dir: Directory for config/database files
            audio_dir: Directory containing audio samples
        """
        self.config_dir = Path(config_dir or "/etc/chapel_bells")
        self.audio_dir = Path(audio_dir or "/var/lib/chapel_bells/audio")
        self.data_dir = self.config_dir / "data"
        
        # Create directories if needed
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        logger.info("Initializing ChapelBells components...")
        
        # Scheduler
        db_path = str(self.data_dir / "chapel_bells.db")
        config_file = self.config_dir / "schedule.yaml"
        self.scheduler = BellScheduler(
            db_path=db_path,
            config_file=str(config_file) if config_file.exists() else None
        )
        
        # Audio engine
        audio_config = AudioConfig(
            backend="alsa",  # Try ALSA first, falls back to others
            volume=80
        )
        self.audio_engine = AudioEngine(str(self.audio_dir), audio_config)
        
        # Register audio callback
        self.scheduler.register_callback(self._on_bell_event)
        
        # Control flags
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.last_triggered_minute = -1  # Prevent duplicate triggers
    
    def _on_bell_event(self, event: BellEvent):
        """Callback when bell should ring."""
        try:
            logger.info(f"Playing bell: {event.name} ({event.profile}/{event.tone})")
            self.audio_engine.play(event.profile, event.tone, wait=False)
        except Exception as e:
            logger.error(f"Error playing bell: {e}")
    
    def _scheduler_loop(self):
        """Main scheduler loop (runs in background thread)."""
        logger.info("Starting scheduler loop...")
        
        while self.running:
            try:
                now = datetime.now()
                
                # Only evaluate events at the start of each minute
                # to prevent duplicate triggers
                if now.second == 0 and now.minute != self.last_triggered_minute:
                    self.last_triggered_minute = now.minute
                    
                    # Find matching events
                    events = self.scheduler.evaluate_events(now)
                    
                    # Trigger each matching event
                    for event in events:
                        self.scheduler.trigger_event(event)
                
                # Sleep 100ms to avoid busy waiting
                time.sleep(0.1)
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                time.sleep(1)  # Brief sleep on error
    
    def start(self):
        """Start the ChapelBells system."""
        if self.running:
            logger.warning("ChapelBells already running")
            return
        
        logger.info("Starting ChapelBells...")
        self.running = True
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=False
        )
        self.scheduler_thread.start()
        
        logger.info("ChapelBells started successfully")
    
    def stop(self):
        """Stop the ChapelBells system gracefully."""
        if not self.running:
            logger.warning("ChapelBells not running")
            return
        
        logger.info("Stopping ChapelBells...")
        self.running = False
        
        # Stop audio playback
        self.audio_engine.stop_playback()
        
        # Wait for scheduler thread
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("ChapelBells stopped")
    
    def add_event(self, name: str, rule: str, profile: str = "westminster",
                  tone: str = "bell"):
        """Convenience method to add event."""
        event = BellEvent(
            name=name,
            rule=rule,
            profile=profile,
            tone=tone
        )
        self.scheduler.add_event(event)
    
    def get_status(self) -> dict:
        """Get system status."""
        return {
            "running": self.running,
            "current_time": datetime.now().isoformat(),
            "quiet_hours_enabled": self.scheduler.quiet_hours.enabled,
            "quiet_hours": {
                "start": self.scheduler.quiet_hours.start,
                "end": self.scheduler.quiet_hours.end
            },
            "audio_profiles": self.audio_engine.get_available_profiles(),
            "scheduled_events": len(self.scheduler.get_events())
        }
    
    def run_foreground(self):
        """Run in foreground with graceful shutdown handling."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the system
        self.start()
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            self.stop()


# Example usage and entry point
if __name__ == "__main__":
    # Setup logging
    setup_logging()
    
    # Create application
    app = ChapelBells(
        config_dir="/etc/chapel_bells",
        audio_dir="/var/lib/chapel_bells/audio"
    )
    
    # Add some example events
    app.add_event("Hourly Chimes", "every hour", "westminster", "bell")
    app.add_event("Call to Service", "sunday at 10:00", "carillon", "bell")
    
    # Run in foreground
    app.run_foreground()
