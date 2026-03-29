#!/usr/bin/env python3
"""
Mixkit Church Bell Audio Downloader Helper

This script provides instructions and commands to download free church bell
sounds from Mixkit (https://mixkit.co/free-sound-effects/church-bell/)
and organize them into the ChapelBells audio directory structure.

Mixkit provides free sound effects with no attribution required.
All downloaded files are royalty-free for commercial and personal use.
"""

import os
import subprocess
from pathlib import Path

# Popular Mixkit church bell sound effects
MIXKIT_BELLS = {
    'Church Bell 1': {
        'id': '3214',
        'profile': 'westminster',
        'filename': 'church_bell_1.wav',
        'description': 'Single church bell toll'
    },
    'Church Bell 2': {
        'id': '3215',
        'profile': 'traditional',
        'filename': 'church_bell_2.wav',
        'description': 'Church bell with resonance'
    },
    'Church Bell 3': {
        'id': '3216',
        'profile': 'carillon',
        'filename': 'church_bell_3.wav',
        'description': 'Multiple bell tones'
    },
    'Bell Chime': {
        'id': '3217',
        'profile': 'westminster',
        'filename': 'bell_chime.wav',
        'description': 'Bell chime sequence'
    },
}

def print_instructions():
    """Print download instructions for Mixkit bells."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           Mixkit Church Bell Audio Downloader                  ║
╚════════════════════════════════════════════════════════════════╝

MIXKIT BENEFITS:
✓ Free sound effects library
✓ No attribution required
✓ Royalty-free for all uses (commercial & personal)
✓ High quality audio

AVAILABLE CHURCH BELLS:
═══════════════════════════════════════════════════════════════

https://mixkit.co/free-sound-effects/church-bell/

Popular bells:
1. Church Bell Toll - Single bell
2. Church Bells Ringing - Multiple bells
3. Bell Chime - Sequence of tones
4. Church Tower Bells - Large carillon
5. Small Bell Ring - Delicate bell

HOW TO DOWNLOAD:
════════════════════════════════════════════════════════════════

Option 1: Manual Download (Easiest)
───────────────────────────────────
1. Visit: https://mixkit.co/free-sound-effects/church-bell/
2. Browse and select bells you like
3. Click the bell sound
4. Click "Download" or download button
5. Save to your computer
6. Run the organizing script (see below)

Option 2: Using youtube-dl or yt-dlp
─────────────────────────────────────
Install yt-dlp (handles various formats):
  pip install yt-dlp

Then download:
  yt-dlp "https://mixkit.co/free-sound-effects/church-bell/" \\
    -o "%(title)s.%(ext)s"

Option 3: Using curl (if direct links available)
──────────────────────────────────────────────────
  curl -o church_bell.wav "https://mixkit.co/api/v1/..." 

ORGANIZING DOWNLOADED FILES:
════════════════════════════════════════════════════════════════

After downloading, place files in correct directories:

  mv ~/Downloads/church_bell_toll.wav audio_samples/westminster/bell.wav
  mv ~/Downloads/church_bells_ringing.wav audio_samples/traditional/bell.wav
  mv ~/Downloads/bell_chime_sequence.wav audio_samples/carillon/bell.wav

Or use the organize script below...

SCRIPT: Auto-Organize Downloaded Files
═════════════════════════════════════════════════════════════════

1. Download files from Mixkit to ~/Downloads/mixkit_bells/
2. Run this script:
   python3 organize_mixkit_bells.py
3. Files will be moved to correct directories

NEXT STEPS:
═════════════════════════════════════════════════════════════════

1. Download 3-4 bell sounds from Mixkit
2. Place in audio_samples/ directories
3. Test with: aplay audio_samples/westminster/bell.wav
4. Update config/schedule.yaml
5. Test via web dashboard at http://localhost:5000
6. Deploy to Raspberry Pi

SUPPORTED AUDIO FORMATS FROM MIXKIT:
════════════════════════════════════

Mixkit provides:
✓ MP3 (may need conversion to WAV)
✓ WAV (ready to use)
✓ Files auto-convert at 44.1kHz

If you get MP3 files, convert with FFmpeg:
  ffmpeg -i input.mp3 -ar 44100 -ac 1 output.wav

CONFIGURATION:
═══════════════════════════════════════════════════════════════

After adding files, update config/schedule.yaml:

  audio_profiles:
    westminster:
      type: simple
      duration: 30        # Adjust based on bell duration
    tradition:
      type: simple
      duration: 45
    carillon:
      type: simple
      duration: 60

  events:
    - name: "Sunday Service"
      rule: "sunday at 10:00"
      audio_profile: "westminster"
      tone: "bell"

TESTING:
═════════════════════════════════════════════════════════════════

Command line:
  aplay audio_samples/westminster/bell.wav

Web Dashboard:
  Open http://localhost:5000
  Go to Settings → Audio Test
  Select profile and click Play

LICENSE:
═══════════════════════════════════════════════════════════════

✓ Mixkit sounds are free for commercial and personal use
✓ No attribution required (but appreciated!)
✓ Safe to deploy in production
✓ Can be used in commercial church applications

Learn more: https://mixkit.co/about/

═══════════════════════════════════════════════════════════════
    """)

def organize_bells(source_dir='~/Downloads/mixkit_bells'):
    """
    Organize downloaded Mixkit bells into correct directories.
    
    Expected source structure:
        ~/Downloads/mixkit_bells/
        ├── Church Bell Toll.wav
        ├── Bell Chime.wav
        ├── Church Bells Ringing.wav
        └── etc.
    """
    source_path = Path(source_dir).expanduser()
    
    if not source_path.exists():
        print(f"⚠ Source directory not found: {source_path}")
        print(f"\nCreate and add downloaded files to: {source_path}")
        return False
    
    # Map of keywords in filenames to profile directories
    mappings = {
        'westminster': ['westminster', 'quarter', 'chime'],
        'traditional': ['traditional', 'toll', 'single'],
        'carillon': ['carillon', 'multiple', 'ringing', 'tower'],
    }
    
    moved_count = 0
    
    for wav_file in source_path.glob('*.wav'):
        filename = wav_file.name.lower()
        
        # Determine destination profile
        dest_profile = None
        for profile, keywords in mappings.items():
            if any(keyword in filename for keyword in keywords):
                dest_profile = profile
                break
        
        # If no match, ask user
        if not dest_profile:
            print(f"\nFile: {wav_file.name}")
            print("Options: westminster, traditional, carillon, skip")
            dest_profile = input("Where to place? ").lower()
            if dest_profile == 'skip':
                continue
        
        # Create destination
        dest_dir = Path('audio_samples') / dest_profile
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_file = dest_dir / 'bell.wav'
        
        try:
            import shutil
            shutil.move(str(wav_file), str(dest_file))
            print(f"✓ Moved: {wav_file.name} → {dest_file}")
            moved_count += 1
        except Exception as e:
            print(f"✗ Error moving {wav_file.name}: {e}")
    
    if moved_count > 0:
        print(f"\n✓ Successfully organized {moved_count} files")
        return True
    else:
        print("\nℹ No files moved")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed (for audio conversion)."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✓ FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ FFmpeg not found")
        print("  Install with: sudo apt-get install ffmpeg")
        return False

def convert_mp3_to_wav(input_file, output_file):
    """Convert MP3 to WAV format."""
    if not check_ffmpeg():
        return False
    
    try:
        subprocess.run([
            'ffmpeg', '-i', input_file,
            '-ar', '44100', '-ac', '1',
            output_file, '-y'
        ], check=True, capture_output=True)
        print(f"✓ Converted: {input_file} → {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Conversion failed: {e}")
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'organize':
        # Organize downloaded files
        source = sys.argv[2] if len(sys.argv) > 2 else '~/Downloads/mixkit_bells'
        organize_bells(source)
    else:
        # Print instructions
        print_instructions()
