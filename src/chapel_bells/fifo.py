"""
FIFO (Named Pipe) interface for ChapelBells.

Allows external processes to trigger bell events without needing HTTP API.

Example:
    # From command line
    echo "Sunday Service" > /var/run/chapel_bells.fifo
    
    # From another script
    with open('/var/run/chapel_bells.fifo', 'w') as f:
        f.write('Hourly Chimes\n')
"""

import os
import logging
import threading
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class FIFOInterface:
    """
    Listen on a named pipe (FIFO) for event triggers.
    
    Simpler alternative to HTTP API for local system integration.
    """
    
    def __init__(self, scheduler, fifo_path: str = "/var/run/chapel_bells.fifo"):
        """
        Initialize FIFO interface.
        
        Args:
            scheduler: BellScheduler instance
            fifo_path: Path to FIFO (named pipe)
        """
        self.scheduler = scheduler
        self.fifo_path = fifo_path
        self.running = False
        self._listener_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Create FIFO and start listening for commands."""
        # Create FIFO if it doesn't exist
        if not os.path.exists(self.fifo_path):
            try:
                os.mkfifo(self.fifo_path)
                os.chmod(self.fifo_path, 0o666)
                logger.info(f"Created FIFO at {self.fifo_path}")
            except FileExistsError:
                pass  # Already created
            except PermissionError:
                logger.error(f"Permission denied creating FIFO at {self.fifo_path}")
                logger.info("Try running with sudo or ensure /var/run is writable")
                return
        
        # Start listener thread
        self.running = True
        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=False,
            name="FIFOListener"
        )
        self._listener_thread.start()
        logger.info(f"FIFO interface listening on {self.fifo_path}")
    
    def _listen_loop(self):
        """Main loop: listen for commands on FIFO."""
        while self.running:
            try:
                # Open FIFO for reading (blocking)
                logger.debug(f"Opening FIFO at {self.fifo_path}")
                
                with open(self.fifo_path, 'r') as fifo:
                    for line in fifo:
                        if not self.running:
                            break
                        
                        command = line.strip()
                        if command:
                            self._process_command(command)
            
            except IOError as e:
                if self.running:
                    logger.warning(f"FIFO read error: {e}")
            except Exception as e:
                logger.error(f"Unexpected FIFO error: {e}")
                if self.running:
                    import time
                    time.sleep(1)  # Brief delay before retrying
    
    def _process_command(self, command: str):
        """
        Process a command from FIFO.
        
        Commands:
        - Event name: Trigger that event
        - "list": Print all events
        - "stop": Stop current playback
        - "status": Print system status
        
        Args:
            command: Command string
        """
        logger.info(f"FIFO command: {command}")
        
        # Interpret command
        if command.lower() == "list":
            events = self.scheduler.get_events()
            for event in events:
                print(f"  - {event.name}: {event.rule}")
        
        elif command.lower() == "stop":
            logger.info("FIFO: Stopping playback")
            self.scheduler.audio_engine.stop_playback()
        
        elif command.lower() == "status":
            status = self.scheduler.scheduler_status() if hasattr(self.scheduler, 'scheduler_status') else "Running"
            print(f"ChapelBells: {status}")
        
        else:
            # Assume it's an event name
            event = self.scheduler.find_event_by_name(command)
            if event:
                logger.info(f"FIFO: Triggering event '{event.name}'")
                self.scheduler.trigger_event(event)
            else:
                logger.warning(f"FIFO: Event not found: '{command}'")
                print(f"Error: Event not found: {command}", file=open(os.devnull, 'w'))
    
    def stop(self):
        """Stop listening on FIFO."""
        self.running = False
        
        if self._listener_thread:
            self._listener_thread.join(timeout=2)
        
        # Cleanup FIFO file
        try:
            if os.path.exists(self.fifo_path):
                os.remove(self.fifo_path)
                logger.info(f"Removed FIFO at {self.fifo_path}")
        except Exception as e:
            logger.warning(f"Error removing FIFO: {e}")
    
    def trigger_event(self, event_name: str) -> bool:
        """
        Programmatically trigger an event via FIFO.
        
        Args:
            event_name: Name of event to trigger
        
        Returns:
            True if success, False if FIFO unavailable
        """
        if not os.path.exists(self.fifo_path):
            logger.warning(f"FIFO not available: {self.fifo_path}")
            return False
        
        try:
            with open(self.fifo_path, 'w') as fifo:
                fifo.write(f"{event_name}\n")
            return True
        except Exception as e:
            logger.error(f"Error writing to FIFO: {e}")
            return False


# Example usage/testing
if __name__ == "__main__":
    import sys
    from chapel_bells import ChapelBells
    
    # Create app
    app = ChapelBells()
    
    # Create FIFO interface
    fifo = FIFOInterface(app.scheduler)
    
    # Start listening
    fifo.start()
    
    print("FIFO interface listening. Try:")
    print(f"  echo 'Hourly Chimes' > {fifo.fifo_path}")
    print(f"  echo 'list' > {fifo.fifo_path}")
    print(f"  echo 'stop' > {fifo.fifo_path}")
    print("\nPress Ctrl+C to stop")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        fifo.stop()
