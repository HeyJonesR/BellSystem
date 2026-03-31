"""
Audio playback for bell sounds using pygame.mixer.
Supports .wav and .mp3 files with volume control.
Optimised for Ubuntu 24.04 LTS: tries PipeWire → PulseAudio → ALSA in order.
"""

import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pygame
    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False
    logger.warning("pygame not installed – audio disabled")


class AudioPlayer:
    """
    Play bell sound files via pygame.mixer.

    Initialises the mixer on construction (not at import time).
    Caches loaded Sound objects to avoid repeated disk reads on each ring.
    On Ubuntu 24.04 tries PipeWire → PulseAudio → ALSA in order.
    """

    # Ubuntu 24.04: PipeWire → PulseAudio → ALSA
    # macOS: coreaudio
    _DRIVER_PREFERENCE = ("pipewire", "pulseaudio", "alsa", "coreaudio")

    def __init__(self, audio_dir: str, volume: int = 80):
        self.audio_dir = Path(audio_dir)
        self._volume: float = max(0, min(100, volume)) / 100.0
        self._sound_cache: dict = {}
        self._pygame_ok = False
        if _PYGAME_AVAILABLE:
            self._init_mixer()

    def _init_mixer(self) -> None:
        """Initialise pygame.mixer, trying audio drivers in preference order."""
        user_driver = os.environ.get("SDL_AUDIODRIVER")
        drivers = [user_driver] if user_driver else list(self._DRIVER_PREFERENCE)
        for driver in drivers:
            os.environ["SDL_AUDIODRIVER"] = driver
            try:
                # 512-sample buffer → ~12 ms latency at 44.1 kHz,
                # within PipeWire's default quantum (1024 samples).
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
                self._pygame_ok = True
                logger.info("Audio initialised via %s (pygame %s)", driver, pygame.version.ver)
                return
            except Exception as exc:
                logger.debug("Audio driver %s unavailable: %s", driver, exc)
                try:
                    pygame.mixer.quit()
                except Exception:
                    pass
        logger.warning("All audio drivers failed – audio disabled")

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
        if not self._pygame_ok:
            logger.warning("Audio not available, skipping %s", filename)
            return False

        path = self.audio_dir / filename
        if not path.exists():
            logger.error("Audio file not found: %s", path)
            return False

        try:
            key = str(path.resolve())
            sound = self._sound_cache.get(key)
            if sound is None:
                sound = pygame.mixer.Sound(key)
                self._sound_cache[key] = sound
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
        if self._pygame_ok:
            try:
                pygame.mixer.stop()
            except Exception:
                pass

    def close(self) -> None:
        """Release pygame mixer resources cleanly."""
        if self._pygame_ok:
            try:
                pygame.mixer.quit()
                self._pygame_ok = False
                logger.info("Audio mixer closed")
            except Exception:
                pass
