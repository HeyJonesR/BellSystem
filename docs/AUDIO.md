# Audio Setup

## Supported Formats

- **MP3** — all carillon bell recordings use this format
- **WAV** — Signed 16-bit Little Endian, any sample rate (44.1/48 kHz recommended)

Playback is handled by pygame.mixer (SDL2_mixer), which supports both formats natively.

## Sound File Location

All audio files live under `config/audio_samples/`:

```
config/audio_samples/
├── carillon-bells/         # 13 digital carillon recordings (MP3)
│   ├── america-the-beautiful.mp3
│   ├── ave-maria.mp3
│   ├── carillon-peal.mp3
│   ├── god-rest-ye-merry-gentlemen.mp3
│   ├── hallelujah-chorus.mp3
│   ├── hark-the-herald-angels-sing.mp3
│   ├── jesu-joy-of-mans-desiring.mp3
│   ├── joyful-joyful.mp3
│   ├── morning-has-broken.mp3
│   ├── noon-hour-bell-strike.mp3
│   ├── swinging-english-tuned-bell.mp3
│   ├── swinging-flemish-bell.mp3
│   └── westminster-chimes-full.mp3
├── traditional/            # Traditional bell sounds
└── westminster/            # Westminster quarter chime
```

## Adding New Sounds

Drop any `.wav` or `.mp3` file into `config/audio_samples/` or a subfolder.
The web UI discovers new files automatically — no restart needed.

Naming convention: use lowercase with hyphens (`my-new-bell.mp3`).
The UI converts filenames to display labels automatically
(e.g., `my-new-bell.mp3` → "My New Bell").

## Hardware Setup

### Raspberry Pi 5

The Pi 5 has **no 3.5mm headphone jack**. You need an external audio device:

| Option | Notes |
|--------|-------|
| **USB DAC** (Sound Blaster Play! 3, etc.) | Plug-and-play, $10–30 |
| **I2S DAC HAT** (HiFiBerry DAC+, IQaudio) | Best quality, requires config |
| **HDMI audio extractor** | Uses HDMI port |

### ALSA Configuration

After connecting your audio device, find it:

```bash
cat /proc/asound/cards
```

Example output:
```
 0 [S3             ]: USB-Audio - Sound Blaster Play! 3
 1 [vc4hdmi0       ]: vc4-hdmi - vc4-hdmi-0
 2 [vc4hdmi1       ]: vc4-hdmi - vc4-hdmi-1
```

Configure `/etc/asound.conf` using the **card name** (not number — numbers
change across reboots):

```
pcm.!default {
    type plug
    slave.pcm "dmix:S3,0"
}
ctl.!default {
    type hw
    card S3
}
```

Replace `S3` with your card's name from the brackets in `cat /proc/asound/cards`.

### Set Volume to Maximum

The app controls volume in software; set ALSA to 100%:

```bash
amixer -c 0 scontrols              # list available controls
amixer -c 0 set Speaker 100%       # or PCM, Master — depends on card
```

### Test

```bash
# Test ALSA directly
aplay /usr/share/sounds/alsa/Front_Center.wav

# Test pygame as the bells user
sudo -u bells SDL_AUDIODRIVER=alsa /opt/bells/venv/bin/python3 -c "
import pygame, time
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
s = pygame.mixer.Sound('/opt/bells/config/audio_samples/carillon-bells/westminster-chimes-full.mp3')
s.play()
time.sleep(10)
"
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `aplay -l` shows "no soundcards found" | User not in `audio` group: `sudo usermod -aG audio $USER`, then re-login |
| `ALSA: Couldn't open audio device: Unknown error 524` | Card doesn't support direct `hw` access. Use `plug` + `dmix` in `asound.conf` |
| Sound plays through HDMI, not USB DAC | Wrong default card. Update `asound.conf` to point to your USB card |
| Card number changes after reboot | Use card **name** (e.g., `S3`) instead of number in `asound.conf` |
| `ALSA lib pcm.c: underrun occurred` | Harmless with 512-sample buffer. Increase to 1024 if audio glitches |

## Audio Source Credits

Carillon bell recordings from [Freesound.org](https://freesound.org/)
by theblockofsound235. See `config/audio_samples/carillon-bells/_readme_and_license.txt`
for full license details.
