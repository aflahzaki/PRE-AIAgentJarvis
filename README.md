# PRE-AIAgentJarvis

> *"Membangun Asisten AI Pribadi Seperti J.A.R.V.I.S - Tanpa Budget, Tanpa Batas."*

![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)
![License](https://img.shields.io/badge/License-Personal%20Project-blue)
![AI](https://img.shields.io/badge/AI-Multi%20Agent%20System-purple)

---

## Visi Proyek

Proyek ini adalah perjalanan membangun **sistem AI agent pribadi** yang terinspirasi dari J.A.R.V.I.S dalam film Iron Man. Tujuan utamanya adalah menciptakan asisten AI mandiri yang mampu membantu menjalani hidup seefisien mungkin, mulai dari coding otomatis, pembuatan konten, penulisan akademik, hingga analisis data.

**Yang membuat proyek ini unik:** Semua dibangun dengan **resource gratis dan open-source**. Tidak ada API berbayar, tidak ada subscription mahal. Hanya kreativitas, determinasi, dan pemanfaatan maksimal dari resource yang tersedia.

---

## Struktur Repository

```
PRE-AIAgentJarvis/
│
├── J.A.R.V.I.S_system/                    # Sistem Inti - Autonomous Coding Agent
│   ├── jarvis_coder.py                     # Agent utama (self-healing code fixer)
│   ├── jarvis_coder_fixed.py               # Versi stabil
│   ├── run_jarvis.py                       # Runner script
│   ├── test_prediction.py                  # Test file (auto-generated)
│   ├── requirements.txt                    # Dependencies
│   ├── README_JARVIS.md                    # Dokumentasi J.A.R.V.I.S
│   └── SETUP_INSTRUCTIONS.md              # Panduan setup
│
├── 02_web_agent/                           # Agent Pembuat Website Otomatis
│   ├── web_agent.py                        # 2-step website generator (Groq + Llama 3.3)
│   ├── index.html                          # Output: Landing page
│   ├── index_revisi.html                   # Output: Versi revisi
│   └── logo.png                            # Asset logo
│
├── 03_skripsi_agent/                       # Agent Penulisan Akademik/Skripsi
│   ├── skripsi_agent.py                    # Thesis writing agent (Phidata + Nvidia)
│   ├── agent_any.py                        # General-purpose agent
│   ├── BAB_3_Metodologi_NGBoost.md         # Output: Bab 3 Metodologi
│   ├── BAB_3_NGBoost_Implementation.py     # Output: Implementasi kode
│   ├── BAB_4_5_Template_Hasil_Simpulan.md  # Output: Bab 4 & 5
│   ├── Draft_Latar_Belakang_*.txt          # Output: Draft pendahuluan
│   ├── Sub_Bab_1_*.txt                     # Output: Sub-bab 1.2 - 1.5
│   └── requirements.txt                    # Dependencies
│
├── agentPremium/                           # Agent Premium (Fitur Lanjutan)
│   └── 01_video_clipper_agent/             # Viral Video Clipper - 100% Offline
│       ├── ARCHITECTURE_OVERVIEW.md        # Arsitektur lengkap pipeline
│       ├── audio_peak_detector.py          # Deteksi peak audio
│       ├── config.py                       # Konfigurasi utama
│       ├── config_local.py                 # Konfigurasi lokal
│       └── audio_mentah/                   # Input audio files
│
├── Dataset Data Sistem Informasi Daya Tampung (SIDATA) PTN/
│   ├── daftar_prodi.csv                    # Data prodi PTN (2018-2023)
│   └── daftar_universitas.csv              # Daftar universitas negeri
│
├── AMD Developer Hackathon_ ACT II AI Hackathon _ lablab.ai.pdf
│                                           # Referensi kompetisi AI
└── README.md                               # Dokumentasi utama (file ini)
```

---

## Deskripsi Setiap Modul

### 1. J.A.R.V.I.S System - Autonomous Self-Healing Coding Agent

**Otak utama** dari seluruh sistem. Agent ini mampu:
- Membaca dan menganalisis kode Python secara mandiri
- Mengidentifikasi bug tanpa campur tangan manusia
- Memperbaiki kode secara otomatis (self-healing)
- Menjalankan dan memvalidasi hasil perbaikan
- Melakukan loop hingga kode berjalan sempurna

**Tech Stack:** Phidata Framework + Meta Llama 3.3 70B (via Nvidia NIM API)

**Alur Kerja:**
```
LISTEN → READ → ANALYZE → PATCH → VALIDATE → (loop jika gagal) → REPORT
```

---

### 2. Web Agent - AI Website Generator

Agent yang mampu membuat landing page profesional secara otomatis dalam 2 tahap:
1. **Tahap 1:** Menyusun kerangka HTML5 dasar
2. **Tahap 2:** Mengisi konten, styling (Tailwind CSS), dan animasi (AOS.js)

**Tech Stack:** Groq API (Free Tier) + Llama 3.3 70B Versatile

**Output:** Single-page website dengan scroll animations, responsive design, dan optimasi visual.

---

### 3. Skripsi Agent - Academic Writing Assistant

Agent khusus untuk membantu penulisan skripsi/thesis secara akademis dan formal:
- Menghasilkan bab-bab skripsi sesuai standar IEEE
- Fokus pada bidang Data Science / Machine Learning
- Mampu membaca referensi dan menghasilkan tulisan terstruktur

**Tech Stack:** Phidata + Meta Llama 3.3 70B (via Nvidia NIM API)

**Topik Skripsi:** Analisis Preskriptif Kualitas Air Menggunakan Natural Gradient Boosting dan Counterfactual Explanations

---

### 4. Video Clipper Agent - Viral Short-Form Content Creator

Pipeline 100% offline untuk membuat konten viral otomatis:
- Deteksi momen lucu/viral via audio peak detection
- Transkripsi dengan Whisper (word-level timing)
- Auto-crop landscape ke portrait (9:16)
- Subtitle dinamis word-by-word
- Output siap upload ke TikTok/YouTube Shorts/Reels

**Tech Stack:** FFmpeg + OpenAI Whisper (lokal) + MoviePy + NumPy

---

### 5. Dataset SIDATA PTN

Dataset untuk analisis data penerimaan mahasiswa di Perguruan Tinggi Negeri Indonesia:
- Data daya tampung dan jumlah pendaftar (2018-2023)
- Informasi program studi seluruh PTN
- Potensi untuk analisis prediktif SNBP/SNBT

---

## Resource AI Gratis yang Dimanfaatkan

Berikut adalah daftar resource AI **gratis/free tier** yang bisa digunakan untuk membangun sistem J.A.R.V.I.S tanpa biaya:

### Model AI Lokal (Offline, Gratis Selamanya)

| Resource | Deskripsi | Keunggulan |
|----------|-----------|------------|
| [Ollama](https://ollama.ai) | Menjalankan LLM di komputer sendiri | 100% offline, tanpa batas, privasi penuh |
| [LM Studio](https://lmstudio.ai) | GUI untuk menjalankan model lokal | User-friendly, mendukung GGUF format |
| [HuggingFace](https://huggingface.co) | Repository 500,000+ model gratis | Download model apapun, community besar |
| [OpenAI Whisper](https://github.com/openai/whisper) | Speech-to-text lokal | Akurasi tinggi, multi-bahasa, offline |

**Model Lokal yang Direkomendasikan:**
- `llama3.2:3b` - Ringan, cocok untuk PC standar (RAM 8GB)
- `llama3.1:8b` - Seimbang antara kualitas dan kecepatan
- `mistral:7b` - Sangat baik untuk coding tasks
- `phi3:mini` - Ultra-ringan dari Microsoft (RAM 4GB cukup)
- `codellama:7b` - Spesialis coding
- `qwen2.5-coder:7b` - Alternatif coding agent terbaik

### API Gratis (Cloud, Ada Limit Tapi Cukup)

| Resource | Free Tier | Model Tersedia |
|----------|-----------|----------------|
| [Groq](https://console.groq.com) | 30 req/menit, 14,400 req/hari | Llama 3.3 70B, Mixtral, Gemma2 |
| [Nvidia NIM](https://build.nvidia.com) | 1,000 credits gratis | Llama 3.3 70B, Mistral, Code Llama |
| [Google AI Studio](https://aistudio.google.com) | 60 req/menit (Gemini 2.0 Flash) | Gemini 2.0 Flash, Gemini 1.5 Pro |
| [OpenRouter](https://openrouter.ai) | Model gratis tersedia | Llama 3.3, Mixtral, Qwen (free tier) |
| [Cerebras](https://cerebras.ai) | Inference super cepat | Llama 3.3 70B (beta gratis) |
| [SambaNova](https://sambanova.ai) | Free tier tersedia | Llama 3.1, Llama 3.3 |
| [Together AI](https://together.ai) | $5 credit gratis (sign-up) | 100+ model open-source |
| [Fireworks AI](https://fireworks.ai) | Free tier awal | Llama, Mixtral, embedding models |

### Tools & Framework Gratis

| Tool | Fungsi | Link |
|------|--------|------|
| Phidata | Framework multi-agent Python | [phidata.com](https://phidata.com) |
| LangChain | Orchestration framework | [langchain.com](https://langchain.com) |
| CrewAI | Multi-agent collaboration | [crewai.com](https://crewai.com) |
| AutoGen | Microsoft multi-agent framework | [github.com/microsoft/autogen](https://github.com/microsoft/autogen) |
| Streamlit | UI dashboard gratis | [streamlit.io](https://streamlit.io) |
| n8n | Workflow automation (self-hosted) | [n8n.io](https://n8n.io) |

---

## Cara Memulai

### Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies dasar
pip install phidata openai groq
```

### Menjalankan J.A.R.V.I.S System

```bash
cd J.A.R.V.I.S_system
pip install -r requirements.txt
python jarvis_coder.py
```

### Menjalankan Web Agent

```bash
cd 02_web_agent
# Set API key Groq (gratis dari https://console.groq.com)
export GROQ_API_KEY="your-free-groq-key"
python web_agent.py
```

### Menjalankan Skripsi Agent

```bash
cd 03_skripsi_agent
pip install -r requirements.txt
python skripsi_agent.py
```

---

## Roadmap Pengembangan

Roadmap ini menggambarkan evolusi proyek dari eksperimen individual menjadi sistem J.A.R.V.I.S yang terintegrasi penuh:

### Phase 1: Foundation (Sekarang)
- [x] Autonomous Coding Agent (J.A.R.V.I.S self-healing)
- [x] Web Generation Agent (2-step website builder)
- [x] Academic Writing Agent (thesis/skripsi assistant)
- [x] Video Clipper Agent (offline viral content creator)
- [x] Dokumentasi dan organisasi repository

### Phase 2: Local-First Intelligence
- [ ] Migrasi semua agent ke **Ollama** (100% offline capable)
- [ ] Setup local model server (Llama 3.2/3.1 atau Qwen2.5)
- [ ] Implementasi **RAG (Retrieval-Augmented Generation)** dengan ChromaDB/FAISS
- [ ] Personal knowledge base (catatan kuliah, referensi, dokumen pribadi)
- [ ] Voice interface menggunakan Whisper + local TTS

### Phase 3: Multi-Agent Orchestration
- [ ] Central orchestrator yang mengkoordinasi semua agent
- [ ] Agent communication protocol (agent bisa saling berkomunikasi)
- [ ] Task routing otomatis (request masuk, sistem pilih agent terbaik)
- [ ] Memory system - agent mengingat konteks percakapan sebelumnya
- [ ] Scheduler agent (mengingatkan deadline, jadwal, tugas harian)

### Phase 4: Productivity & Life Automation
- [ ] Email agent (summarize, draft reply, filter penting)
- [ ] Research agent (cari paper, summarize, buat literature review)
- [ ] Finance tracker agent (tracking pengeluaran via chat)
- [ ] Study planner agent (buat jadwal belajar adaptif)
- [ ] Data analysis agent (analisis dataset, visualisasi otomatis)
- [ ] Social media manager agent (scheduling, caption generation)

### Phase 5: Full J.A.R.V.I.S Integration
- [ ] Unified interface (satu chat untuk semua kemampuan)
- [ ] Context-aware responses (agent paham siapa kamu dan kebutuhanmu)
- [ ] Proactive suggestions (agent memberi saran tanpa diminta)
- [ ] Multi-modal input (teks, suara, gambar, dokumen)
- [ ] Mobile access via Telegram/WhatsApp bot
- [ ] Self-improvement loop (agent belajar dari feedback)

---

## Filosofi Pengembangan

```
"Kamu tidak butuh uang untuk membangun AI yang powerful.
 Kamu butuh kreativitas, konsistensi, dan kemampuan
 memanfaatkan resource yang sudah tersedia secara gratis."
```

### Prinsip Utama:

1. **Local-First** - Prioritaskan solusi yang berjalan di komputer sendiri (Ollama, Whisper lokal)
2. **Zero-Cost** - Manfaatkan free tier secara maksimal, jangan bayar kalau bisa gratis
3. **Incremental** - Bangun satu agent dulu yang bekerja, lalu integrasikan
4. **Practical** - Fokus pada masalah nyata yang dihadapi sehari-hari
5. **Open Source** - Gunakan dan kontribusi ke ekosistem open-source

---

## Strategi Memanfaatkan Free Tier Secara Optimal

### Rate Limit Management
```python
# Contoh rotasi API key untuk memaksimalkan free tier
API_PROVIDERS = [
    {"name": "groq", "rpm": 30},      # 30 request/menit
    {"name": "nvidia", "daily": 1000}, # 1000 request/hari
    {"name": "google", "rpm": 60},     # 60 request/menit
]

# Jika satu provider limit, otomatis pindah ke provider lain
# Fallback terakhir: model lokal via Ollama (unlimited)
```

### Hybrid Architecture (Recommended)
```
Request masuk
    │
    ├─ Simple task? → Ollama (lokal, instant, unlimited)
    ├─ Complex task? → Groq/Nvidia (cloud, powerful, limited)
    └─ Fallback? → Google Gemini / OpenRouter free models
```

---

## Tech Stack Overview

| Komponen | Teknologi | Status |
|----------|-----------|--------|
| AI Framework | Phidata | Aktif |
| Primary Model | Meta Llama 3.3 70B | Aktif |
| Cloud Provider | Nvidia NIM, Groq | Aktif |
| Local Model | Ollama (planned) | Roadmap |
| Speech-to-Text | OpenAI Whisper | Aktif |
| Video Processing | FFmpeg + MoviePy | Aktif |
| Web Framework | Tailwind CSS + AOS.js | Aktif |
| Language | Python 3.8+ | Aktif |

---

## Kontribusi & Pengembangan

Proyek ini adalah proyek personal yang terus berkembang. Jika kamu punya visi yang sama - membangun AI assistant pribadi tanpa budget besar - silakan fork, experiment, dan kembangkan sesuai kebutuhanmu.

### Ide Kontribusi:
- Implementasi agent baru untuk use case spesifik
- Optimasi prompt engineering untuk model gratis
- Integrasi dengan tools produktivitas (Notion, Google Calendar, dll)
- Dokumentasi dan tutorial dalam Bahasa Indonesia

---

## Referensi & Inspirasi

- [Phidata Documentation](https://docs.phidata.com)
- [Ollama Model Library](https://ollama.ai/library)
- [Groq Console](https://console.groq.com)
- [Nvidia NIM](https://build.nvidia.com)
- [Google AI Studio](https://aistudio.google.com)
- [HuggingFace Models](https://huggingface.co/models)
- [AMD Developer Hackathon - lablab.ai](https://lablab.ai)

---

## Lisensi

Proyek personal untuk pembelajaran dan pengembangan diri. Gunakan secara bebas untuk inspirasi dan referensi.

---

<p align="center">
  <i>"Sometimes you gotta run before you can walk."</i><br>
  <b>- Tony Stark</b>
</p>

<p align="center">
  Built with determination, creativity, and zero budget.<br>
  <b>PRE-AIAgentJarvis</b> - The journey to build a personal AI assistant.
</p>
