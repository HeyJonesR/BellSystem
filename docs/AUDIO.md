# ChapelBells Audio Setup Guide

This guide explains how to add bell audio files to your ChapelBells system from various sources.

## Quick Start

The system comes with sample bell tones (sine waves) for testing. To use professional bell recordings:

1. **Download** bell audio from one of the sources below
2. **Convert** to WAV format (44.1kHz or 48kHz, 16-bit)
3. **Place** files in `audio_samples/` directory
4. **Configure** in `config/schedule.yaml`
5. **Test** via web dashboard

## Audio File Sources

### Recommended: Professional Bell Recordings

#### 1. **ChimeMaster** (https://www.chimemaster.com/)
- **Most suitable for churches**
- Westminster Quarter hours, full carillons, traditional bells
- Professional studio quality
- License: Purchase (commercial use)
- Cost: $10-50 per recording
- Quality: ⭐⭐⭐⭐⭐

#### 2. **Zapsplat** (https://www.zapsplat.com/)
- High-quality bell and chime sounds
- Free with account
- Search: "church bell", "bell chime", "tower bell"
- License: Free for most uses
- Quality: ⭐⭐⭐⭐

#### 3. **Freesound.org** (https://freesound.org/)
- Community-contributed bell sounds
- Search: "church bell", "bell toll", "carillon"
- License: Check each file (mostly Creative Commons)
- Quality: ⭐⭐⭐ to ⭐⭐⭐⭐

#### 4. **YouTube Audio Library** (https://www.youtube.com/audio-library)
- Royalty-free music and effects
- Search: "bell", "chime", "church"
- License: Free for YouTube videos (check for other uses)
- Quality: ⭐⭐⭐⭐

#### 5. **FreeSFX** (https://www.freesfx.co.uk/)
- Church bells and bell tower sounds
- License: Free for most uses
- Quality: ⭐⭐⭐

### DIY: Record Your Own

The most authentic option is to record your actual church bells:

```bash
# Use a smartphone or quality microphone
# Use free audio recording software:
# - Audacity (audacity.org)
# - GarageBand (Mac)
# - QuickTime Player (Mac)

# Record 30 seconds of your bell
# Save as WAV format
# Extract bell segments in Audacity
# Export each segment as separate WAV file
```

## Audio File Format Requirements

| Property | Required | Details |
|----------|----------|---------|
| **Format** | WAV or FLAC | Uncompressed or lossless |
| **Sample Rate** | 44.1kHz or 48kHz | Standard audio rates |
| **Bit Depth** | 16-bit minimum | 24-bit optional |
| **Channels** | Mono or Stereo | Mono recommended for bells |
| **Duration** | 2-10 seconds | Per bell tone |
| **File Size** | 50KB - 500KB | Typical for bell sounds |

## Directory Structure

```
ChurchBell/
└── audio_samples/
    ├── westminster/          # Westminster Quarter chimes
    │   ├── bell.wav          # Main bell sound
    │   ├── tone_1.wav        # First quarter tone
    │   ├── tone_2.wav        # Second quarter tone
    │   └── tone_3.wav        # Third quarter tone
    │
    ├── carillon/             # Multi-bell carillon
    │   ├── bell.wav          # Main carillon
    │   └── high.wav          # Optional: high notes
    │
    └── traditional/          # Single bell chimes
        └── bell.wav          # Traditional bell toll
```

## Installation Steps

### 1. Download Audio Files

From ChimeMaster (example):
```bash
# Download westminster.wav, carillon.wav, etc. to your computer
```

### 2. Convert to Correct Format

If files are not WAV format at 44.1kHz, convert using FFmpeg:

```bash
# Install FFmpeg (if needed)
sudo apt-get install ffmpeg

# Convert MP3 to WAV (44.1kHz, mono)
ffmpeg -i westminster.mp3 -ar 44100 -ac 1 audio_samples/westminster/bell.wav

# Convert MP4 to WAV
ffmpeg -i bell_audio.mp4 -ar 44100 audio_samples/westminster/bell.wav

# Extract audio from video
ffmpeg -i video.mp4 -q:a 0 -map a audio_samples/westminster/bell.wav
```

### 3. Place Files in Directories

```bash
# Copy downloaded files to correct profiles
cp ~/Downloads/westminster_bells.wav audio_samples/westminster/bell.wav
cp ~/Downloads/carillon_bell.wav audio_samples/carillon/bell.wav
cp ~/Downloads/traditional_bell.wav audio_samples/traditional/bell.wav
```

### 4. Verify Audio Files

```bash
# List all audio files
ls -lah audio_samples/*/

# Test playback
aplay audio_samples/westminster/bell.wav

# Check file format
file audio_samples/westminster/bell.wav
```

### 5. Update Configuration

Edit `config/schedule.yaml`:

```yaml
audio_profiles:
  westminster:
    type: simple
    duration: 60
  carillon:
    type: simple
    duration: 45
  traditional:
    type: simple
    duration: 30

events:
  - name: "Sunday Service"
    rule: "sunday at 10:00"
    audio_profile: "westminster"
    tone: "bell"
    duration_seconds: 60
    
  - name: "Hourly Chimes"
    rule: "every hour"
    audio_profile: "carillon"
    tone: "bell"
    duration_seconds: 15
    quiet_hours: true
```

### 6. Test Audio

Via command line:
```bash
aplay audio_samples/westminster/bell.wav
```

Via web dashboard:
1. Open http://localhost:5000
2. Go to Settings → Audio Test
3. Select profile and click "Play"

## Multi-Tone Sequences

For Westminster Quarter chimes (4 tones):

```
audio_samples/westminster/
├── bell.wav       # Full 4-bell sequence
├── tone_1.wav     # First bell
├── tone_2.wav     # Second bell
└── tone_3.wav     # Third bell
```

Configure in schedule.yaml:
```yaml
audio_profiles:
  westminster:
    type: simple
    duration: 8          # 4 tones × 2 seconds each
```

## Deployment to Raspberry Pi

```bash
# Copy audio directory to Raspberry Pi
scp -r audio_samples pi@192.168.1.100:/path/to/ChurchBell/

# Or deploy with git
cd /path/to/ChurchBell
git add audio_samples/
git commit -m "Add professional bell audio recordings"
git push

# On Raspberry Pi, pull the audio
cd ChurchBell
git pull
```

## Troubleshooting

### Audio Not Playing

```bash
# List audio devices
aplay -l

# Test playback directly
aplay audio_samples/westminster/bell.wav

# Check ALSA configuration
alsamixer

# Check volume levels
amixer get Master
```

### Audio Format Error

```bash
# Check file format
file audio_samples/westminster/bell.wav

# Output should be:
# WAV or WAVE audio, Microsoft PCM, 16 bit, mono 44100 Hz

# If not WAV, convert using FFmpeg
ffmpeg -i input.mp3 -ar 44100 -ac 1 output.wav
```

### Distorted or Quiet Audio

```bash
# Check if audio needs volume adjustment
# Use Audacity to:
# 1. Open the WAV file
# 2. Select all (Ctrl+A)
# 3. Effect → Normalize
# 4. Export as WAV

# Or use FFmpeg to normalize
ffmpeg -i input.wav -af "volume=1.5" output.wav
```

### Missing Files Error

```bash
# Ensure directories exist
mkdir -p audio_samples/{westminster,carillon,traditional}

# Verify files
ls -la audio_samples/westminster/
ls -la audio_samples/carillon/
ls -la audio_samples/traditional/

# Check file permissions
chmod 644 audio_samples/*/*
```

## Sample Audio Specifications

The included sample files are generated sine waves:

| Profile | Frequency | Duration | Use |
|---------|-----------|----------|-----|
| westminster | 587Hz (D) | 0.5s | Test/Demo |
| carillon | 440Hz (A) | 1.0s | Test/Demo |
| traditional | 330Hz (E) | 2.0s | Test/Demo |

Replace these with professional bell recordings for production use.

## License Considerations

When downloading audio:
- ✅ Check the usage rights for your use case
- ✅ Give attribution if required
- ✅ Verify commercial use is allowed (if needed)
- ❌ Don't use copyrighted material without permission

## Advanced: Create Custom Profiles

Add new profiles to `audio_samples/`:

```bash
mkdir audio_samples/bells_of_notre_dame
# Add bell files to this directory

# Update schedule.yaml
audio_profiles:
  bells_of_notre_dame:
    type: simple
    duration: 120
```

## Next Steps

1. Download bell audio from recommended sources above
2. Convert to WAV format if needed
3. Place files in appropriate directories
4. Test via web dashboard
5. Configure events in schedule.yaml
6. Deploy to production

---

For questions or issues, check the main [README.md](../README.md) or [INSTALLATION.md](./INSTALLATION.md).
