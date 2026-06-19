import os
from groq import Groq

# Menggabungkan API Key Groq langsung ke dalam environment code
os.environ["GROQ_API_KEY"] = "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"

client = Groq()

def jalankan_agent_bertahap():
    print("Mulai menginisialisasi Agent Website Budi Mebel...")
    
    # TAHAP 1: Tugas Simpel (Membuat Kerangka HTML Kosong)
    # Kita biarkan agent belajar dari struktur dasar terlebih dahulu
    prompt_tahap_1 = """
    Kamu adalah Web Developer profesional. Tugas pertamamu sangat simpel:
    Buat kerangka dasar HTML5 untuk sebuah website single-page. 
    Hanya buatkan tag <header>, <main> (dengan section Hero, Layanan, Portofolio), dan <footer>.
    Gunakan Tailwind CSS via CDN. Jangan isi teks kontennya dulu, cukup kerangkanya.
    """
    
    print("\n[Tahap 1] Agent sedang menyusun kerangka dasar HTML...")
    response_1 = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_tahap_1}],
        temperature=0.3
    )
    kerangka_html = response_1.choices[0].message.content
    
    # TAHAP 2: Mengisi Konten dan Tema Spesifik Budi Mebel
    # Setelah paham kerangkanya, kita berikan instruksi spesifik klien
    prompt_tahap_2 = f"""
    Sempurna. Sekarang kita akan memperbaiki tata letak dan menyuntikkan interaktivitas kelas atas (Scroll Animations) pada "Super Landing Page" Budi Mebel agar terasa seperti website premium.
    Lanjutkan dari kode HTML berikut:
    {kerangka_html}
    
    Terapkan instruksi TEKNIS berikut secara ketat:
    
    1. ATURAN MUTLAK: HANYA keluarkan kode HTML murni dari <!DOCTYPE html> sampai </html>. JANGAN gunakan markdown ```html.
    
    2. CDN WAJIB (Tailwind & AOS):
       - Di dalam <head>, wajib masukkan 2 baris ini:
         <script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script>
         <link href="[https://unpkg.com/aos@2.3.1/dist/aos.css](https://unpkg.com/aos@2.3.1/dist/aos.css)" rel="stylesheet">
       - Tepat sebelum tag penutup </body>, wajib masukkan:
         <script src="[https://unpkg.com/aos@2.3.1/dist/aos.js](https://unpkg.com/aos@2.3.1/dist/aos.js)"></script>
         <script>AOS.init({{ duration: 1000, once: true }});</script>
         
    3. FIX HERO SECTION (ANTI-BOCOR):
       - Di dalam <head>, tambahkan <style>:
         @keyframes zoomBg {{ 0% {{ transform: scale(1); }} 100% {{ transform: scale(1.1); }} }}
         .hero-bg {{ animation: zoomBg 20s infinite alternate ease-in-out; }}
         html {{ scroll-behavior: smooth; }}
       - Susun Hero Section TEPAT seperti ini: Gunakan tag <section> dengan class `relative w-full h-screen overflow-hidden flex items-center justify-center`. 
       - Di dalamnya, buat div untuk background dengan class `absolute inset-0 hero-bg bg-cover bg-center` (gunakan link gambar arsitektur rumah mewah).
       - Buat div untuk overlay dengan class `absolute inset-0 bg-black/60 z-10`.
       - Buat div untuk konten teks dengan class `relative z-20 text-center text-white px-4` dan tambahkan atribut `data-aos="zoom-in"`.
       
    4. INTERAKTIVITAS KONTEN (AOS & HOVER):
       - Navbar: Pastikan class-nya `fixed top-0 w-full z-50 bg-white/90 backdrop-blur shadow-md`.
       - Tentang Kami: Beri atribut `data-aos="fade-up"` pada kontainer teksnya.
       - Kartu Layanan: Beri class hover (`hover:-translate-y-2 hover:shadow-2xl transition-all duration-300`). Agar muncul bergantian, beri atribut `data-aos="fade-up"` pada setiap kartu, dan tambahkan `data-aos-delay="100"` untuk kartu pertama, `200` untuk kartu kedua, dst.
       - Portofolio: Beri `data-aos="zoom-in-up"` pada grid gambarnya.
       
    5. KONTEN ASLI (JANGAN DIUBAH):
       - Navbar memuat `<img src="logo.png" alt="Logo">`.
       - Tentang Kami memuat teks kebanggaan menjadi vendor "FIFGroup".
       - Footer memuat alamat "Jl. KH Zubeir Ahmad No. 27, Gg. MAN Sadabuan".
    """
    
    print("\n[Tahap 2] Agent sedang mengisi styling mewah dan konten Budi Mebel...")
    response_2 = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_tahap_2}],
        temperature=0.5
    )
    
    hasil_akhir = response_2.choices[0].message.content
    
    # Menyimpan hasil ke file index_revisi.html
    with open("index_revisi.html", "w", encoding="utf-8") as f:
        f.write(hasil_akhir)
        
    print("\nSelesai! File index_revisi.html untuk Budi Mebel berhasil dibuat.")

if __name__ == "__main__":
    jalankan_agent_bertahap()