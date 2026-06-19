"""
🎵 AGENT 1: AUDIO PEAK DETECTOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mengunduh audio dari YouTube dan mendeteksi lonjakan volume (teriakan, tawa, reaksi)
untuk menghasilkan timestamp klip viral otomatis.

Teknologi:
- yt-dlp: Download audio dengan bypass JavaScript cipher via Android client
- wave: Membaca format .wav (built-in, kompatibel Python 3.13+)
- numpy: Menghitung RMS dan konversi dBFS tanpa library deprecated 'audioop'

Cara Kerja:
1. Download audio → wav 2. Analisis per 1000ms (chunk) → RMS → dBFS
3. Filter lonjakan > threshold → Kelompokkan timestamps berdekatan
4. Output: List[(start_time, end_time)] untuk Agent 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import wave
import numpy as np
from yt_dlp import YoutubeDL
import logging

# Setup logging sederhana
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class AudioPeakDetectorAgent:
    """
    Agent untuk deteksi momen viral dari analisis audio.
    Mengidentifikasi spike volume yang merupakan indikasi teriakan/tawa intens.
    """
    
    def __init__(self, download_dir="downloads"):
        """
        Inisialisasi Audio Peak Detector.
        
        Args:
            download_dir (str): Direktori penyimpanan file audio .wav
        """
        self.download_dir = download_dir
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            logger.info(f"Folder '{download_dir}' telah dibuat.")

    def download_audio(self, video_url):
        """Mengunduh audio format WAV menggunakan yt-dlp dengan bypass anti-bot YouTube"""
        logger.info(f"Mengunduh audio (WAV) dari: {video_url}")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.download_dir, '%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',  # WAV untuk kompatibilitas wave + numpy
            }],
            'quiet': False,
            # BYPASS ANTI-BOT: Penyamaran sebagai Android client untuk bypass JavaScript cipher
            'extractor_args': {'youtube': ['player_client=android,web']},
            'socket_timeout': 30,  # Timeout untuk mencegah hang
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                filename = os.path.join(self.download_dir, f"{info['id']}.wav")
                
                # Validasi file berhasil diunduh
                if not os.path.exists(filename):
                    raise FileNotFoundError(f"File audio gagal disimpan: {filename}")
                
                file_size_mb = os.path.getsize(filename) / (1024 * 1024)
                logger.info(f"✓ Audio berhasil diunduh: {info['title'][:50]}... ({file_size_mb:.2f} MB)")
                return filename, info['title']
                
        except Exception as e:
            logger.error(f"✗ Gagal mengunduh audio: {e}")
            raise

    def find_high_energy_moments(self, wav_path, threshold_db=-10.0, chunk_ms=1000):
        """
        Menganalisis file WAV per chunk (default 1 detik) untuk mendeteksi spike audio.
        Menggunakan wave + numpy (tanpa library deprecated 'audioop').
        
        Args:
            wav_path (str): Path ke file .wav
            threshold_db (float): Batas dBFS untuk deteksi (default -10.0 = cukup keras)
            chunk_ms (int): Ukuran chunk analisis dalam milidetik (default 1000ms)
        
        Returns:
            list: [(timestamp_detik, db_value), ...] untuk setiap lonjakan suara
        """
        logger.info(f"Menganalisis audio dari: {wav_path}")
        
        try:
            with wave.open(wav_path, 'rb') as wf:
                sample_rate = wf.getframerate()
                sampwidth = wf.getsampwidth()
                n_channels = wf.getnchannels()
                total_frames = wf.getnframes()
                
                # Info debug
                duration_sec = total_frames / sample_rate
                logger.info(f"  Sample Rate: {sample_rate} Hz | Durasi: {duration_sec:.2f}s | Channels: {n_channels}")
                
                # Menghitung jumlah frame per chunk
                chunk_frames = int(sample_rate * (chunk_ms / 1000.0))
                high_energy_timestamps = []
                current_time = 0.0
                
                while True:
                    frames = wf.readframes(chunk_frames)
                    if not frames:
                        break
                    
                    # Konversi bytes → numpy array (sesuai bit depth)
                    if sampwidth == 2:  # 16-bit (paling umum)
                        data = np.frombuffer(frames, dtype=np.int16)
                    elif sampwidth == 1:  # 8-bit
                        data = np.frombuffer(frames, dtype=np.uint8).astype(np.int16) - 128
                    elif sampwidth == 3:  # 24-bit (jarang tapi ada)
                        # Handle 24-bit secara manual
                        data = np.frombuffer(frames, dtype=np.uint8)
                        data = data.reshape(-1, 3)
                        data = (data[:, 0] + (data[:, 1] << 8) + ((data[:, 2] << 16) - 
                               (data[:, 2] >= 128) * (1 << 24))).astype(np.int32)
                    else:
                        current_time += chunk_ms / 1000.0
                        continue
                    
                    if len(data) == 0:
                        break
                    
                    # Menghitung RMS (Root Mean Square) → indikator volume rata-rata
                    rms = np.sqrt(np.mean(data.astype(np.float64) ** 2))
                    
                    # Konversi ke dBFS (Decibel relative to Full Scale)
                    # Referensi: 16-bit max = 32768
                    if rms > 0:
                        db = 20 * np.log10(rms / 32768.0)
                    else:
                        db = -100.0
                    
                    # Jika melebihi threshold, simpan timestamp
                    if db > threshold_db:
                        high_energy_timestamps.append((current_time, db))
                    
                    current_time += chunk_ms / 1000.0
                
                logger.info(f"✓ Ditemukan {len(high_energy_timestamps)} momen dengan volume > {threshold_db} dB")
                return high_energy_timestamps
                
        except Exception as e:
            logger.error(f"✗ Error saat menganalisis audio: {e}")
            raise

    def group_timestamps(self, timestamps, min_gap_seconds=5):
        """
        Mengelompokkan timestamp lonjakan yang berdekatan menjadi rentang klip utuh.
        Jika gap antara dua spike < min_gap_seconds, dianggap satu momen viral.
        
        Args:
            timestamps (list): [(time_sec, db), ...] dari find_high_energy_moments()
            min_gap_seconds (float): Gap minimum untuk menganggap momen terpisah
        
        Returns:
            list: [(start_time, end_time), ...] untuk setiap klip yang valid
        """
        if not timestamps:
            logger.warning("⚠ Tidak ada timestamp untuk dikelompokkan.")
            return []
        
        grouped = []
        start_time = timestamps[0][0]
        prev_time = timestamps[0][0]
        
        for t, db in timestamps[1:]:
            # Jika gap terlalu besar, awal klip baru
            if t - prev_time > min_gap_seconds:
                grouped.append((start_time, prev_time))
                start_time = t
            prev_time = t
        
        # Tambahkan klip terakhir
        grouped.append((start_time, prev_time))
        
        # Filter durasi > 0
        valid_clips = [(s, e) for s, e in grouped if e > s]
        logger.info(f"✓ Dikelompokkan menjadi {len(valid_clips)} rentang klip")
        
        return valid_clips
    
    def validate_clips(self, clips, min_duration=1.0, max_duration=300.0):
        """
        Validasi klip untuk memastikan durasi wajar.
        Hindari klip terlalu pendek (noise) atau terlalu panjang (memori).
        
        Args:
            clips (list): [(start, end), ...]
            min_duration (float): Durasi minimum klip dalam detik
            max_duration (float): Durasi maksimum klip dalam detik
        
        Returns:
            list: Klip yang valid setelah filter
        """
        valid = []
        for start, end in clips:
            duration = end - start
            if min_duration <= duration <= max_duration:
                valid.append((start, end))
            else:
                logger.debug(f"  ⊗ Klip {start}s~{end}s (durasi {duration}s) ditolak")
        
        logger.info(f"✓ Setelah validasi durasi: {len(valid)} klip valid")
        return valid

# ═════════════════════════════════════════════════════════════════
# EKSEKUSI PIPELINE DETEKSI AUDIO PEAK
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║          🎵 AGENT 1: AUDIO PEAK DETECTOR 🎵                  ║
    ║   Mendeteksi Momen Viral Dari Analisis Gelombang Suara       ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    detector = AudioPeakDetectorAgent()
    
    # ⚠️ MASUKKAN URL VIDEO PILIHAN ANDA DI SINI
    test_url = "https://www.youtube.com/watch?v=AaMdXZMvT3w"
    
    try:
        # TAHAP 1: Unduh Audio
        print("\n[Tahap 1/4] Mengunduh audio dari YouTube...")
        audio_file, title = detector.download_audio(test_url)
        
        # TAHAP 2: Deteksi Spike Volume
        print("\n[Tahap 2/4] Mendeteksi lonjakan suara (teriakan, tawa, reaksi intens)...")
        raw_peaks = detector.find_high_energy_moments(
            audio_file, 
            threshold_db=-12.0,  # Range optimal: -12 hingga -8 dB untuk teriakan/tawa
            chunk_ms=1000         # Analisis per 1 detik
        )
        
        # TAHAP 3: Kelompokkan Menjadi Klip
        print("\n[Tahap 3/4] Mengelompokkan momen yang berdekatan menjadi klip utuh...")
        clip_ranges = detector.group_timestamps(raw_peaks, min_gap_seconds=6)
        
        # TAHAP 4: Validasi Klip
        print("\n[Tahap 4/4] Validasi durasi klip (min 1s, max 5 menit)...")
        valid_clips = detector.validate_clips(clip_ranges, min_duration=1.0, max_duration=300.0)
        
        # OUTPUT HASIL
        print("\n" + "="*70)
        print("✅ HASIL DETEKSI MOMEN VIRAL")
        print("="*70)
        print(f"Video: {title[:60]}")
        print(f"Total klip viral terdeteksi: {len(valid_clips)}")
        print("="*70)
        
        if not valid_clips:
            print("⚠️  Tidak ada momen yang melintasi ambang batas volume.")
        else:
            print(f"\n{'No':<4} {'Start (s)':<12} {'End (s)':<12} {'Duration':<12}")
            print("-" * 70)
            for idx, (start, end) in enumerate(valid_clips, 1):
                duration = end - start
                print(f"{idx:<4} {start:<12.2f} {end:<12.2f} {duration:<12.2f}s")
            
            # Output dalam format Python list (untuk copy-paste ke Agent 2)
            print("\n📋 Format Python List (untuk Agent 2):")
            print(f"clip_timestamps = {valid_clips}")
        
        print("\n✓ Agent 1 selesai. Siap untuk Agent 2 (Video Clipper).\n")
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()