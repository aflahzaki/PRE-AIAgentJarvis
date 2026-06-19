"""
⚙️ CONFIGURATION MODULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Configuration management untuk Viral Video Clipper Agent.
Edit file ini untuk customize behavior tanpa mengubah main code.
"""

import os
import json
from pathlib import Path


class Config:
    """Configuration handler"""
    
    # ═══════════════════════════════════════════════════════════════
    # YOUTUBE VIDEO SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    # URL video YouTube yang akan diproses
    YOUTUBE_URL = "https://www.youtube.com/watch?v=ndAQfTzlVjc"
    
    # ═══════════════════════════════════════════════════════════════
    # AGENT 1: AUDIO PEAK DETECTOR SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    # Threshold dBFS untuk mendeteksi spike audio
    # Range: -20 (very sensitive) hingga -5 (super strict)
    # Recommended: -12 (balanced)
    # Tips:
    #   -20 dB: Tangkap bisikan & noise (terlalu sensitif)
    #   -15 dB: Tangkap suara normal + teriakan
    #   -12 dB: Balanced - teriakan/tawa sedang (RECOMMENDED)
    #   -8 dB:  Hanya teriakan/reaksi sangat keras
    #   -5 dB:  Super strict - jeritan ekstrem saja
    AUDIO_THRESHOLD_DB = -12.0
    
    # Ukuran chunk analisis audio (dalam milidetik)
    # Semakin kecil = semakin presisi tapi lebih lambat
    # Semakin besar = semakin cepat tapi kurang presisi
    # Recommended: 1000 (1 detik)
    AUDIO_CHUNK_MS = 1000
    
    # Minimum gap antara dua spike untuk dianggap klip terpisah (detik)
    # Jika gap < nilai ini, dua spike dianggap satu momen
    # Recommended: 5-6 detik
    # Tips:
    #   2 detik:   Klip lebih banyak, seringkali terpotong
    #   5 detik:   Balanced (RECOMMENDED)
    #   10 detik:  Klip lebih sedikit, lebih utuh
    AUDIO_MIN_GAP_SECONDS = 6.0
    
    # ═══════════════════════════════════════════════════════════════
    # AGENT 2: VIDEO CLIPPER SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    # Format output video
    # Current: 9:16 (Portrait untuk TikTok/YouTube Shorts)
    # Bisa diubah ke: 16:9 (Landscape), 1:1 (Square), etc
    OUTPUT_ASPECT_RATIO = "9:16"  # width:height
    
    # Codec video untuk rendering
    # Options: "libx264" (slow, best quality), "libx265" (H.265, slower)
    # Recommended: "libx264" untuk compatibility
    VIDEO_CODEC = "libx264"
    
    # Codec audio untuk rendering
    # Options: "aac" (recommended), "mp3", "libmp3lame"
    AUDIO_CODEC = "aac"
    
    # Thread untuk rendering (lebih tinggi = lebih cepat tapi CPU intensive)
    # Recommended: 4 (untuk quad-core CPU)
    # Set ke 0 untuk auto-detect
    RENDER_THREADS = 4
    
    # ═══════════════════════════════════════════════════════════════
    # CLIP VALIDATION SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    # Minimum durasi klip dalam detik
    # Klip lebih pendek akan di-skip
    # Recommended: 0.5 - 1.0 detik
    CLIP_MIN_DURATION = 1.0
    
    # Maximum durasi klip dalam detik
    # Klip lebih panjang akan di-skip
    # Recommended: 300 detik (5 menit)
    CLIP_MAX_DURATION = 300.0
    
    # ═══════════════════════════════════════════════════════════════
    # FOLDER & FILE SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    # Folder untuk menyimpan audio yang diunduh
    DOWNLOADS_FOLDER = "downloads"
    
    # Folder untuk menyimpan video output
    OUTPUT_FOLDER = "output_clips"
    
    # Prefix nama file output
    # Final name: "{OUTPUT_PREFIX}_{number}.mp4"
    OUTPUT_PREFIX = "clip"
    
    # Simpan log processing ke JSON
    ENABLE_JSON_LOG = True
    JSON_LOG_FILE = "processing_log.json"
    
    # ═══════════════════════════════════════════════════════════════
    # YT-DLP SETTINGS (YouTube Download)
    # ═══════════════════════════════════════════════════════════════
    
    # Enable retry untuk failed downloads
    YTDLP_RETRY_COUNT = 3
    
    # Socket timeout (detik)
    YTDLP_SOCKET_TIMEOUT = 30
    
    # Quiet mode (True = suppress output, False = show details)
    YTDLP_QUIET = False
    
    # ═══════════════════════════════════════════════════════════════
    # KILL SWITCH SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    # Enable kill switch (stop pipeline jika ada error)
    ENABLE_KILL_SWITCH = True
    
    # Jumlah error berturut-turut sebelum kill switch triggered
    # Jika < 1, trigger pada error pertama
    ERROR_THRESHOLD = 1
    
    # ═══════════════════════════════════════════════════════════════
    # LOGGING & DEBUG SETTINGS
    # ═══════════════════════════════════════════════════════════════
    
    # Log level: DEBUG, INFO, WARNING, ERROR
    LOG_LEVEL = "INFO"
    
    # Print progress bar saat rendering
    SHOW_PROGRESS_BAR = True
    
    # ═══════════════════════════════════════════════════════════════
    # STATIC METHODS
    # ═══════════════════════════════════════════════════════════════
    
    @staticmethod
    def get_output_filename(index: int) -> str:
        """Generate output filename"""
        return f"{Config.OUTPUT_PREFIX}_{index:03d}.mp4"
    
    @staticmethod
    def ensure_folders():
        """Ensure all required folders exist"""
        for folder in [Config.DOWNLOADS_FOLDER, Config.OUTPUT_FOLDER]:
            Path(folder).mkdir(exist_ok=True)
    
    @staticmethod
    def to_dict() -> dict:
        """Convert config to dictionary"""
        return {
            # Audio settings
            'audio_threshold_db': Config.AUDIO_THRESHOLD_DB,
            'audio_chunk_ms': Config.AUDIO_CHUNK_MS,
            'audio_min_gap_seconds': Config.AUDIO_MIN_GAP_SECONDS,
            
            # Video settings
            'output_aspect_ratio': Config.OUTPUT_ASPECT_RATIO,
            'video_codec': Config.VIDEO_CODEC,
            'audio_codec': Config.AUDIO_CODEC,
            'render_threads': Config.RENDER_THREADS,
            
            # Clip validation
            'clip_min_duration': Config.CLIP_MIN_DURATION,
            'clip_max_duration': Config.CLIP_MAX_DURATION,
            
            # Folders
            'downloads_folder': Config.DOWNLOADS_FOLDER,
            'output_folder': Config.OUTPUT_FOLDER,
            'output_prefix': Config.OUTPUT_PREFIX,
            
            # YT-DLP
            'ytdlp_retry_count': Config.YTDLP_RETRY_COUNT,
            'ytdlp_socket_timeout': Config.YTDLP_SOCKET_TIMEOUT,
            'ytdlp_quiet': Config.YTDLP_QUIET,
            
            # Kill switch
            'enable_kill_switch': Config.ENABLE_KILL_SWITCH,
            'error_threshold': Config.ERROR_THRESHOLD,
        }
    
    @staticmethod
    def load_from_json(filepath: str) -> bool:
        """
        Load configuration dari JSON file.
        
        Args:
            filepath: Path ke JSON config file
        
        Returns:
            True jika berhasil
        """
        try:
            with open(filepath, 'r') as f:
                config_data = json.load(f)
            
            # Map JSON keys ke class attributes
            for key, value in config_data.items():
                attr_name = key.upper()
                if hasattr(Config, attr_name):
                    setattr(Config, attr_name, value)
            
            return True
        except Exception as e:
            print(f"Error loading config: {e}")
            return False
    
    @staticmethod
    def save_to_json(filepath: str) -> bool:
        """
        Save configuration ke JSON file.
        
        Args:
            filepath: Path ke JSON config file
        
        Returns:
            True jika berhasil
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(Config.to_dict(), f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    @staticmethod
    def print_config():
        """Print current configuration"""
        print("\n" + "="*70)
        print("⚙️  CURRENT CONFIGURATION")
        print("="*70)
        
        config_dict = Config.to_dict()
        
        for key, value in config_dict.items():
            print(f"{key:<25} : {value}")
        
        print("="*70)


# ═════════════════════════════════════════════════════════════════
# PRESET CONFIGURATIONS
# ═════════════════════════════════════════════════════════════════

class ConfigPresets:
    """Pre-defined configuration presets"""
    
    @staticmethod
    def SENSITIVE():
        """Preset: Sangat sensitif (tangkap lebih banyak momen)"""
        Config.AUDIO_THRESHOLD_DB = -15.0
        Config.AUDIO_MIN_GAP_SECONDS = 2.0
        Config.CLIP_MIN_DURATION = 0.5
    
    @staticmethod
    def BALANCED():
        """Preset: Balanced (recommended)"""
        Config.AUDIO_THRESHOLD_DB = -12.0
        Config.AUDIO_MIN_GAP_SECONDS = 6.0
        Config.CLIP_MIN_DURATION = 1.0
    
    @staticmethod
    def STRICT():
        """Preset: Strict (hanya tangkap momen terbaik)"""
        Config.AUDIO_THRESHOLD_DB = -8.0
        Config.AUDIO_MIN_GAP_SECONDS = 10.0
        Config.CLIP_MIN_DURATION = 1.5
    
    @staticmethod
    def FAST():
        """Preset: Fast processing (compromise quality untuk kecepatan)"""
        Config.AUDIO_CHUNK_MS = 2000
        Config.RENDER_THREADS = 8
        Config.VIDEO_CODEC = "libx264"  # Gunakan libx265 untuk faster
    
    @staticmethod
    def HIGH_QUALITY():
        """Preset: High quality output (lambat tapi hasil bagus)"""
        Config.AUDIO_CHUNK_MS = 500
        Config.AUDIO_THRESHOLD_DB = -12.0
        Config.RENDER_THREADS = 2
        Config.VIDEO_CODEC = "libx264"


# ═════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🔧 Configuration Module")
    
    # Print current config
    Config.print_config()
    
    # Save ke JSON
    print("\n💾 Saving config to config.json...")
    Config.save_to_json("config.json")
    print("✓ Saved!")
    
    # Test preset
    print("\n🎯 Testing STRICT preset...")
    ConfigPresets.STRICT()
    Config.print_config()
    
    # Reset to balanced
    print("\n↩️  Resetting to BALANCED preset...")
    ConfigPresets.BALANCED()
    Config.print_config()
