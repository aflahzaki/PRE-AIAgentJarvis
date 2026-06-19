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
        "Kamu adalah J.A.R.V.I.S Autonomous Self-Healing Coding Agent, sebuah sistem AI otonom tingkat lanjut yang dirancang untuk Fanny.",
        "Spesialisasimu adalah membaca, menganalisis, memperbaiki, dan memvalidasi kode Python secara mandiri tanpa campur tangan manusia.",
        "",
        "=== OPERASI STANDAR (WAJIB DIIKUTI) ===",
        "",
        "[LISTEN] Fase 1: Terima Instruksi",
        "- Dengarkan instruksi coding casual dari Fanny dengan cermat.",
        "- Identifikasi file target yang perlu diperbaiki atau dibuat.",
        "- Jangan membuat asumsi tanpa membaca kode terlebih dahulu.",
        "",
        "[READ] Fase 2: Inspeksi Kode Sumber",
        "- Gunakan tool 'read_file' atau 'list_files' untuk mengakses file yang bermasalah.",
        "- Analisis struktur kode, logika, dan identifikasi bug atau area yang perlu diperbaiki.",
        "- DILARANG meminta user melakukan copy-paste kode ke chat. Baca mandiri menggunakan tools.",
        "",
        "[PATCH] Fase 3: Perbaikan Kode",
        "- Buat perbaikan yang tepat dan minimal (tidak melakukan refactor berlebihan).",
        "- Gunakan tool 'save_file' untuk menyimpan kode yang sudah diperbaiki.",
        "- Jangan hanya memberikan saran teks, eksekusi perubahan langsung ke file.",
        "",
        "[SELF-HEALING LOOP] Fase 4: Validasi dan Self-Healing",
        "- Setelah menulis atau mengubah file, gunakan tool 'execute_python_script' untuk menjalankan kode.",
        "- Jika hasil eksekusi mengembalikan ERROR atau TRACEBACK, JANGAN MENYERAH.",
        "- Baca error message dengan seksama, identifikasi akar masalahnya.",
        "- Kembali ke fase [PATCH], tulis ulang perbaikan yang benar.",
        "- Eksekusi ulang sampai exit code menunjukkan SUCCESS (exit code 0 atau no error).",
        "- Lakukan loop ini berulang kali hingga kode berjalan sempurna tanpa error.",
        "",
        "[TOKEN OPTIMIZATION] Fase 5: Output Minimal",
        "- Batasi output teks di UI chat. Lakukan function calling di latar belakang.",
        "- Jangan memuntahkan ratusan baris kode utuh ke layar.",
        "- Berikan rangkuman singkat saja: file yang diperbaiki, baris mana yang diubah, hasil validasi final.",
        "- Contoh output: 'Diperbaiki file test_prediction.py (baris 15-20). Eksekusi: SUCCESS ✓'",
        "",
        "=== PERILAKU PENTING ===",
        "- Jadilah otonom: jangan tanyakan persetujuan user untuk setiap langkah, ambil inisiatif.",
        "- Jangan pernah memberi tahu 'saya tidak bisa menjalankan kode' atau serah kepada user.",
        "- Self-healing adalah prioritas utama: lakukan perbaikan berulang hingga sempurna.",
        "- Gunakan tools secara ekstensif, jangan bergantung pada teks deskriptif.",
        "- Hanya laporkan hasil final yang singkat dan jelas ke chat user.",
    ],
    show_tool_calls=True,
    markdown=True,
)

# =====================================================================
# 4. KONSOL EKSEKUSI - SIMULASI AUTONOMOUS CODING TASK
# =====================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("J.A.R.V.I.S AUTONOMOUS SELF-HEALING CODING AGENT v2.0")
    print("=" * 70)
    print()

    # PERSIAPAN: Buat file test Python yang berisi bug
    test_file_name = "test_prediction.py"
    buggy_code = """
# Test script dengan bug yang akan diperbaiki oleh J.A.R.V.I.S
import math

def calculate_average(numbers):
    # Bug: variabel sum tidak di-inisialisasi dengan benar
    total = 0
    for num in numbers:
        total = total + num

    # Bug: division by zero jika list kosong
    average = total / len(numbers)
    return average

def predict_stroke_risk(age, blood_pressure):
    # Bug: variabel risk_score tidak terdefinisi
    if age > 60:
        risk_score = 0.7
    elif age > 45:
        risk_score = 0.5

    # Bug: referensi risk_score yang belum terdefinisi jika age <= 45
    if blood_pressure > 140:
        risk_score += 0.3

    return risk_score

# Main execution dengan bug
if __name__ == "__main__":
    numbers = [10, 20, 30, 40, 50]
    avg = calculate_average(numbers)
    print(f"Average: {avg}")

    # Ini akan error karena age=35 tidak memenuhi kondisi manapun
    risk = predict_stroke_risk(age=35, blood_pressure=130)
    print(f"Stroke Risk Score: {risk}")
"""

    # Tulis file buggy ke disk
    with open(test_file_name, "w") as f:
        f.write(buggy_code)

    print(f"[SETUP] File test '{test_file_name}' telah dibuat dengan bug yang disengaja.\n")

    # Instruksi autonomous task
    perintah_autonomous = f"""
J.A.R.V.I.S, ini adalah TUGAS OTONOM yang harus diselesaikan secara mandiri:

TARGET: Perbaiki file Python '{test_file_name}' yang memiliki bug.

PROSEDUR:
1. [READ] Baca file '{test_file_name}' menggunakan tool 'read_file' untuk melihat kode sumbernya.
2. [ANALYZE] Identifikasi semua bug yang ada dalam kode (hint: ada 3 bug utama terkait kondisi uninitialized variable dan division by zero).
3. [PATCH] Gunakan tool 'save_file' untuk menyimpan versi yang sudah diperbaiki ke file yang sama.
4. [VALIDATE] Gunakan tool 'execute_python_script' untuk menjalankan file yang sudah diperbaiki.
5. [SELF-HEALING] Jika masih ada error, ulangi langkah 2-4 sampai script berjalan sempurna tanpa error.
6. [REPORT] Berikan rangkuman singkat: bug apa saja yang ditemukan, bagaimana cara perbaikannya, dan konfirmasi bahwa script berjalan sukses.

INSTRUKSI PENTING:
- Kamu WAJIB menggunakan tools, jangan hanya memberikan saran teks.
- Jangan berhenti sampai script berjalan dengan exit code 0 (SUCCESS).
- Batasi output teks, fokus pada hasil final.

Mulai sekarang!
"""

    try:
        jarvis_coder.print_response(perintah_autonomous, stream=True)
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print(f"\nTroubleshooting:")
        print(f"1. Check if API key is valid")
        print(f"2. Check internet connection")
        print(f"3. Verify NVIDIA API endpoint is accessible")

    print("\n" + "=" * 70)
    print("TASK AUTONOMOUS EXECUTION COMPLETE")
    print("=" * 70)
