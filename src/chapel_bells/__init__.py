"""
ChapelBells - Modern Automated Church Bell System

A lightweight, reliable system for managing church bells on Linux/Raspberry Pi.
Features include:
- Flexible scheduling (hourly, daily, weekly, monthly)
- Automatic DST handling
- Quiet hours management
- Web-based administration
- Sunrise/sunset calculations
- Multiple audio profiles
- GPIO support (optional, Raspberry Pi)
- FIFO interface for external triggers
"""

__version__ = "1.0.0"
__author__ = "ChapelBells Contributors"
__license__ = "MIT"

from chapel_bells.__main__ import ChapelBells
from chapel_bells.scheduler import BellScheduler, BellEvent, QuietHours
from chapel_bells.audio import AudioEngine, AudioConfig
from chapel_bells.astro import AstronomicalCalculator

# Optional hardware support
try:
    from chapel_bells.gpio import GPIOController, GPIOConfig, LEDIndicator
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False

try:
    from chapel_bells.fifo import FIFOInterface
    HAS_FIFO = True
except ImportError:
    HAS_FIFO = False

__all__ = [
    "ChapelBells",
    "BellScheduler",
    "BellEvent",
    "QuietHours",
    "AudioEngine",
    "AudioConfig",
    "AstronomicalCalculator",
    "GPIOController",
    "GPIOConfig",
    "LEDIndicator",
    "FIFOInterface",
    "HAS_GPIO",
    "HAS_FIFO"
]
