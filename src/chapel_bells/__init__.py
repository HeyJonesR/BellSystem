"""ChapelBells - Automated church bell system."""

__version__ = "1.0.0"
__author__ = "ChapelBells Contributors"
__license__ = "MIT"

from chapel_bells.scheduler import BellScheduler
from chapel_bells.audio import AudioPlayer

__all__ = ["BellScheduler", "AudioPlayer"]
