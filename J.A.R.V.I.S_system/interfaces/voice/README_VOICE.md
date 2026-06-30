# J.A.R.V.I.S Voice Interface

Voice-controlled interface for J.A.R.V.I.S using Speech-to-Text (STT) and Text-to-Speech (TTS).

## Overview

The Voice Interface provides hands-free interaction with J.A.R.V.I.S through:
- **Speech-to-Text (STT)**: Uses `faster-whisper` for local speech recognition
- **Text-to-Speech (TTS)**: Uses `edge-tts` for natural speech output (free Microsoft Azure voices)

Both components are optional. If dependencies are not installed, the system gracefully falls back to text-only mode.

## Installation

### Required (Core)

```bash
pip install rich python-dotenv
```

### Optional: Speech-to-Text

```bash
pip install faster-whisper sounddevice numpy
```

**Note**: The first time you run with STT enabled, the Whisper model will be downloaded automatically (base model is approximately 150MB).

### Optional: Text-to-Speech

```bash
pip install edge-tts
```

### Install Everything

```bash
pip install faster-whisper sounddevice numpy edge-tts
```

## Configuration

Add the following to your `.env` file:

```env
# Voice Interface Configuration
VOICE_MODEL=base
VOICE_LANGUAGE=id
TTS_VOICE=id-ID-ArdiNeural
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MODEL` | `base` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) |
| `VOICE_LANGUAGE` | `id` | Language code for speech recognition (e.g., `id` for Indonesian, `en` for English) |
| `TTS_VOICE` | `id-ID-ArdiNeural` | Edge-TTS voice name |

### Available Whisper Models

| Model | Size | RAM | Description |
|-------|------|-----|-------------|
| `tiny` | 75MB | ~1GB | Fastest, lower accuracy |
| `base` | 150MB | ~1GB | Good balance (recommended) |
| `small` | 500MB | ~2GB | Better accuracy |
| `medium` | 1.5GB | ~5GB | High accuracy |
| `large` | 3GB | ~10GB | Best accuracy |

### Finding TTS Voices

List available edge-tts voices:

```bash
edge-tts --list-voices
```

Popular voices:
- `id-ID-ArdiNeural` - Indonesian male
- `id-ID-GadisNeural` - Indonesian female
- `en-US-GuyNeural` - English (US) male
- `en-US-JennyNeural` - English (US) female

## Usage

### Running

```bash
cd J.A.R.V.I.S_system
python run_voice.py
```

### Modes

1. **Push-to-Talk (default)**: Press Enter to start recording, or type your message directly
2. **Continuous**: Automatically listens and responds (activate with `mode` command)

### Commands

| Command | Description |
|---------|-------------|
| `exit` / `quit` / `q` | Exit the voice interface |
| `mode` | Toggle between push-to-talk and continuous mode |
| `wake` | Show wake word information |
| `status` | Show STT/TTS availability status |
| `help` | Show available commands |

### Wake Word

In continuous mode, the system listens for the wake word "jarvis" before processing input. This prevents unintended activation.

## Troubleshooting

### No audio input detected
- Ensure your microphone is connected and not muted
- Check system audio settings for the correct input device
- Try: `python -c "import sounddevice; print(sounddevice.query_devices())"`

### Whisper model download fails
- Ensure you have internet connectivity for the first download
- The model is cached at `~/.cache/huggingface/` after first download

### TTS not playing audio
- On Linux, install one of: `mpv`, `ffplay`, or `aplay`
- On macOS, `afplay` should be available by default
- Check that your audio output device is working

### ImportError on startup
- This is expected behavior when optional deps are not installed
- The system will show a warning and fall back to text-only mode
