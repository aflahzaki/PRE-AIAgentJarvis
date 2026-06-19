# J.A.R.V.I.S Autonomous Self-Healing Coding Agent v2.0

## Overview
J.A.R.V.I.S adalah sistem AI otonom tingkat lanjut untuk Fanny yang dirancang untuk membaca, menganalisis, memperbaiki, dan memvalidasi kode Python secara mandiri tanpa campur tangan manusia.

## Prerequisites
1. **Python 3.8+** - Installed and in PATH
2. **Phidata** - Install dengan: `pip install phidata`
3. **Nvidia API Key** - Already embedded in the script
4. **Internet Connection** - Required untuk akses Nvidia API

## File Structure
```
J.A.R.V.I.S_system/
├── jarvis_coder.py          # Main agent file
├── test_prediction.py       # (Generated) Buggy test file
└── README_JARVIS.md         # This file
```

## How to Run

### Method 1: Direct Python Execution
```bash
cd C:\Users\aflah\Downloads\agentPremium\J.A.R.V.I.S_system
python jarvis_coder.py
```

### Method 2: With Error Handling
```bash
python jarvis_coder.py 2>&1 | tee jarvis_output.log
```

## Expected Output

When run successfully, you will see:
```
======================================================================
J.A.R.V.I.S AUTONOMOUS SELF-HEALING CODING AGENT v2.0
======================================================================

[SETUP] File test 'test_prediction.py' telah dibuat dengan bug yang disengaja.

[Tool calls from agent...]
- [READ] Membaca test_prediction.py
- [ANALYZE] Mengidentifikasi 3 bug:
  1. Division by zero pada calculate_average
  2. Uninitialized variable risk_score
  3. Missing else case in predict_stroke_risk
- [PATCH] Menulis perbaikan ke file
- [VALIDATE] Menjalankan test_prediction.py
  Average: 30.0
  Stroke Risk Score: 0.5
  [EXIT CODE: 0] ✓

[REPORT] Diperbaiki file test_prediction.py. Eksekusi: SUCCESS ✓

======================================================================
TASK AUTONOMOUS EXECUTION COMPLETE
======================================================================
```

## Key Features

### ✓ Autonomous Operation
- Agent bekerja tanpa intervensi user
- Membaca kode, menganalisis, dan memperbaiki secara mandiri

### ✓ Self-Healing Loop
1. **[LISTEN]** - Menerima instruksi
2. **[READ]** - Membaca file dengan tools
3. **[PATCH]** - Menulis perbaikan
4. **[VALIDATE]** - Menjalankan dan verifikasi
5. **[SELF-HEALING]** - Loop hingga success
6. **[REPORT]** - Laporan ringkas

### ✓ Native Python Execution Tool
- Fungsi `execute_python_script()` bisa diakses agent
- Menjalankan script Python dan menangkap output/error
- Exit code untuk validasi status

### ✓ Token Optimization
- Output minimal di chat
- Fokus pada hasil akhir
- Tidak membanjiri layar dengan code dump

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'phi'"
**Solution:**
```bash
pip install phidata
pip install openai
```

### Error: "Failed to connect to API"
**Causes:**
1. Internet connection issue
2. API key expired or invalid
3. Nvidia API endpoint down

**Solution:**
- Check internet: `ping google.com`
- Verify API key is valid
- Wait and retry (API might be temporarily unavailable)

### Error: "Timeout"
**Cause:** Script execution exceeds 30 seconds

**Solution:**
- Check test_prediction.py for infinite loops
- Increase timeout in execute_python_script() if needed
- Break large tasks into smaller chunks

### Exit Code Non-Zero
**Meaning:** Script ran but with errors

**What to check:**
1. Read stderr output carefully
2. Identify the specific error
3. Let agent go through self-healing loop again
4. Or manually inspect test_prediction.py

## Agent Instructions Summary

The agent MUST follow these phases:

| Phase | Action | Tool |
|-------|--------|------|
| **LISTEN** | Receive instructions | - |
| **READ** | Inspect source code | `read_file`, `list_files` |
| **PATCH** | Fix code | `save_file` |
| **VALIDATE** | Run and check | `execute_python_script` |
| **SELF-HEALING** | Loop until success | Repeat PATCH→VALIDATE |
| **REPORT** | Output summary | (Text output) |

## Files Generated

After first run, these files are created:
- `test_prediction.py` - Buggy test file (auto-generated)
- (Others created as agent works)

## Customization

To modify the test case:
1. Edit the `buggy_code` string in jarvis_coder.py (around line 130)
2. Run the script again
3. Agent will create new buggy_code and start fixing it

Example custom task:
```python
perintah_autonomous = """
J.A.R.V.I.S, perbaiki file 'my_script.py' yang memiliki bug terkait database connection.
"""
```

## Success Criteria

✓ Agent reads file without user copy-paste
✓ Agent identifies bugs correctly
✓ Agent patches code without asking permission
✓ Agent runs execute_python_script tool
✓ If error occurs, agent doesn't give up
✓ Agent loops until exit code = 0
✓ Agent provides brief final report

## Contact & Support

For issues or customization:
- Check the troubleshooting section above
- Review jarvis_coder.py instructions (lines 74-114)
- Verify prerequisites are installed

---

**Version:** 2.0  
**Last Updated:** 2026-05-18  
**Framework:** Phidata  
**Model:** Meta Llama 3.3 70B (via Nvidia API)
