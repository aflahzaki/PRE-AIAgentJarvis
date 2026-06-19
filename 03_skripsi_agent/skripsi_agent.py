import os
from phi.agent import Agent
from phi.model.openai import OpenAIChat

# =====================================================================
# 1. OTENTIKASI (Menggunakan otak pintar NVIDIA Llama 3.3)
# =====================================================================
os.environ["OPENAI_API_KEY"] = "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" # Pastikan API Key Anda aktif
os.environ["OPENAI_BASE_URL"] = "https://integrate.api.nvidia.com/v1"

academic_agent = Agent(
    name="Thesis Writer",
    model=OpenAIChat(id="meta/llama-3.3-70b-instruct"), 
    instructions=[
        "Kamu adalah asisten peneliti ahli yang sedang menulis Bab 1 untuk skripsi bidang IT.",
        "Topik utama: Optimasi dan Interpretasi Prediksi Risiko Stroke Menggunakan Stacking Ensemble Learning dan SHAP.",
        "Tulisan harus sangat akademis, formal, objektif, dan tajam.",
        "Gunakan standar IEEE (poin-poin pertanyaan penelitian yang spesifik dan terukur)."
    ],
    markdown=False, 
)

# =====================================================================
# 2. PROSES MEMBACA FILE MANUAL (Pasti Berhasil)
# =====================================================================
nama_file_sumber = "isi template proposal aflah.txt" # Pastikan file ini ada di folder yang sama dengan skrip ini

print(f"Mencoba membaca isi dari {nama_file_sumber}...")
try:
    with open(nama_file_sumber, "r", encoding="utf-8") as f:
        isi_pendahuluan = f.read()
    print("File proposal berhasil dibaca!\n")
except FileNotFoundError:
    print(f"ERROR: File '{nama_file_sumber}' tidak ditemukan di folder ini.")
    print("Pastikan namanya benar dan filenya ada di folder yang sama dengan skrip ini.")
    exit() # Menghentikan program jika file tidak ada


# =====================================================================
# 3. PROSES BERPIKIR & MENULIS (Menggunakan Prompt Terarah)
# =====================================================================
tugas_rencana_kegiatan = f"""
Berikut adalah isi dari Bab 1 Pendahuluan skripsi saya:
\"\"\"
{isi_pendahuluan}
\"\"\"

Berdasarkan teks pendahuluan di atas, tolong buatkan HANYA 'Sub-bab 1.5 Rencana Kegiatan' untuk skripsi berjudul 'Analisis Preskriptif Kualitas Air Menggunakan Natural Gradient Boosting dan Counterfactual Explanations'.

ATURAN SUPER KETAT (WAJIB DIPATUHI):
1. FOKUS PENELITIAN: Ini adalah penelitian murni di ranah Data Science / Machine Learning menggunakan dataset sekunder (Kaggle).
2. DILARANG KERAS mengasumsikan penelitian ini menggunakan hardware, merakit alat, atau membangun sistem fisik IoT di lapangan. Fokus mutlak pada manipulasi, pemodelan, dan interpretasi data secara software.
3. Ikuti format penulisan akademik resmi institusi (FIF Universitas Telkom) dan standar IEEE.
4. Gunakan kalimat pasif/orang ketiga, formal, baku (EYD), dan objektif.
5. JANGAN berikan teks basa-basi penjelas atau komentar AI di awal atau di akhir. Langsung keluarkan isi naskah sub-babnya.

Struktur Konten Rencana Kegiatan yang WAJIB Anda susun secara detail dan kritis:
- Paragraf Pengantar: Jelaskan secara singkat bahwa rencana kegiatan Tugas Akhir ini disusun secara sistematis melalui beberapa tahapan utama demi menjamin validitas hasil pemodelan.
- Poin 1 (Kajian Pustaka): Jelaskan rencana pencarian, penelaahan, dan sintesis literatur ilmiah (jurnal terindeks) yang berkaitan dengan parameter kualitas air, teori dasar algoritma Natural Gradient Boosting (NGBoost), serta framework Counterfactual Explanations menggunakan DiCE.
- Poin 2 (Cara Pengumpulan Data): Deklarasikan secara tegas bahwa metode pengumpulan data menggunakan pendekatan kuantitatif melalui pemanfaatan data sekunder berupa dataset parameter fisik dan kimia air yang diperoleh dari platform publik Kaggle. Sebutkan bahwa data tersebut mencakup fitur-fitur seperti pH, turbiditas, klorin, dan padatan terlarut.
- Poin 3 (Rancangan Penelitian & Perancangan Sistem): Jabarkan prosedur penelitian yang mencakup tahap pra-proses data (data preprocessing), pembagian data (data splitting), pelatihan model prediktif menggunakan NGBoost, integrasi Explainable AI (XAI), hingga perancangan alur generasi penyesuaian fitur menggunakan Counterfactual Explanations (DiCE).
- Poin 4 (Cara Menguji Hasil Penelitian): Rincikan bagaimana performa model prediktif dievaluasi (menggunakan metrik seperti akurasi, precision, recall, dan F1-score) serta bagaimana hasil rekomendasi preskriptif dari DiCE diinterpretasikan, ditafsirkan, dan ditarik kesimpulannya untuk mendukung keputusan operasional kelayakan air.

Format Output: Mulai langsung dengan judul '1.5. RENEANA KEGIATAN' (sesuaikan typo template: 1.5. Rencana Kegiatan), diikuti paragraf pengantar, lalu gunakan format penulisan poin-poin deskriptif yang mendalam untuk keempat tahapan di atas.
"""

print("Jarvis sedang memikirkan dan menulis Sub-bab 1.5 Rencana Kegiatan...")
response = academic_agent.run(tugas_rencana_kegiatan)


# =====================================================================
# 4. PROSES MENYIMPAN FILE MANUAL (Anti-Gagal)
# =====================================================================
# Menentukan nama file output yang spesifik HANYA untuk Sub-bab 1.5
nama_file_baru = "Sub_Bab_1_5_Rencana_Kegiatan.txt"

# Membuka file (mode "w" untuk menulis baru) dan menyimpan hasilnya secara fisik
with open(nama_file_baru, "w", encoding="utf-8") as file:
    file.write("1.5. RENCANA KEGIATAN\n\n")
    file.write(response.content)

print(f"\n✅ SUKSES BESAR! File '{nama_file_baru}' telah berhasil dibuat di folder ini.")