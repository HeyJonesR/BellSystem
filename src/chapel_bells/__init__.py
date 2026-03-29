"""
ChapelBells - Modern Automated Church Bell System

A lightweight, reliable system for managing church bells on Linux/Raspberry Pi.
Features include:
- Flexible scheduling (hourly, daily, weekly, monthly)
- Automatic DST handling
- Quiet hours management
- Web-based administration
- Multiple audio profiles
- Speaker output with configurable volume
"""

__version__ = "1.0.0"
__author__ = "ChapelBells Contributors"
__license__ = "MIT"

from chapel_bells.__main__ import ChapelBells
from chapel_bells.scheduler import BellScheduler, BellEvent, QuietHours
from chapel_bells.audio import AudioEngine, AudioConfig

__all__ = [
    "ChapelBells",
    "BellScheduler",
    "BellEvent",
    "QuietHours",
    "AudioEngine",
    "AudioConfig"
]
