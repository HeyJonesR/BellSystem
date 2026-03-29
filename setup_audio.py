#!/usr/bin/env python3
"""
Audio File Setup Guide for ChapelBells

This script helps you add audio files to the ChapelBells system.
Audio files should be WAV or FLAC format, 44.1kHz or 48kHz sample rate.

SOURCES FOR BELL AUDIO:
========================

1. **ChimeMaster** (https://www.chimemaster.com/)
   - Professional church bell recordings
   - Westminster, Carillon, Traditional formats
   - License: Typically purchase-based
   - Quality: Studio professional

2. **FreeSFX** (https://www.freesfx.co.uk/)
   - Church bell SFX
   - Church bells, bell towers, chimes
   - License: Free for most uses (check each file)
   - Quality: Good amateur

3. **Freesound.org** (https://freesound.org/)
   - Bell sounds and chimes
   - Search: "church bell", "bell toll", "carillon"
   - License: Various (check Creative Commons compatibility)
   - Quality: Variable

4. **Zapsplat** (https://www.zapsplat.com/)
   - Free sound effects
   - Church bells and bell tolls
   - License: Free with attribution
   - Quality: Good

5. **YouTube Audio Library** (https://www.youtube.com/audio-library)
   - Royalty-free music and sound effects
   - Search: "bell", "chime", "church"
   - License: Free to use
   - Quality: Good

6. **Local Church**
   - Record your own church bells
   - Record the bell tower
   - Most authentic option
   - License: Your own

SETUP INSTRUCTIONS:
===================

Directory Structure:
    audio_samples/
    ├── westminster/          # Westminster chimes
    │   ├── bell.wav
    │   ├── tone_1.wav
    │   ├── tone_2.wav
    │   └── tone_3.wav
    ├── carillon/             # Multi-bell carillon
    │   ├── bell.wav
    │   └── sequence.wav
    └── traditional/          # Traditional single bell
        └── bell.wav

Steps to Add Audio:
1. Download WAV or FLAC files from one of the sources above
2. Ensure format is correct (WAV 44.1kHz or 48kHz, mono or stereo)
3. Copy to appropriate directory:
   cp downloaded_bell.wav audio_samples/westminster/bell.wav
4. Update config/schedule.yaml to use the profile:
   events:
     - name: "Sunday Service"
       rule: "sunday at 10:00"
       audio_profile: "westminster"
       tone: "bell"
5. Test via web UI: Dashboard → Settings → Audio Test

AUDIO FILE REQUIREMENTS:
========================

Format:        WAV or FLAC
Sample Rate:   44.1kHz or 48kHz
Channels:      Mono or Stereo
Duration:      2-10 seconds per file
Bitrate:       16-bit depth minimum
File Size:     50KB - 500KB per file

Converting Audio Files:
=======================

If your files are in the wrong format, convert them using FFmpeg:

Install FFmpeg:
  sudo apt-get install ffmpeg

Convert MP3 to WAV (44.1kHz, mono):
  ffmpeg -i input.mp3 -ar 44100 -ac 1 output.wav

Convert MP3 to WAV (48kHz, stereo):
  ffmpeg -i input.mp3 -ar 48000 -ac 2 output.wav

Convert FLAC to WAV:
  ffmpeg -i input.flac output.wav

Generate Test Tone (440Hz, 2 seconds):
  ffmpeg -f lavfi -i sine=frequency=440:duration=2 -q:a 9 test_tone.wav

CONFIGURATION:
===============

In config/schedule.yaml, reference audio profiles:

audio_profiles:
  westminster:
    type: simple
    duration: 60
  carillon:
    type: sequence
    duration: 45
  traditional:
    type: simple
    duration: 30

Then use in events:
  events:
    - name: "Hourly Chimes"
      rule: "every hour"
      audio_profile: "westminster"
      tone: "bell"

PLAYLIST SUPPORT:
==================

For multiple tones in sequence, create a sequence file:

1. Create audio_samples/westminster/sequence.wav with multiple bell tones
2. Or configure in schedule.yaml with custom duration

TROUBLESHOOTING:
=================

Audio not playing?
- Check ALSA: aplay audio_samples/westminster/bell.wav
- Check volume: alsamixer
- Check permissions: ls -la audio_samples/

Wrong audio format error?
- Convert using FFmpeg (see instructions above)
- Check file type: file audio_samples/westminster/bell.wav

Silent or distorted audio?
- Check volume levels (use Audacity to adjust if needed)
- Ensure file format meets requirements (44.1kHz or 48kHz)
- Try a different source if audio quality is poor

RECOMMENDED WORKFLOW:
======================

1. Download 3-4 bell audio files from your preferred source
2. Convert to standardized format (44.1kHz WAV)
3. Place in appropriate directories (westminster, carillon, traditional)
4. Name files consistently (bell.wav, tone_1.wav, etc)
5. Update config/schedule.yaml to reference the profiles
6. Test via web dashboard
7. Deploy to Raspberry Pi with same directory structure
"""

def create_sample_wav():
    """Create sample WAV files for testing."""
    import wave
    import array
    import os
    
    def generate_sine_wave(frequency, duration, sample_rate=44100):
        """Generate a simple sine wave."""
        import math
        num_samples = int(duration * sample_rate)
        samples = []
        for i in range(num_samples):
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * i / sample_rate))
            samples.append(sample)
        return samples
    
    profiles = {
        'westminster': {
            'frequencies': [587, 523, 659, 494],  # D, C, E, B
            'duration': 0.5
        },
        'carillon': {
            'frequencies': [440],  # A
            'duration': 1.0
        },
        'traditional': {
            'frequencies': [330],  # E
            'duration': 2.0
        }
    }
    
    for profile_name, profile_data in profiles.items():
        profile_dir = f'audio_samples/{profile_name}'
        os.makedirs(profile_dir, exist_ok=True)
        
        # Create main bell sound (first frequency)
        freq = profile_data['frequencies'][0]
        samples = generate_sine_wave(freq, profile_data['duration'])
        
        wav_path = f'{profile_dir}/bell.wav'
        with wave.open(wav_path, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(44100)
            wav_file.writeframes(array.array('h', samples).tobytes())
        
        print(f'✓ Created {wav_path}')
        
        # Create individual tones if multiple frequencies
        for idx, freq in enumerate(profile_data['frequencies'][1:], 1):
            samples = generate_sine_wave(freq, profile_data['duration'])
            tone_path = f'{profile_dir}/tone_{idx}.wav'
            with wave.open(tone_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(44100)
                wav_file.writeframes(array.array('h', samples).tobytes())
            print(f'✓ Created {tone_path}')

if __name__ == '__main__':
    print("ChapelBells Audio Setup\n")
    print(f"\n{__doc__}")
    
    print("\n\n" + "="*60)
    print("GENERATE SAMPLE AUDIO FILES")
    print("="*60)
    
    try:
        create_sample_wav()
        print("\n✓ Sample audio files created successfully!")
        print("\nNext steps:")
        print("1. Test audio: aplay audio_samples/westminster/bell.wav")
        print("2. Add your own bells from sources listed above")
        print("3. Update config/schedule.yaml with audio profiles")
        print("4. Test via web dashboard at http://localhost:5000")
    except Exception as e:
        print(f"\n⚠ Note: Could not generate sample files: {e}")
        print("This is optional - provide your own audio files instead")
