"""
Audio playback for bell sounds using pygame.mixer.
Supports .wav and .mp3 files with volume control.
"""

import logging
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import pygame
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()
    _PYGAME_OK = True
    logger.info("Audio initialised (pygame %s)", pygame.version.ver)
except Exception as _e:
    _PYGAME_OK = False
    logger.warning("pygame unavailable – audio disabled (%s)", _e)


class AudioPlayer:
    """
    Play bell sound files via pygame.mixer.

    Each call to play() loads the file as a pygame.mixer.Sound so that
    rapid successive rings (bell count patterns) work correctly even if
    the previous sound hasn't finished.
    """

    def __init__(self, audio_dir: str, volume: int = 80):
        self.audio_dir = Path(audio_dir)
        self._volume: float = max(0, min(100, volume)) / 100.0

    # ------------------------------------------------------------------
    # Volume
    # ------------------------------------------------------------------

    @property
    def volume(self) -> int:
        return int(self._volume * 100)

    def set_volume(self, volume: int) -> None:
        self._volume = max(0, min(100, volume)) / 100.0
        logger.info("Volume set to %d%%", self.volume)

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def play(self, filename: str, wait: bool = True) -> bool:
        """
        Play an audio file.

        Args:
            filename: Relative path inside audio_dir (e.g. "westminster/bell.wav")
            wait:     Block until the sound finishes (default True, good for
                      counted rings so the next ring doesn't overlap)

        Returns:
            True on success, False on any error.
        """
        if not _PYGAME_OK:
            logger.warning("Audio not available, skipping %s", filename)
            return False

        path = self.audio_dir / filename
        if not path.exists():
            logger.error("Audio file not found: %s", path)
            return False

        try:
            sound = pygame.mixer.Sound(str(path))
            sound.set_volume(self._volume)
            channel = sound.play()
            if wait and channel:
                while channel.get_busy():
                    time.sleep(0.05)
            return True
        except Exception as exc:
            logger.error("Playback error (%s): %s", filename, exc)
            return False

    def stop(self) -> None:
        """Stop all currently playing sounds."""
        if _PYGAME_OK:
            try:
                pygame.mixer.stop()
            except Exception:
                pass
