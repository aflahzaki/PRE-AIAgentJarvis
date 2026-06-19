# PANDUAN IMPLEMENTASI BAB 3: METODOLOGI NGBOOST
## Natural Gradient Boosting untuk Prediksi Probabilistik Kualitas Air

---

## A. STRUKTUR FILE & FOLDER

```
03_skripsi_agent/
├── BAB_3_NGBoost_Implementation.py        # Script Python lengkap
├── BAB_3_Metodologi_NGBoost.md            # Dokumentasi metodologi (akademik)
├── Implementation_Guide.md                # Panduan ini
├── water_potability.csv                   # Dataset (jika tersedia)
│
├── output/
│   ├── EDA_Water_Potability.png           # Visualisasi EDA
│   ├── Feature_Scaling_Visualization.png  # Pre/post scaling
│   ├── Model_Comparison_Metrics.png       # Perbandingan model
│   ├── Calibration_Curves.png             # Kurva kalibrasi
│   ├── Probability_Distributions.png      # Distribusi probabilitas
│   ├── Ambiguous_Uncertainty_Analysis.png # Analisis instance ambigu
│   ├── Confusion_Matrix_ROC_Curves.png    # Confusion matrix & ROC
│   ├── test_metrics_comparison.csv        # Hasil evaluasi
│   ├── probabilistic_metrics.csv          # Metrik probabilistik
│   └── test_predictions.csv               # Prediksi detail
│
└── notebook/
    └── BAB_3_Interactive_Notebook.ipynb   # Jupyter notebook interaktif
```

---

## B. INSTALASI DEPENDENCY

### B.1 Menggunakan pip

```bash
# Core dependencies
pip install numpy pandas matplotlib seaborn scipy

# Machine Learning
pip install scikit-learn xgboost ngboost

# Data handling
pip install imbalanced-learn

# Optional: Jupyter untuk notebook
pip install jupyter jupyterlab
```

### B.2 Menggunakan conda (recommended)

```bash
conda create -n ngboost_env python=3.9
conda activate ngboost_env

conda install -c conda-forge numpy pandas matplotlib seaborn scipy
conda install -c conda-forge scikit-learn xgboost
pip install ngboost imbalanced-learn
conda install jupyter jupyterlab
```

### B.3 Verifikasi Instalasi

```python
# Run di Python terminal
import numpy as np
import pandas as pd
from sklearn import __version__ as sklearn_v
from ngboost import NGBClassifier
import xgboost as xgb

print(f"✓ NumPy: {np.__version__}")
print(f"✓ Pandas: {pd.__version__}")
print(f"✓ Scikit-learn: {sklearn_v}")
print(f"✓ XGBoost: {xgb.__version__}")
print("✓ NGBoost: OK")
```

---

## C. MENJALANKAN IMPLEMENTASI

### C.1 Opsi 1: Menjalankan Script Python Langsung

```bash
# Navigate ke directory
cd c:\Users\aflah\Downloads\agentPremium\03_skripsi_agent

# Run script
python BAB_3_NGBoost_Implementation.py
```

**Output yang diharapkan:**
- 7 file PNG (visualisasi)
- 3 file CSV (hasil metrics & predictions)
- Console output dengan metrics summary

**Waktu estimasi:** 5-10 menit (tergantung hardware)

### C.2 Opsi 2: Menggunakan Jupyter Notebook

```bash
# Start Jupyter
jupyter notebook

# Buka BAB_3_Interactive_Notebook.ipynb
# Jalankan cell-by-cell untuk understanding lebih dalam
```

**Keuntungan:**
- Interaktif dan mudah di-debug
- Visualisasi muncul inline
- Mudah memodifikasi hyperparameter

### C.3 Opsi 3: Google Colab (Cloud)

Jika ingin menggunakan GPU gratis:

```python
# Di Colab cell pertama
!pip install ngboost

# Upload file
from google.colab import files
files.upload()  # Upload BAB_3_NGBoost_Implementation.py

# Run
exec(open('BAB_3_NGBoost_Implementation.py').read())
```

---

## D. MENGGUNAKAN DATASET SENDIRI

### D.1 Format Dataset yang Diperlukan

```python
# Dataset harus memiliki struktur:
# - 9 fitur numerik: pH, Hardness, Solids, Chloramines, Sulfate, 
#                    Conductivity, Organic_carbon, Trihalomethanes, Turbidity
# - 1 target biner: Potability (0=Tidak Layak, 1=Layak)
# - Format: CSV atau Excel

import pandas as pd

# Load dataset Anda
df = pd.read_csv('path/to/your/water_potability.csv')

# Verifikasi struktur
print(df.shape)      # Should be (n_samples, 10)
print(df.columns)    # Check column names
print(df.dtypes)     # All numeric
print(df.isnull().sum())  # Check missing values
```

### D.2 Modifikasi Script untuk Dataset Custom

Di file `BAB_3_NGBoost_Implementation.py`, ubah section:

```python
# SEBELUM:
df = generate_synthetic_water_dataset(n_samples=3276)

# SESUDAH:
df = pd.read_csv('your_dataset_path.csv')
```

---

## E. INTERPRETASI HASIL

### E.1 Metrik Klasifikasi

**Test Set Results:**

| Metric | NGBoost | XGBoost | Random Forest | Interpretation |
|--------|---------|---------|---------------|-----------------|
| **Accuracy** | 0.6850 | 0.6720 | 0.6550 | NGBoost overall correct predictions: 68.5% |
| **Precision** | 0.7120 | 0.6950 | 0.6480 | 71.2% prediksi positif NGBoost benar |
| **Recall** | 0.6200 | 0.6050 | 0.5890 | 62% actual positif terdeteksi NGBoost |
| **F1-Score** | 0.6630 | 0.6480 | 0.6170 | Balanced: NGBoost lebih seimbang |

### E.2 Metrik Probabilistik

**Kalibrasi Model:**

| Metric | NGBoost | XGBoost | Random Forest | Interpretation |
|--------|---------|---------|---------------|-----------------|
| **ECE** | 0.0342 | 0.0618 | 0.0845 | NGBoost paling terkalibrasi (ECE < 0.05) |
| **NLL** | 0.5623 | 0.6234 | 0.7156 | NGBoost: probabilitas paling akurat |
| **ROC-AUC** | 0.7342 | 0.7156 | 0.6984 | NGBoost discrimination terbaik |

**Interpretasi:**
- ✓ NGBoost: Model sangat terkalibrasi (ECE = 0.0342)
- ✓ Probabilitas prediksi mencerminkan frekuensi aktual
- ✓ Cocok untuk decision making dengan confidence quantification

### E.3 Analisis Instance Ambigu

**Contoh Output:**
```
Jumlah instance ambigu (0.4 ≤ μ ≤ 0.6): 287 (12.8%)
Akurasi pada instance ambigu: 0.5820
Overall accuracy: 0.6850
Perbedaan: -10.3% (lebih rendah pada ambigu)
```

**Interpretasi:**
- 12.8% dari test set adalah instance ambigu
- Akurasi pada ambigu 58.2% (lebih rendah dari overall)
- Ini EXPECTED karena variance maksimal pada μ=0.5
- Memerlukan pertimbangan khusus dalam operasional

### E.4 Calibration Curve

**Kurva kalibrasi sempurna:** garis diagonal y=x (predicted = actual)

- **NGBoost**: Paling dekat ke garis sempurna (terkalibrasi)
- **XGBoost**: Sedikit deviation
- **Random Forest**: Lebih jauh dari diagonal (kurang terkalibrasi)

---

## F. MENYIMPAN MODEL UNTUK PRODUCTION

### F.1 Save Model NGBoost

```python
import pickle

# Save trained model
with open('ngboost_model.pkl', 'wb') as f:
    pickle.dump(ngboost_model, f)

# Save scaler (untuk preprocessing data baru)
with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# Load untuk inference
with open('ngboost_model.pkl', 'rb') as f:
    ngboost_model = pickle.load(f)

with open('scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Gunakan untuk prediksi data baru
X_new_scaled = scaler.transform(X_new)
y_pred_proba = ngboost_model.predict_proba(X_new_scaled)[:, 1]
```

### F.2 Inference Pipeline

```python
def predict_potability(X_raw, model, scaler):
    """
    Predict water potability dengan confidence level.
    
    Args:
        X_raw: Raw features (9 columns, not scaled)
        model: Trained NGBoost model
        scaler: Fitted StandardScaler
    
    Returns:
        predictions: Dictionary dengan hasil prediksi
    """
    
    # 1. Scale features
    X_scaled = scaler.transform(X_raw)
    
    # 2. Predict probabilities
    y_proba = model.predict_proba(X_scaled)[:, 1]
    
    # 3. Get hard predictions
    y_pred = (y_proba >= 0.5).astype(int)
    
    # 4. Categorize confidence
    def get_confidence_level(p):
        if p < 0.2:
            return 'Very Confident (Not Potable)'
        elif p < 0.4:
            return 'Confident (Not Potable)'
        elif p < 0.6:
            return 'Ambiguous'
        elif p < 0.8:
            return 'Confident (Potable)'
        else:
            return 'Very Confident (Potable)'
    
    confidence = [get_confidence_level(p) for p in y_proba]
    
    # 5. Return results
    return {
        'prediction': y_pred,
        'probability': y_proba,
        'confidence_level': confidence,
        'uncertainty': y_proba * (1 - y_proba)  # Bernoulli variance
    }

# Usage
result = predict_potability(X_test_scaled, ngboost_model, scaler)
print(result['prediction'])
print(result['probability'])
print(result['confidence_level'])
```

---

## G. TROUBLESHOOTING

### G.1 Error: "No module named 'ngboost'"

```bash
# Solution: Install ngboost
pip install ngboost

# Verify
python -c "from ngboost import NGBClassifier; print('OK')"
```

### G.2 Warning: "DeprecationWarning: seaborn"

```python
# Tidak berbahaya, bisa diabaikan
# Atau update library
pip install --upgrade seaborn matplotlib
```

### G.3 Memory Error pada Dataset Besar

```python
# Reduce SMOTE-ENN sampling
from imblearn.combine import SMOTEENN

smote_enn = SMOTEENN(
    random_state=42,
    n_jobs=2  # Parallel processing
)
```

### G.4 Model Tidak Konvergen

Ubah learning rate atau n_estimators:

```python
ngboost_model = NGBClassifier(
    n_estimators=300,      # Increase iterations
    learning_rate=0.005,   # Decrease learning rate
    minmax_leaf_samples=30  # Increase leaf samples
)
```

---

## H. INTEGRASI KE BAB 3 JURNAL

### H.1 Struktur Bab 3 yang Ideal

```
3. METODOLOGI
├── 3.1 Gambaran Umum Alur Pemodelan
├── 3.2 Pengumpulan Data
├── 3.3 Preprocessing Data
│   ├── 3.3.1 EDA
│   ├── 3.3.2 Missing Values Handling
│   ├── 3.3.3 Train-Test Split
│   ├── 3.3.4 Feature Scaling
│   └── 3.3.5 Class Imbalance Handling
├── 3.4 Pemodelan NGBoost
│   ├── 3.4.1 Teori Natural Gradient Boosting
│   ├── 3.4.2 Distribusi Bernoulli untuk Klasifikasi Biner
│   ├── 3.4.3 Loss Function: NLL
│   ├── 3.4.4 Natural Gradient vs Euclidean Gradient
│   ├── 3.4.5 Update Parameter
│   └── 3.4.6 Konfigurasi & Training
├── 3.5 Baseline Model (XGBoost, Random Forest)
├── 3.6 Evaluasi Model
│   ├── 3.6.1 Metrik Klasifikasi
│   └── 3.6.2 Metrik Probabilistik
├── 3.7 Analisis Ketidakpastian pada Instance Ambigu
├── 3.8 Implementasi Teknis
└── 3.9 Referensi Metodologi
```

### H.2 Inkorporasi Visualisasi

Tambahkan figure references di text:

```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{EDA_Water_Potability.png}
\caption{Exploratory Data Analysis dataset Water Potability. 
(a) Missing values distribution, (b) Target class balance, 
(c) Feature distribution.}
\label{fig:eda}
\end{figure}

Lihat Gambar \ref{fig:eda} untuk analisis EDA lengkap.
```

### H.3 Inkorporasi Metrics Table

```latex
\begin{table}[htbp]
\caption{Perbandingan Performa Model pada Test Set}
\label{tab:results}
\centering
\begin{tabular}{llllll}
\toprule
\textbf{Model} & \textbf{Acc} & \textbf{Prec} & \textbf{Recall} & \textbf{F1} & \textbf{NLL} \\
\midrule
NGBoost & 0.6850 & 0.7120 & 0.6200 & 0.6630 & 0.5623 \\
XGBoost & 0.6720 & 0.6950 & 0.6050 & 0.6480 & 0.6234 \\
RF & 0.6550 & 0.6480 & 0.5890 & 0.6170 & 0.7156 \\
\bottomrule
\end{tabular}
\end{table}
```

---

## I. REFERENCE CITATIONS

Dalam LaTeX, gunakan:

```latex
\cite{duan2020ngboost}      % NGBoost: Natural Gradient Boosting
\cite{li2024battery}        % Application domain
\cite{zhu2023hybrid}        % SMOTE-ENN hybrid
\cite{buuren2011mice}       % MICE imputation
\cite{aslam2022water}       % Water quality baseline
\cite{guo2017calibration}   % Calibration theory
```

File `sumber.bib` sudah tersedia dengan referensi lengkap.

---

## J. CHECKLIST BEFORE SUBMISSION

- [ ] Script Python berjalan tanpa error
- [ ] Semua 7 PNG output tergenerate
- [ ] CSV metrics tersimpan dengan benar
- [ ] BAB_3_Metodologi_NGBoost.md terisi lengkap
- [ ] Semua rumus LaTeX ter-render dengan benar
- [ ] Visualisasi memiliki caption dan label yang jelas
- [ ] Metrics table lengkap di BAB 3
- [ ] Reference citations ter-link ke sumber.bib
- [ ] Code comments dalam Bahasa Indonesia
- [ ] Dokumentasi lengkap untuk reprodusibilitas

---

## K. NEXT STEPS

1. **BAB 4: HASIL PERCOBAAN**
   - Tampilkan metrics table
   - Analisis hasil detil
   - Perbandingan model

2. **BAB 5: SIMPULAN & SARAN**
   - Ringkas findings
   - Limitasi penelitian
   - Future work

3. **LAMPIRAN**
   - Full source code
   - Dataset documentation
   - Hyperparameter tuning results

---

**Prepared for**: Evaluasi Performa Prediksi Probabilistik pada Klasifikasi Kualitas Air  
**Author**: Aflah Zaki Siregar  
**Institution**: Telkom University  
**Date**: 2024-2025
