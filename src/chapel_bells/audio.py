"""
Audio playback engine for bell sounds.
Supports ALSA, PulseAudio, and fallback options.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum
import subprocess
import threading
import time

logger = logging.getLogger(__name__)


class AudioProfile(Enum):
    """Predefined bell sound profiles."""
    WESTMINSTER = "westminster"      # Classic Westminster quarters
    CARILLON = "carillon"            # Full carillon bells
    TRADITIONAL = "traditional"      # Deep, traditional large bell
    LIGHT = "light"                  # Softer, lighter chimes
    CUSTOM = "custom"                # User-provided audio files


@dataclass
class AudioConfig:
    """Audio engine configuration."""
    audio_device: str = "default"     # ALSA device or pulse sink
    volume: int = 80                  # 0-100
    backend: str = "alsa"             # "alsa", "pulse", "ffplay"
    sample_rate: int = 44100          # Hz
    channels: int = 2                 # mono=1, stereo=2


class AudioEngine:
    """
    Handle audio playback of bell sounds.
    
    Gracefully handles missing audio devices or library dependencies.
    """
    
    def __init__(self, audio_dir: str, config: AudioConfig = None):
        """
        Initialize audio engine.
        
        Args:
            audio_dir: Directory containing audio sample files
            config: AudioConfig object (uses defaults if None)
        """
        self.audio_dir = Path(audio_dir)
        self.config = config or AudioConfig()
        self.current_playback: Optional[subprocess.Popen] = None
        self.lock = threading.Lock()
        
        # Cache loaded profiles
        self.profiles: Dict[str, Dict[str, Path]] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """Scan audio_dir for bell profiles."""
        if not self.audio_dir.exists():
            logger.warning(f"Audio directory not found: {self.audio_dir}")
            return
        
        # Scan for subdirectories (profiles)
        for profile_dir in self.audio_dir.iterdir():
            if profile_dir.is_dir():
                profile_name = profile_dir.name
                audio_files = {}
                
                # Find audio files in this profile
                for audio_file in profile_dir.glob("*.wav"):
                    # Filename pattern: tone_1.wav, tone_2.wav, etc.
                    audio_files[audio_file.stem] = audio_file
                
                if audio_files:
                    self.profiles[profile_name] = audio_files
                    logger.info(f"Loaded audio profile: {profile_name} ({len(audio_files)} files)")
    
    def get_available_profiles(self) -> list:
        """Return list of available audio profiles."""
        return list(self.profiles.keys()) + [p.value for p in AudioProfile]
    
    def _get_audio_file(self, profile: str, tone: str = "bell") -> Optional[Path]:
        """Get path to audio file for profile and tone."""
        if profile in self.profiles:
            # Custom loaded profile
            return self.profiles[profile].get(tone)
        
        # Look for default profile in audio_dir
        profile_path = self.audio_dir / profile / f"{tone}.wav"
        if profile_path.exists():
            return profile_path
        
        logger.warning(f"Audio file not found: {profile}/{tone}.wav")
        return None
    
    def _play_with_ffplay(self, audio_file: Path) -> bool:
        """Fallback: play audio using ffplay."""
        try:
            cmd = ["ffplay", "-nodisp", "-autoexit", str(audio_file)]
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except FileNotFoundError:
            logger.error("ffplay not installed")
            return False
    
    def _play_with_alsa(self, audio_file: Path) -> bool:
        """Play audio using aplay (ALSA)."""
        try:
            cmd = ["aplay", "-D", self.config.audio_device, str(audio_file)]
            self.current_playback = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except FileNotFoundError:
            logger.error("aplay not installed")
            return False
    
    def _play_with_pulse(self, audio_file: Path) -> bool:
        """Play audio using paplay (PulseAudio)."""
        try:
            cmd = ["paplay", "-d", self.config.audio_device, str(audio_file)]
            self.current_playback = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except FileNotFoundError:
            logger.error("paplay not installed")
            return False
    
    def play(self, profile: str = "westminster", tone: str = "bell", 
             wait: bool = False) -> bool:
        """
        Play a bell tone.
        
        Args:
            profile: Audio profile name (e.g., "westminster")
            tone: Tone identifier within profile (e.g., "bell", "tone_1")
            wait: If True, block until playback completes
        
        Returns:
            True if playback started successfully
        """
        with self.lock:
            # Find audio file
            audio_file = self._get_audio_file(profile, tone)
            if not audio_file:
                logger.warning(f"No audio file for {profile}/{tone}")
                return False
            
            # Try to play with configured backend
            success = False
            if self.config.backend == "alsa":
                success = self._play_with_alsa(audio_file)
            elif self.config.backend == "pulse":
                success = self._play_with_pulse(audio_file)
            else:
                success = self._play_with_ffplay(audio_file)
            
            if not success and self.config.backend != "ffplay":
                # Fallback to ffplay
                logger.info("Falling back to ffplay")
                success = self._play_with_ffplay(audio_file)
            
            if wait and self.current_playback and success:
                self.current_playback.wait()
            
            return success
    
    def play_sequence(self, profile: str, tones: list, interval: float = 1.0):
        """
        Play a sequence of tones with intervals.
        
        Args:
            profile: Audio profile
            tones: List of tone identifiers
            interval: Delay between tones in seconds
        """
        for i, tone in enumerate(tones):
            if i > 0:
                time.sleep(interval)
            self.play(profile, tone, wait=True)
    
    def set_volume(self, level: int):
        """
        Set volume level (0-100).
        
        Note: This is application-level only; actual system volume
        depends on ALSA/PulseAudio configuration.
        """
        self.config.volume = max(0, min(100, level))
        logger.info(f"Volume set to {self.config.volume}%")
    
    def stop_playback(self):
        """Stop any ongoing playback."""
        with self.lock:
            if self.current_playback:
                try:
                    self.current_playback.terminate()
                    self.current_playback.wait(timeout=2)
                except Exception as e:
                    logger.warning(f"Error stopping playback: {e}")
                    if self.current_playback.poll() is None:
                        self.current_playback.kill()
                finally:
                    self.current_playback = None


class AudioPlaybackSequence:
    """
    Define complex bell sequences (e.g., Westminster quarters).
    """
    
    def __init__(self, name: str, profile: str):
        self.name = name
        self.profile = profile
        self.tones = []
    
    def add_tone(self, tone_id: str, delay_seconds: float = 0):
        """Add a tone to sequence."""
        self.tones.append((tone_id, delay_seconds))
    
    def execute(self, engine: AudioEngine):
        """Play the entire sequence."""
        for tone_id, delay in self.tones:
            if delay > 0:
                time.sleep(delay)
            engine.play(self.profile, tone_id, wait=True)


# Example Westminster Quarters sequence builder
def westminster_quarters(hour: int, engine: AudioEngine) -> AudioPlaybackSequence:
    """
    Generate Westminster quarter sequence for given hour.
    
    Pattern:
    - Quarter 1: 2 strokes of bell
    - Quarter 2: 4 strokes
    - Quarter 3: 6 strokes
    - On the hour: hour strikes
    """
    seq = AudioPlaybackSequence("Westminster", "westminster")
    
    # Simplified: use different tones for different quarters
    quarters = [
        ["bell"] * 2,
        ["bell"] * 4,
        ["bell"] * 6,
    ]
    
    for i, quarter in enumerate(quarters):
        if i > 0:
            seq.add_tone("bell", 2)  # Gap between quarters
        
        for j, tone in enumerate(quarter):
            if j > 0:
                seq.add_tone("bell", 0.5)
            seq.add_tone(tone, 0)
    
    # Hour strokes
    seq.add_tone("bell", 3)  # Gap before hour
    for i in range(hour % 12):
        if i > 0:
            seq.add_tone("bell", 0.5)
        seq.add_tone("bell", 0)
    
    return seq
