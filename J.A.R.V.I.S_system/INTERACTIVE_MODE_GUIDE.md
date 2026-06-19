# 🤖 J.A.R.V.I.S Interactive Chatbot Mode - User Guide

## Apa Itu?

J.A.R.V.I.S sekarang beroperasi dalam **INTERACTIVE CHATBOT MODE**, artinya:

✅ Program tetap berjalan di terminal setelah menjalankan satu perintah  
✅ Bisa menerima input baru secara langsung tanpa restart  
✅ Bisa disapa casual ("halo", "hai", dll)  
✅ Punya akses penuh ke AI Agent tools untuk automatisasi  
✅ Seperti percakapan dengan human, tapi dengan AI agent capabilities  

---

## Cara Menjalankan

### Method 1: Dengan Helper Script (Recommended)
```bash
cd C:\Users\aflah\Downloads\agentPremium\J.A.R.V.I.S_system
python run_jarvis.py
```

### Method 2: Direct Run
```bash
python jarvis_coder.py
```

---

## Contoh Penggunaan

### Session Contoh:

```
======================================================================
J.A.R.V.I.S AUTONOMOUS SELF-HEALING CODING AGENT v2.0
Interactive Mode - Chatbot dengan AI Agent Capabilities
======================================================================

📝 Commands:
  • Type anything to chat or give instructions
  • Examples: 'halo', 'perbaiki test.py', 'buat file baru', etc
  • 'help' - Show available commands
  • 'tools' - Show available tools
  • 'clear' - Clear screen
  • 'exit' or 'quit' - Exit program

----------------------------------------------------------------------

📌 You: halo

🤖 J.A.R.V.I.S: Halo! Saya J.A.R.V.I.S, AI Agent yang siap membantu 
tugas coding Anda. Apa yang bisa saya bantu hari ini? 😊

📌 You: perbaiki file test.py yang punya bug

🤖 J.A.R.V.I.S: [Menggunakan tools untuk membaca, analisis, patch, 
dan validasi file test.py]

Diperbaiki file test.py dengan memperbaiki:
- Line 5: Tambah validasi list kosong
- Line 12: Initialize risk_score = 0.0
- Line 25: Add default else case

Hasil eksekusi: SUCCESS ✓

📌 You: list semua file di folder

🤖 J.A.R.V.I.S: [Menampilkan daftar file di current directory]

File yang ada:
- jarvis_coder.py (8KB)
- test.py (1.2KB) 
- utils.py (3KB)
- data.json (5KB)

📌 You: buat file baru bernama hello.py dengan content "print('Hello World')"

🤖 J.A.R.V.I.S: [Membuat file hello.py]

File hello.py berhasil dibuat. Isi: print('Hello World')

📌 You: jalankan hello.py

🤖 J.A.R.V.I.S: [Menjalankan file dengan execute_python_script]

Output:
Hello World
[EXIT CODE: 0] ✓

📌 You: exit

👋 Goodbye! J.A.R.V.I.S signing off...
```

---

## Perintah Khusus

| Command | Fungsi |
|---------|--------|
| `help` | Tampilkan help menu lengkap |
| `tools` | Tampilkan daftar tools yang tersedia |
| `clear` | Clear screen |
| `exit` atau `quit` | Keluar dari program |
| `halo`, `hai`, `hello` | Sapa J.A.R.V.I.S |

---

## Contoh Instruksi Praktis

### 1. File Reading & Inspection
```
📌 You: baca file utils.py

📌 You: lihat semua file di folder

📌 You: cek isi file test.py
```

### 2. Code Fixing & Debugging
```
📌 You: perbaiki file dengan nama script.py yang error

📌 You: debug function calculate_average di test.py

📌 You: ada bug di line 5, tolong perbaiki
```

### 3. File Creation & Modification
```
📌 You: buat file baru bernama config.py

📌 You: tambahkan function get_config ke file config.py

📌 You: edit line 10 di test.py, ubah nilai x menjadi 100
```

### 4. Code Execution & Testing
```
📌 You: jalankan file main.py

📌 You: test file hello.py dan pastikan tidak ada error

📌 You: eksekusi script.py dan tampilkan outputnya
```

### 5. Multi-Step Tasks
```
📌 You: baca file test.py, identifikasi bugs, perbaiki, 
        jalankan, dan lapor hasilnya

📌 You: refactor function calculate_average di test.py
```

---

## Fitur Chatbot

### Casual Conversation
```
📌 You: halo
🤖 J.A.R.V.I.S: Halo! Saya J.A.R.V.I.S, AI Agent yang siap membantu...

📌 You: apa kabar?
🤖 J.A.R.V.I.S: Saya siap membantu dengan tugas coding Anda! 😊
```

### Autonomous Task Execution
```
📌 You: perbaiki file test.py

🤖 J.A.R.V.I.S: [Otomatis membaca file]
[Menganalisis code]
[Menemukan 3 bugs]
[Membuat fixes]
[Menjalankan test]
[Validasi output]

Status: SUCCESS ✓
```

### Self-Healing on Errors
```
📌 You: jalankan script.py

🤖 J.A.R.V.I.S: [Menjalankan]
❌ Error: UnboundLocalError at line 5

[Otomatis membaca error]
[Menganalisis masalah]
[Membuat fix]
[Re-run]

✓ SUCCESS
```

---

## Tools yang Tersedia

J.A.R.V.I.S punya akses ke:

### File Tools (dari local_file_bridge)
- `read_file(path)` - Baca file
- `save_file(path, content)` - Simpan/buat file
- `list_files()` - Lihat semua file
- `edit_file(path, find, replace)` - Edit file

### Python Execution
- `execute_python_script(filename)` - Jalankan Python script
- Capture stdout, stderr, exit code
- Timeout 30 detik

### AI Agent Capabilities
- Autonomous code analysis
- Self-healing loops
- Multi-step task execution
- Error detection & fixing

---

## Tips & Tricks

### ✅ DO's
- ✓ Berikan instruksi yang jelas dan spesifik
- ✓ Gunakan bahasa casual dan natural
- ✓ Sebutkan nama file atau baris code jika perlu
- ✓ Tunggu agent selesai sebelum input baru

### ❌ DON'Ts
- ✗ Jangan tekan Ctrl+C di tengah operasi (tunggu selesai)
- ✗ Jangan coba paste ratusan baris code sekali
- ✗ Jangan ubah file dari aplikasi lain sambil agent bekerja

---

## Troubleshooting

### Program tidak merespons
- Tunggu beberapa detik (API mungkin sedang processing)
- Jika tetap stuck, tekan Ctrl+C dan restart

### Error: API key invalid
- Verify OPENAI_API_KEY di jarvis_coder.py
- Check internet connection
- Tunggu dan retry (API mungkin down)

### File not found error
- Pastikan file ada di working directory
- Use `tools` command untuk lihat tersedia files
- Sebutkan path lengkap jika file di subfolder

### Exit code non-zero
- Agent akan otomatis self-heal dan retry
- Check error message di console
- Validate file syntax sebelum exec

---

## Session Example

```bash
$ python jarvis_coder.py

======================================================================
J.A.R.V.I.S AUTONOMOUS SELF-HEALING CODING AGENT v2.0
Interactive Mode - Chatbot dengan AI Agent Capabilities
======================================================================

📝 Commands:
  • Type anything to chat or give instructions
  ...

----------------------------------------------------------------------

📌 You: help
[Display help menu]

📌 You: halo
🤖 J.A.R.V.I.S: Halo! Saya J.A.R.V.I.S...

📌 You: buat file test_hello.py dengan isi print('hello world')
🤖 J.A.R.V.I.S: [Create file]
File berhasil dibuat!

📌 You: jalankan test_hello.py
🤖 J.A.R.V.I.S: [Execute file]
hello world
[EXIT CODE: 0] ✓

📌 You: exit
👋 Goodbye! J.A.R.V.I.S signing off...
```

---

## Notes

- Program tetap active di terminal sampai Anda ketik `exit`
- Setiap input diproses oleh AI Agent dengan full tool access
- Self-healing otomatis jika ada error saat eksekusi
- Output minimal & focused (tidak spam chat)
- Perfect untuk interactive development & testing

---

**Enjoy chatting dengan J.A.R.V.I.S!** 🚀
