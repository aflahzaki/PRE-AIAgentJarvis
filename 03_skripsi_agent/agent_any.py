import os
from phi.agent import Agent
from phi.model.openai import OpenAIChat

# =====================================================================
# 1. OTENTIKASI (Menggunakan NVIDIA Llama 3.3)
# =====================================================================
# Pastikan API Key Anda aktif
os.environ["OPENAI_API_KEY"] = "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" 
os.environ["OPENAI_BASE_URL"] = "https://integrate.api.nvidia.com/v1"

academic_agent = Agent(
    name="Thesis Writer",
    model=OpenAIChat(id="meta/llama-3.3-70b-instruct"), 
    instructions=[
        "Kamu adalah asisten peneliti ahli dan reviewer IEEE yang sedang menulis Bab 1 untuk skripsi bidang IT.",
        "Topik utama: Optimasi dan Interpretasi Prediksi Risiko Stroke Menggunakan Stacking Ensemble Learning dan SHAP.",
        "Tulisan harus sangat akademis, formal, objektif, dan tajam (bebas dari opini subjektif).",
        "Fokus pada identifikasi 'research gap' terkait class imbalance dan fenomena black-box pada model Machine Learning klinis."
    ],
    markdown=False, 
)

# =====================================================================
# 2. PROSES MEMBACA FILE MANUAL 
# =====================================================================
# Membaca draf latar belakang yang sudah disiapkan
nama_file_sumber = "latarbelakang_fanny.txt" 

print(f"Mencoba membaca isi dari {nama_file_sumber}...")
try:
    with open(nama_file_sumber, "r", encoding="utf-8") as f:
        isi_pendahuluan = f.read()
    print("File latar belakang berhasil dibaca!\n")
except FileNotFoundError:
    print(f"ERROR: File '{nama_file_sumber}' tidak ditemukan di folder ini.")
    print("Pastikan namanya benar dan filenya ada di folder yang sama dengan skrip ini.")
    exit() 


# =====================================================================
# 3. PROSES BERPIKIR & MENULIS (Prompt Perumusan Masalah IEEE)
# =====================================================================
tugas_perumusan_masalah = f"""
Berikut adalah isi dari Latar Belakang skripsi:
\"\"\"
{isi_pendahuluan}
\"\"\"

Tugas Utama:
Berdasarkan teks latar belakang di atas, susunlah "Sub-bab 1.2 Perumusan Masalah" (Problem Statement / Research Questions) dalam bahasa Indonesia akademis yang formal dan terstruktur.

Konteks & Celah Penelitian (Research Gap):
1. Ketidakseimbangan Distribusi Kelas (Class Imbalance): Mayoritas dataset medis memiliki jumlah pasien stroke kurang dari 5%. Algoritma standar menghasilkan model bias.
2. Fenomena Black-Box: Model klasifikasi tingkat lanjut tidak memiliki transparansi, sehingga praktisi medis kesulitan memahami justifikasi prediksi.
3. Kebaruan (Novelty): Penelitian ini menggunakan arsitektur Stacking Ensemble Learning (mengintegrasikan XGBoost, LightGBM, CatBoost) dipadukan dengan teknik penyeimbangan data dan SHAP untuk interpretabilitas.

Instruksi Output yang WAJIB dipatuhi:
1. JANGAN berikan teks basa-basi penjelas atau komentar AI di awal atau di akhir. Langsung keluarkan isi naskahnya.
2. Paragraf Pengantar (1-2 paragraf): Rangkum dengan padat inti permasalahan dari latar belakang (class imbalance dan isu black-box pada sistem pendukung keputusan medis). Gunakan bahasa objektif dan saintifik (standar IEEE).
3. Poin Perumusan Masalah (Research Questions): Buat 3 poin pertanyaan penelitian terukur (measurable) yang langsung menjawab research gap:
   - Poin pertama fokus pada cara mengatasi ketidakseimbangan kelas data secara efektif.
   - Poin kedua fokus pada performa arsitektur Stacking Ensemble (Trio-Boosting) dibandingkan model tunggal dalam memprediksi risiko stroke.
   - Poin ketiga fokus pada bagaimana metode SHAP dapat membongkar black-box model untuk memberikan interpretasi fitur klinis yang valid.

Format Output: Mulai langsung dengan judul '1.2. PERUMUSAN MASALAH', diikuti paragraf pengantar, lalu gunakan poin-poin bernomor untuk pertanyaan penelitian.
"""

print("Agent sedang memikirkan dan menyusun Sub-bab 1.2 Perumusan Masalah...")
response = academic_agent.run(tugas_perumusan_masalah)


# =====================================================================
# 4. PROSES MENYIMPAN FILE MANUAL
# =====================================================================
nama_file_baru = "Sub_Bab_1_2_Perumusan_Masalah_Fanny.txt"

with open(nama_file_baru, "w", encoding="utf-8") as file:
    file.write(response.content)

print(f"\n✅ SUKSES! File '{nama_file_baru}' telah berhasil dibuat di folder ini.")