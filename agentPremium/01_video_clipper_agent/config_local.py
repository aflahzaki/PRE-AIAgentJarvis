"""
⚙️ CONFIGURATION MODULE (LOCAL PROCESSING)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Configuration untuk Viral Video Clipper Agent dengan LOCAL FILE PROCESSING.
Edit file ini untuk customize behavior tanpa mengubah main code.

CATATAN PENTING: Semua path dalam file ini akan menjadi FOLDER BASIS,
bukan file individual. Pipeline akan otomatis memproses SEMUA file
di dalam folder tersebut.
"""

import os
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# DIRECTORY STRUCTURE (MANDATORY - JANGAN UBAH TANPA ALASAN KUAT)
# ═══════════════════════════════════════════════════════════════════

# Base directory dari project ini
BASE_DIR = Path(__file__).parent.resolve()

# INPUT DIRECTORIES
# ────────────────────────────────────────────────────────────────────
# Folder video mentah (landscape MP4, format: Any resolution)
# Semua file MP4 di folder ini akan diproses otomatis
VIDEO_INPUT_DIR = BASE_DIR / "vidio_mentah"

# Folder audio mentah (WAV/MP3 dari video yang sama)
# Nama file harus MATCH dengan video (contoh: video1.mp4 → video1.wav)
AUDIO_INPUT_DIR = BASE_DIR / "audio_mentah"

# OUTPUT DIRECTORIES
# ────────────────────────────────────────────────────────────────────
# Folder hasil video jadi (portrait MP4 9:16, durasi max 15s per file)
# Hasil akan dinamis bernama: viral_short_001.mp4, viral_short_002.mp4, dst
VIDEO_OUTPUT_DIR = BASE_DIR / "vidio_clip_finish"

# Folder temporary (untuk debugging dan cleanup)
TEMP_DIR = BASE_DIR / "_temp"

# Folder untuk menyimpan log proses
LOG_DIR = BASE_DIR / "_logs"

# ═══════════════════════════════════════════════════════════════════
# AGENT 1: LOCAL AUDIO ANALYSIS SETTINGS
# ═══════════════════════════════════════════════════════════════════

class AudioConfig:
    """Konfigurasi untuk audio analysis"""
    
    # Threshold dBFS untuk mendeteksi spike audio (dalam desibel)
    # Range: -30 (super sensitif) hingga -5 (sangat ketat)
    # Rekomendasi: -12 dB (balanced)
    # Tips:
    #   -30 dB: Tangkap semua noise + suara (terlalu sensitif)
    #   -20 dB: Tangkap suara bicara normal + reaksi
    #   -15 dB: Balanced - teriakan/tawa sedang
    #   -12 dB: Ketat - hanya teriakan/tawa keras (RECOMMENDED)
    #   -8 dB:  Sangat ketat - jeritan ekstrem saja
    THRESHOLD_DB = -12.0
    
    # Ukuran chunk analisis (milidetik)
    # Semakin kecil = semakin presisi tapi lebih lambat
    # Recommended: 500-1000ms
    CHUNK_MS = 500
    
    # Minimum gap antara dua spike untuk dianggap klip terpisah (detik)
    # Jika gap < nilai ini, dua spike dianggap satu momen lucu
    # Recommended: 3-5 detik
    MIN_GAP_SECONDS = 4.0
    
    # Durasi minimum & maximum untuk satu klip (detik)
    # IMPORTANT: max_duration harus ≤ 15 karena format TikTok/Shorts
    MIN_CLIP_DURATION = 1.0
    MAX_CLIP_DURATION = 15.0
    
    # Overlap antara detected peaks (detik)
    # Digunakan untuk menghindari pemotongan yang terlalu tepat di puncak suara
    PEAK_MARGIN_BEFORE = 0.5  # Mulai detik sebelum peak
    PEAK_MARGIN_AFTER = 0.5   # Akhir detik setelah peak

# ═══════════════════════════════════════════════════════════════════
# AGENT 2: WHISPER TRANSCRIPTION SETTINGS
# ═══════════════════════════════════════════════════════════════════

class WhisperConfig:
    """Konfigurasi untuk Whisper speech-to-text"""
    
    # Model size untuk Faster-Whisper
    # Options: tiny, base, small, medium, large
    # Trade-off: Lebih besar = lebih akurat tapi lebih lambat
    # Recommended: base (balance) atau small (untuk CPU weak)
    MODEL_SIZE = "base"
    
    # Device untuk inference
    # Options: cuda (GPU), cpu (CPU)
    # Auto-detect akan digunakan jika tidak dispecify
    DEVICE = "auto"  # atau "cpu" / "cuda"
    
    # Compute type untuk optimasi
    # Options: float32 (akurat tapi lebih memory), float16 (balanced), int8 (cepat tapi kurang akurat)
    COMPUTE_TYPE = "float32"
    
    # Bahasa untuk transcription
    # Untuk Indonesia/Inggris mixed: None (auto-detect)
    # Untuk Indonesia saja: "id"
    # Untuk Inggris saja: "en"
    LANGUAGE = None  # Auto-detect
    
    # Temperature untuk decoding (0.0 - 1.0)
    # Semakin tinggi = lebih creative tapi kurang akurat
    # Recommended: 0.0 (deterministic, untuk presisi maksimal)
    TEMPERATURE = 0.0
    
    # Number of beams untuk beam search
    # Semakin tinggi = lebih akurat tapi lebih lambat
    # Recommended: 5
    NUM_BEAMS = 5

# ═══════════════════════════════════════════════════════════════════
# AGENT 3: VIDEO COMPOSITION & STYLING SETTINGS
# ═══════════════════════════════════════════════════════════════════

class VideoConfig:
    """Konfigurasi untuk video editing & composition"""
    
    # Target resolution untuk output
    # Format: (width, height) dalam pixel
    # Untuk portrait 9:16, recommended: (540, 960) atau (720, 1280)
    OUTPUT_RESOLUTION = (720, 1280)  # Full HD portrait
    
    # FPS untuk video output
    FPS = 30
    
    # Codec untuk rendering
    # Options: 'libx264' (h264, default), 'libx265' (hevc), 'mpeg4'
    VIDEO_CODEC = "libx264"
    
    # Audio codec
    # Options: 'aac', 'mp3', 'libvorbis'
    AUDIO_CODEC = "aac"
    
    # Bitrate untuk video (kbps)
    # Recommended: 2500-5000 untuk good quality portrait
    VIDEO_BITRATE = "3000k"
    
    # Bitrate untuk audio (kbps)
    # Recommended: 128-256 untuk clear audio
    AUDIO_BITRATE = "192k"
    
    # Number of rendering threads (untuk optimasi)
    # Recommended: -1 (auto), atau jumlah cores dikurang 1
    # Contoh: 4 core → set 3
    NUM_THREADS = -1  # Auto

# ═══════════════════════════════════════════════════════════════════
# TEXT & SUBTITLE STYLING
# ═══════════════════════════════════════════════════════════════════

class TextConfig:
    """Styling untuk subtitle & text overlay"""
    
    # Font settings
    FONT_NAME = "Arial"  # Atau: "Montserrat", "Impact", "Verdana"
    FONT_SIZE = 50  # Pixel (untuk resolution 720x1280)
    
    # Text color (RGB)
    # White: (255, 255, 255)
    # Yellow: (255, 255, 0)
    # Cyan: (0, 255, 255)
    TEXT_COLOR = (255, 255, 0)  # Yellow
    
    # Outline/stroke (untuk visibility over video)
    OUTLINE_WIDTH = 3  # Pixel
    OUTLINE_COLOR = (0, 0, 0)  # Black
    
    # Positioning
    MARGIN_BOTTOM = 100  # Pixel dari bawah
    MAX_WIDTH_PERCENT = 0.85  # 85% dari lebar video
    
    # Animation timing
    FADE_IN_DURATION = 0.1  # detik
    FADE_OUT_DURATION = 0.1  # detik
    WORD_HOLD_MIN = 0.2  # Minimum waktu sebelum fade out
    
    # Hook text styling (teks untuk hook/opening)
    HOOK_FONT_SIZE = 65  # Lebih besar
    HOOK_TEXT_COLOR = (255, 255, 0)  # Yellow
    HOOK_OUTLINE_WIDTH = 4  # Lebih tebal

# ═══════════════════════════════════════════════════════════════════
# HOOK DETECTION & OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════

class HookConfig:
    """Konfigurasi untuk hook optimization"""
    
    # Durasi pertama video yang harus jadi "hook" pembuka (detik)
    # Recommended: 1-3 detik
    HOOK_DURATION = 2.5
    
    # Strategi hook:
    # - 'loudest': Gunakan momen dengan dB tertinggi
    # - 'most_energetic': Gunakan segmen dengan RMS tertinggi
    # - 'first_word': Gunakan kata pertama yang paling ekspresif
    HOOK_STRATEGY = "loudest"
    
    # Jika menggunakan strategi word-based, berapa kata untuk hook?
    HOOK_WORD_COUNT = 2
    
    # Transition effect untuk hook
    # Options: 'fade', 'zoom', 'cut', 'slide_from_bottom'
    HOOK_TRANSITION = "zoom"

# ═══════════════════════════════════════════════════════════════════
# PROCESSING & OPTIMIZATION SETTINGS
# ═══════════════════════════════════════════════════════════════════

class ProcessingConfig:
    """Konfigurasi untuk optimasi processing"""
    
    # Enable parallel processing (jika ada multiple cores)
    PARALLEL_PROCESSING = True
    
    # Max number of parallel tasks
    MAX_WORKERS = 4
    
    # Timeout untuk setiap proses (detik)
    PROCESSING_TIMEOUT = 300  # 5 menit per video
    
    # Enable debug mode (print detail logs)
    DEBUG_MODE = False
    
    # Auto-cleanup temporary files setelah render sukses
    AUTO_CLEANUP = True
    
    # Keep failed clips (untuk debugging)
    KEEP_FAILED_CLIPS = False
    
    # Log level
    # Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    LOG_LEVEL = "INFO"

# ═══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def ensure_directories():
    """Buat semua directory yang diperlukan"""
    directories = [
        VIDEO_INPUT_DIR,
        AUDIO_INPUT_DIR,
        VIDEO_OUTPUT_DIR,
        TEMP_DIR,
        LOG_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    return True


def get_config_summary():
    """Return summary of current configuration"""
    summary = f"""
╔════════════════════════════════════════════════════════════════╗
║          LOCAL PIPELINE CONFIGURATION SUMMARY                 ║
╚════════════════════════════════════════════════════════════════╝

📁 DIRECTORIES:
   Input Video:   {VIDEO_INPUT_DIR}
   Input Audio:   {AUDIO_INPUT_DIR}
   Output Video:  {VIDEO_OUTPUT_DIR}
   Temp Storage:  {TEMP_DIR}

🎵 AUDIO ANALYSIS:
   Threshold:     {AudioConfig.THRESHOLD_DB} dB
   Chunk Size:    {AudioConfig.CHUNK_MS} ms
   Min Duration:  {AudioConfig.MIN_CLIP_DURATION} s
   Max Duration:  {AudioConfig.MAX_CLIP_DURATION} s

🤖 WHISPER:
   Model:         {WhisperConfig.MODEL_SIZE}
   Language:      {WhisperConfig.LANGUAGE if WhisperConfig.LANGUAGE else 'Auto-detect'}

🎬 VIDEO OUTPUT:
   Resolution:    {VideoConfig.OUTPUT_RESOLUTION[0]}x{VideoConfig.OUTPUT_RESOLUTION[1]} (9:16 portrait)
   Codec:         {VideoConfig.VIDEO_CODEC}
   FPS:           {VideoConfig.FPS}
   Bitrate:       {VideoConfig.VIDEO_BITRATE}

📝 SUBTITLES:
   Font:          {TextConfig.FONT_NAME} {TextConfig.FONT_SIZE}px
   Color:         RGB{TextConfig.TEXT_COLOR}
   Outline:       {TextConfig.OUTLINE_WIDTH}px {TextConfig.OUTLINE_COLOR}

🎣 HOOK:
   Duration:      {HookConfig.HOOK_DURATION} s
   Strategy:      {HookConfig.HOOK_STRATEGY}
"""
    return summary


if __name__ == "__main__":
    # Test configuration
    ensure_directories()
    print(get_config_summary())
    print("✓ Configuration loaded successfully!")
