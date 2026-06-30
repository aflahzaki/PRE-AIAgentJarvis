# J.A.R.V.I.S - Just A Rather Very Intelligent System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active%20Development-orange)
![Agents](https://img.shields.io/badge/AI%20Agents-7-purple)
![Tools](https://img.shields.io/badge/Tools-33-red)

> **AI Assistant pribadi yang terinspirasi dari J.A.R.V.I.S milik Tony Stark (Iron Man),
> dibangun sepenuhnya GRATIS tanpa budget menggunakan model open-source dan free-tier API.**

---

## Visi Proyek

J.A.R.V.I.S adalah sistem AI multi-agent yang dirancang untuk menjadi asisten pribadi
all-in-one. Tidak seperti ChatGPT atau layanan berbayar lainnya, J.A.R.V.I.S:

- **100% Gratis** - Menggunakan Ollama (local), Groq free tier, Gemini free tier, dan OpenRouter free models
- **Multi-Agent** - 7 agen AI spesialis yang bekerja secara otonom
- **Multi-Interface** - Akses via Terminal, Web Dashboard, Telegram Bot, atau Voice
- **Self-Healing** - Agent secara otomatis memperbaiki error dan retry
- **Privacy-First** - Data tersimpan lokal di database kamu sendiri
- **Extensible** - Arsitektur plugin-based, mudah ditambah agent/tool baru

---

## Fitur Utama

| Kategori | Detail |
|----------|--------|
| AI Agents | 7 agen spesialis (Coder, Researcher, Web Search, Data Analyst, Scheduler, Writer, Life Assistant) |
| LLM Providers | 4 provider (Ollama local, Groq cloud, Gemini cloud, OpenRouter cloud) |
| Access Interfaces | 5 cara akses (Terminal REPL, Web Dashboard, Telegram Bot, Voice, Proactive Engine) |
| Database | 6 tabel (tasks, knowledge, conversations, journals, habits, habit_logs) |
| Tools | 33 registered tools (file ops, code execution, web search, data analysis, dll) |
| Cognitive | Chain-of-Thought, Planning, Self-Reflection, Error Learning |
| Knowledge | RAG Pipeline + File Upload (PDF, DOCX, TXT) |
| Performance | Response Caching + Agent Memory |
| Security | Code Sandbox + Web Authentication + Token-based Auth |
| Monitoring | Analytics Dashboard + Health Monitoring |
| Proactive | Background engine dengan triggers otomatis |

---

## Arsitektur Sistem

```
                         J.A.R.V.I.S System Architecture

    +------------------+     +------------------+     +------------------+
    |    Terminal       |     |   Web Dashboard  |     |   Telegram Bot   |
    |   (run_jarvis    |     |    (run_web.py)  |     |  (run_telegram   |
    |     _v2.py)      |     |   localhost:8000 |     |      .py)        |
    +--------+---------+     +--------+---------+     +--------+---------+
             |                        |                        |
    +--------+---------+     +--------+---------+              |
    |  Voice Interface |     | Proactive Engine |              |
    |  (run_voice.py)  |     |   (Background)   |              |
    +--------+---------+     +--------+---------+              |
             |                        |                        |
             +------------------------+------------------------+
                                      |
                                      v
                        +-------------+-------------+
                        |        ORCHESTRATOR       |
                        |   (Task Classification)   |
                        |   (Conversation Memory)   |
                        |   (RAG Context Injection) |
                        +-------------+-------------+
                                      |
                          +-----------+-----------+
                          |                       |
                          v                       v
              +-----------+--------+    +---------+---------+
              |    MODEL ROUTER    |    |  THINKING ENGINE  |
              | (Difficulty-based) |    |  (CoT, Planning,  |
              | (Smart Fallback)   |    |   Reflection)     |
              +-----------+--------+    +-------------------+
                          |
            +-------------+-------------+-------------+
            |             |             |             |
            v             v             v             v
      +-----+----+ +-----+----+ +-----+----+ +------+-----+
      |  Ollama  | |   Groq   | |  Gemini  | | OpenRouter |
      |  (Local) | |  (Cloud) | |  (Cloud) | |  (Cloud)   |
      +----------+ +----------+ +----------+ +------------+
                          |
                          v
     +----+----+----+----+----+----+----+
     |    |    |    |    |    |    |    |
     v    v    v    v    v    v    v    v
   Code Rsrch  Web  Data Schd Wrtr Life Simple
   Agent Agent Srch Anlys Agent Agent Asst Response
     |    |    |    |    |    |    |
     v    v    v    v    v    v    v
   +---+ +--+ +--+ +--+ +--+ +--+ +--+
   |T  | |  | |S | |D | |S | |W | |K |
   |o  | |  | |e | |a | |c | |r | |n |
   |o  | |  | |a | |t | |h | |i | |o |
   |l  | |  | |r | |a | |e | |t | |w |
   |s  | |  | |c | |  | |d | |e | |l |
   +---+ +--+ |h | |T | |u | |  | |e |
              +--+ |o | |l | |T | |d |
                   |o | |e | |o | |g |
                   |l | |r | |o | |e |
                   |s | |  | |l | |  |
                   +--+ +--+ |s | +--+
                              +--+
```

### Flow Sederhana:

```
User Input -> Interface -> Orchestrator -> classify_task()
          -> Model Router -> select provider/model
          -> Agent (with tools) -> execute & self-heal
          -> Response + Memory + Analytics
```

---

## Daftar Agent

| # | Agent | Fungsi | Tools | Contoh Perintah |
|---|-------|--------|-------|-----------------|
| 1 | **Coder Agent** | Menulis, debug, dan eksekusi kode secara otonom | `read_file`, `write_file`, `edit_file`, `list_files`, `execute_python`, `execute_sandboxed`, `check_code_safety` | "Buatkan script Python untuk scraping data" |
| 2 | **Researcher Agent** | Analisis mendalam, critical thinking, perbandingan | *(reasoning-based, no tools)* | "Bandingkan React vs Vue untuk proyek enterprise" |
| 3 | **Web Search Agent** | Pencarian internet real-time, verifikasi fakta | `search_web`, `search_news`, `get_page_summary` | "Cari berita terbaru tentang AI di Indonesia" |
| 4 | **Data Analyst Agent** | Analisis data, statistik, insight generation | `read_csv_file`, `describe_data`, `filter_data`, `calculate_stats`, `execute_python_code` | "Analisis file sales.csv dan beri insight" |
| 5 | **Scheduler Agent** | Manajemen task, deadline, dan reminder | `add_task`, `list_tasks`, `update_task`, `complete_task`, `get_overdue_tasks`, `get_today_tasks` | "Tambahkan deadline skripsi hari Jumat" |
| 6 | **Writer Agent** | Penulisan email, proposal, caption, artikel | `email_template`, `proposal_template`, `caption_template`, `format_academic`, `format_casual` | "Buatkan email formal ke dosen pembimbing" |
| 7 | **Life Assistant Agent** | Bantuan keputusan, wellness, habit tracking | `add_task`, `list_tasks`, `complete_task`, `get_today_tasks`, `add_knowledge`, `search_knowledge`, `get_knowledge_by_category`, `delete_knowledge` | "Aku bingung pilih jurusan, bantu aku" |

---

## Daftar LLM Provider

| # | Provider | Tipe | Model Default | Free Tier | Keterangan |
|---|----------|------|---------------|-----------|------------|
| 1 | **Ollama** | Local | `llama3.2:3b` (easy), `qwen2.5-coder:7b` (medium) | Unlimited (local) | Install dari ollama.ai, jalan di PC sendiri |
| 2 | **Groq** | Cloud | `llama-3.3-70b-versatile` | ~30 req/menit, 14.400/hari | Tercepat, recommended untuk mulai |
| 3 | **Gemini** | Cloud | `gemini-2.0-flash` | 15 req/menit, 1500/hari | Google AI Studio, sangat generous |
| 4 | **OpenRouter** | Cloud | `meta-llama/llama-3.3-70b-instruct:free` | Varies per model | Aggregator, banyak free model |

### Fallback Logic:

```
EASY task:   Ollama small -> Ollama medium -> Groq -> Gemini -> OpenRouter
MEDIUM task: Ollama medium -> Groq -> Gemini -> OpenRouter
HARD task:   Groq -> Gemini -> OpenRouter -> Ollama medium
```

Jika satu provider down atau rate-limited, sistem otomatis fallback ke provider berikutnya.

---

## Daftar Interface

### 1. Terminal REPL (`run_jarvis_v2.py`)
- Interface utama dengan Rich formatting
- Autocomplete dan syntax highlighting
- Commands: `/status`, `/clear`, `/export`, `/refresh`, `/help`

### 2. Web Dashboard (`run_web.py`)
- FastAPI backend di `localhost:8000`
- Real-time chat interface
- Task management panel
- Knowledge base browser
- Journal & habit tracker
- Analytics dashboard
- Optional authentication (token-based)

### 3. Telegram Bot (`run_telegram.py`)
- Chat dengan J.A.R.V.I.S langsung dari Telegram
- Inline buttons untuk quick actions
- User whitelist untuk keamanan
- Semua fitur agent tersedia

### 4. Voice Interface (`run_voice.py`)
- Speech-to-Text via Faster Whisper
- Text-to-Speech via Edge TTS
- Hands-free interaction
- Configurable language dan voice

### 5. Proactive Engine (Background)
- Berjalan di background thread
- Notifikasi otomatis berdasarkan triggers
- Tidak perlu user input untuk aktif

---
## Quick Start (Step-by-Step)

### Prerequisites

| Requirement | Keterangan |
|-------------|------------|
| Python 3.8+ | Wajib. Cek: `python --version` |
| pip | Wajib. Package manager Python |
| Git | Wajib. Untuk clone repository |
| XAMPP/MySQL | Opsional. Untuk persistent database (fallback SQLite tersedia) |
| Ollama | Opsional. Untuk menjalankan LLM secara lokal |

### Step 1: Clone Repository

```bash
git clone https://github.com/aflahzaki/PRE-AIAgentJarvis.git
cd PRE-AIAgentJarvis/J.A.R.V.I.S_system
```

### Step 2: Install Dependencies

```bash
pip install -r requirements_v2.txt
```

### Step 3: Jalankan Setup Wizard

```bash
python setup_jarvis.py
```

Setup wizard akan:
- Cek sistem (Python, OS, RAM)
- Install dependencies yang missing
- Guide setup Ollama (opsional)
- Buat file `.env` dari template
- Setup database (MySQL atau SQLite fallback)
- Test koneksi ke providers

### Step 4: Konfigurasi API Keys

Edit file `.env` dan isi minimal satu provider:

```bash
# RECOMMENDED: Groq (gratis, cepat, mudah)
# Daftar di: https://console.groq.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx

# ALTERNATIVE: Google Gemini (gratis)
# Daftar di: https://aistudio.google.com/apikey
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxx

# ALTERNATIVE: OpenRouter (banyak free model)
# Daftar di: https://openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxx
```

### Step 5: Jalankan J.A.R.V.I.S

```bash
# Terminal mode (recommended untuk pertama kali)
python run_jarvis_v2.py

# Web dashboard
python run_web.py

# Telegram bot
python run_telegram.py

# Voice interface
python run_voice.py

# Semua sekaligus
python run_all.py
```

---

## Mode Penggunaan

### Contoh Percakapan - Coding

```
You: Buatkan script Python untuk download semua gambar dari sebuah website

J.A.R.V.I.S [Coder Agent]: Saya akan buatkan script web scraper untuk
download gambar. Menggunakan requests + BeautifulSoup...

[Tool Call: write_file("image_downloader.py", ...)]
[Tool Call: execute_python("image_downloader.py")]

Script berhasil dibuat dan ditest. File tersimpan di image_downloader.py
```

### Contoh Percakapan - Research

```
You: Bandingkan FastAPI vs Django untuk REST API di 2024

J.A.R.V.I.S [Researcher Agent]:
## Perbandingan FastAPI vs Django REST Framework

### Performance
- FastAPI: async-native, ~15x lebih cepat dari Django...
- Django: synchronous by default, tapi mature ecosystem...

### Kesimpulan
Untuk microservice/API-first: FastAPI
Untuk full-stack dengan admin: Django
```

### Contoh Percakapan - Web Search

```
You: Cari berita terbaru tentang AI regulation di Indonesia

J.A.R.V.I.S [Web Search Agent]:
[Tool Call: search_news("AI regulation Indonesia 2024")]

Berikut berita terbaru tentang regulasi AI di Indonesia:
1. [Judul berita] - Sumber, tanggal
2. ...
```

### Contoh Percakapan - Task Management

```
You: Tambahkan deadline skripsi bab 3 hari Jumat, prioritas tinggi

J.A.R.V.I.S [Scheduler Agent]:
[Tool Call: add_task("Skripsi Bab 3", priority="high", due_date="...")]

Task berhasil ditambahkan!
- Title: Skripsi Bab 3
- Priority: HIGH
- Due: Jumat, ...
```

### Contoh Percakapan - Writing

```
You: Buatkan email formal ke dosen untuk minta bimbingan skripsi

J.A.R.V.I.S [Writer Agent]:
[Tool Call: email_template("formal", ...)]

Subject: Permohonan Bimbingan Skripsi

Yth. Bapak/Ibu [Nama Dosen],
Dengan hormat, ...
```

### Contoh Percakapan - Life Assistant

```
You: Aku bingung mau pilih magang di startup atau perusahaan besar

J.A.R.V.I.S [Life Assistant]:
Saya pahami dilema ini. Mari kita breakdown:

**Startup:**
+ Learning curve tinggi, exposure luas
+ Ownership dan impact langsung terasa
- Risiko lebih tinggi, less structured

**Perusahaan Besar:**
+ Brand name di CV, mentorship terstruktur
+ Stabilitas dan resources
- Scope kerja bisa terbatas

Pertanyaan untuk refleksi: ...
```

---

## Database & phpMyAdmin

### Setup MySQL (via XAMPP)

1. Install dan buka XAMPP Control Panel
2. Start **Apache** dan **MySQL**
3. Buka phpMyAdmin: `http://localhost/phpmyadmin`
4. Buat database baru: `jarvis_db`
5. J.A.R.V.I.S akan otomatis create tabel saat pertama kali jalan

### Konfigurasi di .env:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=jarvis_db
DB_FALLBACK_SQLITE=true
```

### Daftar Tabel

| Tabel | Fungsi | Kolom Utama |
|-------|--------|-------------|
| `tasks` | Task management & reminders | id, title, description, priority, status, due_date, reminder_at |
| `knowledge` | Knowledge base entries | id, title, content, category, tags, source |
| `conversations` | Chat history log | id, session_id, role, content, agent_used, model_used, provider_used |
| `journals` | Daily journal & mood | id, date, mood, content, highlights, challenges, tomorrow_plan |
| `habits` | Habit definitions | id, name, frequency, target_count, is_active |
| `habit_logs` | Daily habit completion | id, habit_id, logged_date, count, notes |

### SQLite Fallback

Jika MySQL tidak tersedia dan `DB_FALLBACK_SQLITE=true`, sistem otomatis
menggunakan SQLite (file: `data/jarvis.db`). Tidak perlu setup apapun.

---
## Konfigurasi (.env)

Salin `.env.example` ke `.env` dan sesuaikan:

```bash
cp .env.example .env
```

### LLM Providers

| Variable | Keterangan | Default |
|----------|------------|---------|
| `OLLAMA_BASE_URL` | URL Ollama server | `http://localhost:11434/v1` |
| `OLLAMA_MODEL_SMALL` | Model untuk task mudah | `llama3.2:3b` |
| `OLLAMA_MODEL_MEDIUM` | Model untuk task medium | `qwen2.5-coder:7b` |
| `GROQ_API_KEY` | API key Groq | - |
| `GROQ_MODEL` | Model Groq | `llama-3.3-70b-versatile` |
| `GEMINI_API_KEY` | API key Google Gemini | - |
| `GEMINI_MODEL` | Model Gemini | `gemini-2.0-flash` |
| `OPENROUTER_API_KEY` | API key OpenRouter | - |
| `OPENROUTER_MODEL` | Model OpenRouter | `meta-llama/llama-3.3-70b-instruct:free` |

### Database

| Variable | Keterangan | Default |
|----------|------------|---------|
| `DB_HOST` | MySQL host | `localhost` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_USER` | MySQL username | `root` |
| `DB_PASSWORD` | MySQL password | *(kosong)* |
| `DB_NAME` | Nama database | `jarvis_db` |
| `DB_FALLBACK_SQLITE` | Fallback ke SQLite jika MySQL gagal | `true` |

### Interfaces

| Variable | Keterangan | Default |
|----------|------------|---------|
| `WEB_HOST` | Web dashboard host | `0.0.0.0` |
| `WEB_PORT` | Web dashboard port | `8000` |
| `WEB_AUTH_ENABLED` | Aktifkan web authentication | `false` |
| `WEB_AUTH_TOKEN` | Token untuk web auth | - |
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram (dari @BotFather) | - |
| `TELEGRAM_ALLOWED_USERS` | Chat ID yang diizinkan | - |
| `VOICE_MODEL` | Model Whisper (base/small/medium/large) | `base` |
| `VOICE_LANGUAGE` | Bahasa voice recognition | `en` |
| `TTS_VOICE` | Voice untuk Text-to-Speech | `en-US-AriaNeural` |

### Features

| Variable | Keterangan | Default |
|----------|------------|---------|
| `PROACTIVE_ENABLED` | Aktifkan proactive engine | `false` |
| `PROACTIVE_INTERVAL_MINUTES` | Interval cek triggers (menit) | `15` |
| `RAG_ENABLED` | Aktifkan RAG pipeline | `true` |
| `EMBEDDING_MODEL` | Model embedding (tfidf/sentence_transformer) | `tfidf` |
| `RAG_TOP_K` | Jumlah dokumen relevan yang di-retrieve | `5` |
| `CACHE_ENABLED` | Aktifkan response caching | `true` |
| `CACHE_TTL_SECONDS` | Cache time-to-live (detik) | `3600` |
| `CACHE_MAX_SIZE` | Maksimum cache entries | `100` |
| `SANDBOX_STRICT_MODE` | Block kode berbahaya (bukan hanya warning) | `false` |

---

## Cognitive Features

J.A.R.V.I.S memiliki **ThinkingEngine** yang memberikan kemampuan kognitif tambahan:

### 1. Chain-of-Thought (CoT)
- Scaled berdasarkan difficulty level
- **Easy**: Tidak ada overhead (direct response)
- **Medium**: Brief 2-line thinking instruction
- **Hard**: Full reasoning chain dengan structured thinking

### 2. Multi-Step Planning
- Untuk task kompleks, agent membuat rencana step-by-step sebelum eksekusi
- Setiap step di-validate sebelum lanjut ke step berikutnya
- Planning prompt di-inject ke system message

### 3. Self-Reflection
- Setelah memberikan jawaban, agent melakukan self-check
- Memastikan jawaban akurat, lengkap, dan relevan
- Reflection prompt mendorong agent untuk mengakui keterbatasan

### 4. Error Learning
- Setiap error yang terjadi di-log ke `data/cognition/error_log.json`
- Maksimum 100 entries (auto-prune oldest)
- Error context di-inject ke prompt agar agent tidak mengulangi kesalahan yang sama
- Agent belajar dari past failures secara otomatis

---

## Knowledge Base & RAG

### Cara Upload File

Via Web Dashboard:
1. Buka `http://localhost:8000`
2. Navigasi ke tab **Knowledge**
3. Klik **Upload** dan pilih file (PDF, DOCX, TXT)
4. File akan di-parse dan di-index secara otomatis

Via API:
```bash
curl -X POST http://localhost:8000/api/knowledge/upload \
  -F "file=@dokumen.pdf"
```

### Cara Search Knowledge

Knowledge base otomatis di-query setiap kali user bertanya (RAG pipeline):

```
User: Apa itu design pattern singleton?

[RAG: Searching knowledge base...]
[Found 3 relevant entries]

J.A.R.V.I.S: Berdasarkan knowledge base kamu + pengetahuan saya:
Singleton pattern adalah...
```

### Embedding Models

| Model | Kelebihan | Kekurangan |
|-------|-----------|------------|
| `tfidf` (default) | Ringan, no download, cepat | Hanya keyword matching |
| `sentence_transformer` | Semantic similarity, lebih akurat | Download ~90MB model pertama kali |

Untuk upgrade ke sentence_transformer:
```bash
pip install sentence-transformers
# Edit .env:
EMBEDDING_MODEL=sentence_transformer
```

---

## Proactive Engine

Proactive Engine adalah background service yang berjalan otomatis dan memberikan
notifikasi tanpa perlu user bertanya.

### Triggers yang Tersedia

| Trigger | Fungsi | Kapan Aktif |
|---------|--------|-------------|
| `check_overdue_tasks` | Deteksi task yang melewati deadline | Setiap interval |
| `check_unlogged_habits` | Habit yang belum di-log hari ini | Setiap interval |
| `check_upcoming_deadlines` | Task yang due dalam 24 jam | Setiap interval |
| `daily_summary` | Ringkasan task hari ini | Pagi hari |
| `mood_check` | Reminder jurnal jika belum ditulis | Siang/sore hari |

### Cara Mengaktifkan

```env
# Di file .env:
PROACTIVE_ENABLED=true
PROACTIVE_INTERVAL_MINUTES=15
```

Notifikasi dikirim via:
- Console (Terminal mode)
- Telegram (jika bot token dikonfigurasi)

---

## Analytics Dashboard

J.A.R.V.I.S mencatat statistik penggunaan secara otomatis:

### Metrics yang Di-track

| Metric | Keterangan |
|--------|------------|
| Requests per day/hour | Volume penggunaan harian |
| Agent usage distribution | Agent mana yang paling sering dipakai |
| Provider usage distribution | Provider mana yang paling aktif |
| Model usage distribution | Model mana yang digunakan |
| Average response time | Rata-rata waktu respons (ms) |
| Token consumption | Pemakaian token per provider |
| Cache hit rate | Persentase response dari cache |
| Error rate per provider | Provider mana yang sering error |

### Health Monitoring

Background daemon thread yang cek provider availability setiap 5 menit:
- Auto-detect provider yang down
- Logging latency per provider
- Status tersedia via `/status` command atau Web Dashboard

Data disimpan di: `data/analytics/analytics_YYYY-MM-DD.json`

---
## Security

### Code Sandbox
- Semua eksekusi kode user melewati safety checker
- Pattern berbahaya dideteksi: `os.system`, `subprocess`, `shutil.rmtree`, `eval`, dll
- Mode **warning** (default): Log warning tapi tetap jalankan
- Mode **strict** (`SANDBOX_STRICT_MODE=true`): Block eksekusi kode berbahaya
- Timeout execution: mencegah infinite loop
- Output size limit: mencegah memory bomb

### Web Authentication
- Token-based authentication (Bearer token)
- Disable by default untuk kemudahan development
- Static files (login page) selalu accessible
- API routes dilindungi saat auth enabled

```env
WEB_AUTH_ENABLED=true
WEB_AUTH_TOKEN=your-strong-secret-token-here
```

### Telegram User Whitelist
- Hanya chat ID yang terdaftar yang bisa interact dengan bot
- Konfigurasi: `TELEGRAM_ALLOWED_USERS=123456789`

### Environment Variable Sanitization
- API keys tidak di-pass ke executed user code
- Database credentials terisolasi dari sandbox

---

## Struktur Folder Lengkap

```
PRE-AIAgentJarvis/
|
|-- J.A.R.V.I.S_system/                  # Sistem utama
|   |-- core/                            # Core engine
|   |   |-- agents/                      # 7 AI agents
|   |   |   |-- base_agent.py            # Abstract base + self-healing loop
|   |   |   |-- coder_agent.py           # Coding & file manipulation
|   |   |   |-- researcher_agent.py      # Critical thinking & analysis
|   |   |   |-- web_search_agent.py      # Internet research
|   |   |   |-- data_analyst_agent.py    # Data analysis & stats
|   |   |   |-- scheduler_agent.py       # Task & time management
|   |   |   |-- writer_agent.py          # Content writing
|   |   |   |-- life_assistant_agent.py  # Personal wellness
|   |   |
|   |   |-- analytics/                   # Usage tracking
|   |   |   |-- analytics_tracker.py     # JSON-based stats recorder
|   |   |   |-- health_monitor.py        # Provider health checker
|   |   |
|   |   |-- cognition/                   # Cognitive enhancement
|   |   |   |-- thinking.py              # CoT, Planning, Reflection, Error Learning
|   |   |
|   |   |-- database/                    # Database layer
|   |   |   |-- db_manager.py            # Connection & session management
|   |   |   |-- models.py                # 6 SQLAlchemy ORM models
|   |   |   |-- migrations.py            # Schema migrations
|   |   |
|   |   |-- knowledge/                   # Knowledge & RAG
|   |   |   |-- knowledge_base.py        # Knowledge CRUD
|   |   |   |-- embeddings.py            # TF-IDF & sentence-transformer
|   |   |   |-- rag_engine.py            # RAG pipeline
|   |   |   |-- document_loader.py       # PDF/DOCX/TXT parser
|   |   |
|   |   |-- memory/                      # Memory systems
|   |   |   |-- conversation.py          # Conversation buffer & summary
|   |   |   |-- cache.py                 # Response caching
|   |   |   |-- agent_memory.py          # Per-agent persistent memory
|   |   |
|   |   |-- plugins/                     # Plugin system
|   |   |   |-- plugin_loader.py         # Dynamic plugin loading
|   |   |
|   |   |-- protocols/                   # Communication protocols
|   |   |   |-- agent_protocol.py        # Agent communication protocol
|   |   |   |-- task_queue.py            # Async task queue
|   |   |
|   |   |-- providers/                   # LLM providers
|   |   |   |-- base_provider.py         # Abstract provider interface
|   |   |   |-- ollama_provider.py       # Local Ollama
|   |   |   |-- groq_provider.py         # Groq cloud
|   |   |   |-- gemini_provider.py       # Google Gemini
|   |   |   |-- openrouter_provider.py   # OpenRouter aggregator
|   |   |
|   |   |-- tools/                       # Agent tools (33 total)
|   |   |   |-- file_tools.py            # read, write, edit, list files
|   |   |   |-- python_executor.py       # Safe code execution
|   |   |   |-- sandbox.py               # Sandboxed execution + safety
|   |   |   |-- web_search.py            # DuckDuckGo search
|   |   |   |-- data_tools.py            # CSV/JSON data tools
|   |   |   |-- scheduler_tools.py       # Task CRUD
|   |   |   |-- knowledge_tools.py       # Knowledge CRUD
|   |   |   |-- writing_tools.py         # Email/proposal/caption templates
|   |   |   |-- upload_tools.py          # File upload handling
|   |   |
|   |   |-- utils/                       # Utilities
|   |   |   |-- export.py                # Session export
|   |   |   |-- model_manager.py         # Model download suggestions
|   |   |
|   |   |-- model_router.py              # Smart model routing
|   |   |-- orchestrator.py              # Main brain/coordinator
|   |
|   |-- interfaces/                      # Access interfaces
|   |   |-- web_dashboard/               # FastAPI web UI
|   |   |   |-- app.py                   # FastAPI application
|   |   |   |-- auth.py                  # Token authentication
|   |   |   |-- database.py              # Web-specific DB helpers
|   |   |   |-- routes/                  # API routes
|   |   |   |   |-- chat.py              # Chat endpoints
|   |   |   |   |-- tasks.py             # Task management
|   |   |   |   |-- knowledge.py         # Knowledge base
|   |   |   |   |-- journals.py          # Journal entries
|   |   |   |   |-- habits.py            # Habit tracking
|   |   |   |   |-- analytics.py         # Analytics data
|   |   |   |   |-- status.py            # System status
|   |   |   |-- static/                  # Frontend files
|   |   |       |-- index.html           # Main page
|   |   |       |-- style.css            # Styling
|   |   |       |-- app.js               # Frontend logic
|   |   |
|   |   |-- telegram_bot/                # Telegram interface
|   |   |   |-- bot.py                   # Bot initialization
|   |   |   |-- handlers.py              # Message handlers
|   |   |
|   |   |-- voice/                       # Voice interface
|   |   |   |-- voice_interface.py       # Main voice loop
|   |   |   |-- speech_to_text.py        # Whisper STT
|   |   |   |-- text_to_speech.py        # Edge TTS
|   |   |
|   |   |-- proactive/                   # Proactive engine
|   |       |-- proactive_engine.py      # Background scheduler
|   |       |-- triggers.py              # Notification triggers
|   |       |-- notifications.py         # Notification dispatchers
|   |
|   |-- data/                            # Runtime data (gitignored)
|   |   |-- analytics/                   # Daily analytics JSON
|   |   |-- cache/                       # Response cache
|   |   |-- cognition/                   # Error logs
|   |   |-- agent_memory/                # Agent persistent memory
|   |   |-- jarvis.db                    # SQLite fallback DB
|   |
|   |-- .env.example                     # Template konfigurasi
|   |-- requirements_v2.txt              # Python dependencies
|   |-- setup_jarvis.py                  # Setup wizard
|   |-- run_jarvis_v2.py                 # Terminal REPL
|   |-- run_web.py                       # Web dashboard launcher
|   |-- run_telegram.py                  # Telegram bot launcher
|   |-- run_voice.py                     # Voice interface launcher
|   |-- run_all.py                       # Launch all interfaces
|
|-- 02_web_agent/                        # [Legacy] Groq website generator
|-- 03_skripsi_agent/                    # [Legacy] Thesis writing agent
|-- agentPremium/                        # [Legacy] Premium agent experiments
|-- Dataset Data Sistem Informasi.../    # [Legacy] SNBP PTN dataset
|-- README.md                            # Dokumentasi ini
```

---

## Upgrade Path

J.A.R.V.I.S dirancang agar mudah di-upgrade dari free ke paid tanpa mengubah kode:

### Free Tier (Default)
```env
GROQ_API_KEY=gsk_free_tier_key
GROQ_MODEL=llama-3.3-70b-versatile
```

### Upgrade ke Model Lebih Powerful
```env
# Ganti ke model berbayar di OpenRouter
OPENROUTER_API_KEY=sk-or-paid-key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Atau gunakan OpenAI via Groq-compatible endpoint
# (Cukup ganti key dan model, endpoint tetap sama)
```

### Upgrade Knowledge Base
```env
# Dari keyword search ke semantic search
EMBEDDING_MODEL=sentence_transformer
# Install: pip install sentence-transformers
```

### Upgrade Database
```env
# Dari SQLite ke MySQL/MariaDB
DB_HOST=your-cloud-mysql.host.com
DB_PORT=3306
DB_USER=jarvis_user
DB_PASSWORD=strong_password
DB_NAME=jarvis_production
DB_FALLBACK_SQLITE=false
```

### Upgrade Voice
```bash
# Install voice dependencies
pip install faster-whisper edge-tts sounddevice numpy

# Gunakan model Whisper yang lebih akurat
# .env:
VOICE_MODEL=medium  # atau large untuk akurasi terbaik
```

---
## Troubleshooting

### Common Issues

| Problem | Penyebab | Solusi |
|---------|----------|--------|
| `ModuleNotFoundError` | Dependencies belum terinstall | `pip install -r requirements_v2.txt` |
| `Connection refused (Ollama)` | Ollama belum running | Start Ollama: `ollama serve` |
| `401 Unauthorized (Groq)` | API key salah/expired | Cek key di https://console.groq.com |
| `Rate limit exceeded` | Terlalu banyak request | Tunggu 1 menit, atau ganti provider |
| `Database connection failed` | MySQL belum running | Start XAMPP MySQL, atau set `DB_FALLBACK_SQLITE=true` |
| `No provider available` | Semua provider down | Cek internet, cek API keys, cek Ollama |
| `Telegram bot not responding` | Token/chat ID salah | Verify dengan @BotFather dan @userinfobot |
| `Voice not working` | Dependencies missing | `pip install faster-whisper edge-tts sounddevice numpy` |
| `Permission denied (file)` | Tidak ada write access | Jalankan dari folder yang kamu own |
| `Port 8000 already in use` | Port conflict | Ganti `WEB_PORT` di .env atau kill proses lain |

### Debug Mode

Untuk melihat log detail:

```python
# Di run_jarvis_v2.py, tambahkan di awal:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Reset System

```bash
# Reset conversation memory
# Di terminal J.A.R.V.I.S, ketik:
/clear

# Reset database (hapus semua data)
rm J.A.R.V.I.S_system/data/jarvis.db

# Reset cache
rm -rf J.A.R.V.I.S_system/data/cache/

# Reset analytics
rm -rf J.A.R.V.I.S_system/data/analytics/

# Full reset (semua data runtime)
rm -rf J.A.R.V.I.S_system/data/
```

### Provider Priority Check

```
# Di terminal J.A.R.V.I.S:
/status

# Output menunjukkan provider mana yang available:
# Ollama: Available (local)
# Groq: Available (cloud)
# Gemini: Available (cloud)
# OpenRouter: Unavailable (no key)
```

---

## Legacy Modules

Repository ini juga berisi modul-modul lama dari fase eksperimen sebelumnya:

| Folder | Deskripsi | Status |
|--------|-----------|--------|
| `02_web_agent/` | Agent berbasis Groq untuk generate website otomatis | Archived - digantikan oleh Coder Agent |
| `03_skripsi_agent/` | Agent khusus untuk membantu penulisan skripsi | Archived - digantikan oleh Writer Agent |
| `agentPremium/01_video_clipper_agent/` | Agent untuk memotong dan edit video | Experimental - belum integrated |
| `Dataset Data Sistem Informasi.../` | Dataset SNBP PTN untuk analisis data | Reference data |
| `AMD Developer Hackathon...pdf` | Dokumentasi hackathon | Reference |

> **Note:** Modul-modul legacy ini tidak diperlukan untuk menjalankan J.A.R.V.I.S v2.
> Semua fungsionalitas utama ada di folder `J.A.R.V.I.S_system/`.

---

## Credits & Inspirasi

### Inspirasi
- **J.A.R.V.I.S (Iron Man)** - AI assistant Tony Stark yang menjadi visi utama proyek ini
- **Open-source AI movement** - Komunitas yang membuktikan AI berkualitas bisa gratis
- **Multi-agent systems** - Konsep spesialisasi agent untuk task berbeda

### Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.8+ |
| LLM (Local) | Ollama + Llama 3.2, Qwen 2.5 Coder |
| LLM (Cloud) | Groq, Google Gemini, OpenRouter |
| Web Framework | FastAPI + Uvicorn |
| Database ORM | SQLAlchemy 2.0 |
| Database | MySQL/MariaDB (XAMPP) atau SQLite |
| Terminal UI | Rich |
| Web Search | DuckDuckGo Search |
| Data Analysis | Pandas, Scikit-learn |
| Telegram | python-telegram-bot |
| Voice STT | Faster Whisper |
| Voice TTS | Edge TTS |
| Scheduling | Schedule library |
| Embeddings | TF-IDF (scikit-learn) / Sentence Transformers |

### Dibuat Oleh

**Aflah Zaki** - AI Engineering Enthusiast

- GitHub: [@aflahzaki](https://github.com/aflahzaki)

---

## Lisensi

Proyek ini bersifat open-source untuk tujuan edukasi dan pengembangan pribadi.

---

<p align="center">
  <i>"Sometimes you gotta run before you can walk."</i><br>
  - Tony Stark
</p>
