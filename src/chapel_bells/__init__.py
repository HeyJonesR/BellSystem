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
"""

__version__ = "1.0.0"
__author__ = "ChapelBells Contributors"
__license__ = "MIT"

from chapel_bells.__main__ import ChapelBells

__all__ = ["ChapelBells"]
