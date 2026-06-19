# 🚀 J.A.R.V.I.S Setup & Execution Guide

## Langkah 1: Install Dependencies

```bash
cd C:\Users\aflah\Downloads\agentPremium\J.A.R.V.I.S_system
pip install -r requirements.txt
```

Atau manual:
```bash
pip install phidata openai pydantic
```

## Langkah 2: Verifikasi Setup

```bash
python run_jarvis.py
```

Script ini akan:
- ✓ Check semua dependencies terinstall
- ✓ Verify environment variables
- ✓ Run J.A.R.V.I.S agent
- ✓ Show hasil akhir

## Langkah 3: Jalankan J.A.R.V.I.S

### Option A: Dengan Helper Script (Recommended)
```bash
python run_jarvis.py
```

### Option B: Direct Execution
```bash
python jarvis_coder.py
```

## Apa yang Akan Terjadi?

1. **[SETUP]** - Script membuat file `test_prediction.py` dengan 3 bugs
2. **[AGENT RUNS]** - J.A.R.V.I.S membaca, analisis, dan perbaiki bugs
3. **[SELF-HEALING]** - Jika ada error, agent otomatis loop sampai sukses
4. **[REPORT]** - Agent memberikan summary singkat hasil perbaikan

## Output Yang Diharapkan

```
======================================================================
J.A.R.V.I.S AUTONOMOUS SELF-HEALING CODING AGENT v2.0
======================================================================

[SETUP] File test 'test_prediction.py' telah dibuat dengan bug yang disengaja.

[Tool Calls...]
- Reading file test_prediction.py
- Analyzing code...
- Patching bugs...
- Validating execution...

Average: 30.0
Stroke Risk Score: 0.5
[EXIT CODE: 0] ✓

Diperbaiki file test_prediction.py. Eksekusi: SUCCESS ✓

======================================================================
TASK AUTONOMOUS EXECUTION COMPLETE
======================================================================
```

## Troubleshooting

### ❌ Error: "No module named 'phi'"
```bash
pip install phidata
```

### ❌ Error: "Connection timeout"
- Check internet connection
- Verify API key is valid
- Wait and retry (API might be down)

### ❌ Error: "Script timeout"
- Check test_prediction.py for infinite loops
- Increase timeout in execute_python_script()

### ❌ Exit code non-zero
- Agent akan otomatis retry sampai sukses
- Jika tetap error, check error message dan lihat README_JARVIS.md

## Files Created

After running:
- `test_prediction.py` - Auto-generated test file (overwritten each run)
- `jarvis_output.log` - (Optional) jika redirect output ke file

## Next Steps

1. ✓ Verify script berjalan tanpa error
2. ✓ Check output di console
3. ✓ Customize buggy code di jarvis_coder.py jika ingin test case lain
4. ✓ Ready untuk production use!

---

**Questions?** Check README_JARVIS.md untuk dokumentasi lengkap.
