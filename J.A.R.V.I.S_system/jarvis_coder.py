import os
import subprocess
import sys
import warnings
warnings.filterwarnings("ignore")

from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.tools.file import FileTools

# =====================================================================
# 1. OTENTIKASI NVIDIA BUILD
# =====================================================================
os.environ["OPENAI_API_KEY"] = "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"
os.environ["OPENAI_BASE_URL"] = "https://integrate.api.nvidia.com/v1"

# Memberikan akses folder agar agen bisa membaca, memodifikasi, dan menyimpan file
local_file_bridge = FileTools(
    base_dir=".",
    read_files=True,
    save_files=True,
    list_files=True
)

# =====================================================================
# 2. NATIVE PYTHON TOOL - EXECUTE PYTHON SCRIPT
# =====================================================================
def execute_python_script(file_name: str) -> str:
    """
    Mengeksekusi script Python secara lokal menggunakan subprocess.
    Menangkap stdout dan stderr, mengembalikan hasil sebagai string.

    Args:
        file_name: Nama file Python yang akan dieksekusi (relatif ke current directory)

    Returns:
        String berisi output eksekusi (stdout + stderr) atau pesan error
    """
    try:
        # Validasi file existence
        if not os.path.exists(file_name):
            return f"ERROR: File '{file_name}' tidak ditemukan di current directory."

        # Execute script dengan subprocess
        result = subprocess.run(
            [sys.executable, file_name],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Gabungkan stdout dan stderr
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"

        # Tambahkan exit code untuk konteks
        output += f"\n[EXIT CODE: {result.returncode}]"

        return output if output.strip() else "[Script executed successfully with no output]"

    except subprocess.TimeoutExpired:
        return f"ERROR: Script '{file_name}' timeout (exceeds 30 seconds)"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)}"

# =====================================================================
# 3. AUTONOMOUS SELF-HEALING CODING AGENT
# =====================================================================
jarvis_coder = Agent(
    name="J.A.R.V.I.S Autonomous Self-Healing Coder",
    model=OpenAIChat(id="meta/llama-3.3-70b-instruct"),
    tools=[local_file_bridge, execute_python_script],
    instructions=[
        "Kamu adalah J.A.R.V.I.S, sebuah AI Agent otonom yang sedang berada dalam mode INTERACTIVE CHATBOT.",
        "Kamu siap membantu Fanny dengan tugas coding dan file manipulation dalam mode percakapan real-time.",
        "User bisa memberikan instruksi casual apapun, dan kamu harus membantu dengan sempurna menggunakan tools.",
        "",
        "=== PERILAKU DI INTERACTIVE MODE ===",
        "",
        "[LISTEN & RESPOND]",
        "- Dengarkan instruksi user dengan cermat dalam mode chatbot interaktif",
        "- Bersikap ramah dan responsif terhadap pertanyaan casual",
        "- Jika user menyapa (halo, hai, etc), balas dengan hangat",
        "- JANGAN tutup program atau exit setelah menjalankan instruksi",
        "- Siap menerima instruksi berikutnya",
        "",
        "[EXECUTE TASKS]",
        "- Gunakan tools (read_file, save_file, list_files, execute_python_script) sesuai kebutuhan",
        "- Untuk tugas file: baca → analisis → patch → validasi",
        "- Untuk debugging: identifikasi bug → buat fix → test → validate",
        "- JANGAN menyerah jika ada error, lakukan self-healing loop",
        "",
        "[AUTONOMOUS SELF-HEALING]",
        "- Setelah menulis/memodifikasi file, WAJIB jalankan execute_python_script",
        "- Jika exit code != 0 atau ada error, ulangi [PATCH] → [VALIDATE] loop",
        "- Lakukan berulang kali sampai hasil sempurna (exit code 0)",
        "- JANGAN menyerah atau bilang 'saya tidak bisa'",
        "",
        "[OUTPUT STYLE]",
        "- Output SINGKAT dan FOKUS pada hasil akhir",
        "- Jangan dump ratusan baris kode ke chat",
        "- Berikan ringkasan: apa yang diubah, hasil akhir, status (✓ SUCCESS atau ✗ FAILED)",
        "- Contoh: 'Diperbaiki calculate_average (line 5-10). Eksekusi: SUCCESS ✓'",
        "",
        "[IMPORTANT NOTES]",
        "- Ini adalah mode CHATBOT INTERAKTIF, bukan batch processing",
        "- User akan terus memberikan instruksi berbeda",
        "- Tetap siap untuk instruksi berikutnya tanpa perlu restart",
        "- Jadilah otonom dan proaktif dalam menggunakan tools",
        "- Hanya gunakan tools untuk action nyata, jangan hanya advice",
    ],
    show_tool_calls=True,
    markdown=True,
)

# =====================================================================
# 4. INTERACTIVE CHATBOT MODE - J.A.R.V.I.S REPL
# =====================================================================

def print_welcome():
    """Display welcome message"""
    print("\n" + "=" * 70)
    print("J.A.R.V.I.S AUTONOMOUS SELF-HEALING CODING AGENT v2.0")
    print("Interactive Mode - Chatbot dengan AI Agent Capabilities")
    print("=" * 70)
    print("\n📝 Commands:")
    print("  • Type anything to chat or give instructions")
    print("  • Examples: 'halo', 'perbaiki test.py', 'buat file baru', etc")
    print("  • 'help' - Show available commands")
    print("  • 'tools' - Show available tools")
    print("  • 'clear' - Clear screen")
    print("  • 'exit' or 'quit' - Exit program")
    print("\n" + "-" * 70 + "\n")

def print_help():
    """Display help information"""
    help_text = """
╔════════════════════════════════════════════════════════════════════╗
║                     J.A.R.V.I.S HELP MENU                         ║
╚════════════════════════════════════════════════════════════════════╝

CONTOH PERINTAH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Greetings:
  "halo", "hai", "hello"

File Operations:
  "baca file myfile.py"
  "perbaiki file test.py yang error"
  "lihat semua file di folder"
  "buat file baru dengan nama utils.py"
  "hapus file test.py"

Debugging & Testing:
  "cek error di script.py"
  "jalankan file test.py"
  "debug script.py"
  "perbaiki bug di test.py"

Development:
  "refactor function calculate_average di test.py"
  "tambahkan error handling di script.py"
  "dokumentasi function di test.py"

System:
  "help" - Show ini
  "tools" - Show available tools
  "clear" - Clear screen
  "exit" atau "quit" - Exit program

TIPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Berbicara casual, tidak perlu formal
✓ Agent akan otomatis menggunakan tools yang dibutuhkan
✓ Untuk multi-baris input, gunakan triple quotes (''')
✓ Agent akan self-heal jika ada error

"""
    print(help_text)

def print_tools():
    """Display available tools"""
    tools_text = """
╔════════════════════════════════════════════════════════════════════╗
║                   AVAILABLE TOOLS & CAPABILITIES                  ║
╚════════════════════════════════════════════════════════════════════╝

🔧 FILE TOOLS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ read_file(path)          - Baca isi file
  ✓ save_file(path, content) - Simpan/buat file
  ✓ list_files()             - Lihat semua file di folder
  ✓ edit_file(path, ...)     - Edit file (find & replace)

🐍 PYTHON EXECUTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ execute_python_script(file_name) - Jalankan script Python
  ✓ Capture stdout & stderr
  ✓ Return exit code
  ✓ Timeout: 30 detik

🧠 AGENT CAPABILITIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ [LISTEN]        - Terima instruksi casual
  ✓ [READ]          - Baca kode sumber
  ✓ [ANALYZE]       - Analisis problem
  ✓ [PATCH]         - Perbaiki kode
  ✓ [VALIDATE]      - Test & validasi
  ✓ [SELF-HEALING]  - Auto-retry jika error
  ✓ [REPORT]        - Summary hasil

"""
    print(tools_text)

def interactive_mode():
    """Run J.A.R.V.I.S in interactive REPL mode"""
    print_welcome()
    
    conversation_history = []
    
    while True:
        try:
            # Get user input
            user_input = input("📌 You: ").strip()
            
            # Handle empty input
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit', 'keluar']:
                print("\n👋 Goodbye! J.A.R.V.I.S signing off...")
                break
            
            if user_input.lower() == 'help':
                print_help()
                continue
            
            if user_input.lower() == 'tools':
                print_tools()
                continue
            
            if user_input.lower() == 'clear':
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
                print_welcome()
                continue
            
            if user_input.lower() in ['halo', 'hai', 'hello', 'apa kabar']:
                response = "Halo! Saya J.A.R.V.I.S, AI Agent yang siap membantu tugas coding Anda. Apa yang bisa saya bantu hari ini? 😊"
                print(f"\n🤖 J.A.R.V.I.S: {response}\n")
                continue
            
            # Add to conversation history
            conversation_history.append({"role": "user", "content": user_input})
            
            print(f"\n🤖 J.A.R.V.I.S: ", end="", flush=True)
            
            try:
                # Send to agent with context of previous messages
                context_message = f"""
User: {user_input}

Catatan: Ini adalah percakapan interaktif. User bisa memberikan instruksi apapun.
Gunakan tools yang tersedia untuk membantu user. Berikan jawaban singkat dan fokus pada hasil.
"""
                
                jarvis_coder.print_response(context_message, stream=True)
                print("\n")
                
            except Exception as e:
                print(f"\n❌ Error: {type(e).__name__}: {str(e)[:200]}")
                print("💡 Tip: Coba 'help' untuk melihat contoh perintah\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            continue

if __name__ == "__main__":
    interactive_mode()