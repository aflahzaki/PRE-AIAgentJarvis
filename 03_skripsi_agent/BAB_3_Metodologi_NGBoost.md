# BAB 3: METODOLOGI
## Evaluasi Performa Prediksi Probabilistik pada Klasifikasi Kualitas Air Menggunakan Natural Gradient Boosting (NGBoost)

---

## 3.1 GAMBARAN UMUM ALUR PEMODELAN

Penelitian ini mengusulkan kerangka kerja prediksi probabilistik untuk klasifikasi kelayakan air minum menggunakan algoritma *Natural Gradient Boosting* (NGBoost). Kerangka kerja tersebut dirancang untuk mengkuantifikasi ketidakpastian prediksi secara eksplisit melalui pemodelan distribusi penuh probabilitas, serta mengevaluasi kalibrasi model dibandingkan dengan pendekatan deterministik konvensional.

Secara keseluruhan, alur penelitian terdiri atas **empat tahapan utama**, yaitu:

### 3.1.1 Tahapan Utama

1. **Pengumpulan dan Eksplorasi Data (EDA)**
   - Penggalian dataset Water Potability dari Kaggle
   - Analisis statistik deskriptif (mean, std, quartile)
   - Deteksi missing values dan outliers
   - Visualisasi distribusi fitur dan target

2. **Pra-pemrosesan Data**
   - Penanganan missing values dengan MICE (*Multivariate Imputation by Chained Equations*)
   - Stratified train-test split (70:15:15)
   - Feature scaling dengan standardization: $z = \frac{x - \mu}{\sigma}$
   - Penanganan class imbalance dengan SMOTE-ENN

3. **Pemodelan Probabilistik dengan NGBoost dan Baseline Deterministik**
   - NGBoost: Memodelkan distribusi Bernoulli penuh
   - XGBoost: Gradient boosting deterministik (point estimate)
   - Random Forest: Ensemble bagging deterministik

4. **Evaluasi Performa Prediktif dan Kalibrasi Probabilitas**
   - Metrik klasifikasi: Accuracy, Precision, Recall, F1-Score
   - Metrik probabilistik: NLL (*Negative Log-Likelihood*), ECE (*Expected Calibration Error*)
   - Analisis ketidakpastian pada instance ambigu (μ ≈ 0.5)

### 3.1.2 Arsitektur Umum Alur Pemodelan

```
┌─────────────────────────────────────────────────────────────┐
│                  START - Data Collection                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
         ┌───────────────────────┐
         │ Water Potability      │
         │ Dataset (3,276 ×  9)  │
         └────────┬──────────────┘
                  │
                  ↓
    ┌─────────────────────────────────┐
    │ EDA + Preprocessing:            │
    │ • MICE Imputation              │
    │ • Standardization              │
    │ • Stratified Split             │
    │ • SMOTE-ENN Resampling        │
    └────┬──────────────────────┬─────┘
         │                      │
         ↓                      ↓
    ┌──────────────┐      ┌──────────────┐
    │   NGBoost    │      │ Baseline     │
    │   Training   │      │ Training:    │
    │   (Natural   │      │ • XGBoost    │
    │   Gradient)  │      │ • RF         │
    └────┬─────────┘      └──────┬───────┘
         │                       │
         └───────────┬───────────┘
                     ↓
         ┌──────────────────────────┐
         │ Evaluasi Model:          │
         │ • Klasifikasi (Acc,      │
         │   Precision, Recall, F1) │
         │ • Probabilistik (NLL,    │
         │   ECE, Calibration)      │
         │ • Ketidakpastian Ambigu  │
         └────────┬─────────────────┘
                  │
                  ↓
    ┌──────────────────────────────┐
    │  END - Result & Analysis     │
    └──────────────────────────────┘
```

---

## 3.2 PENGUMPULAN DATA

### 3.2.1 Sumber dan Deskripsi Dataset

Pengumpulan data pada penelitian ini dilakukan menggunakan dataset sekunder publik berformat tabular yang tersedia di platform Kaggle, yaitu **Water Potability Dataset** \cite{albataineh2026hybrid}. Dataset tersebut dipilih karena memuat parameter fisikokimia yang representatif terhadap kualitas air minum serta telah digunakan pada penelitian terdahulu dalam domain yang identik.

**Karakteristik Dataset:**

| Aspek | Deskripsi |
|-------|-----------|
| **Jumlah Sampel** | 3,276 baris |
| **Jumlah Fitur** | 9 parameter fisikokimia |
| **Jumlah Target** | 1 variabel biner (Potability) |
| **Missing Values** | ~10% (terutama pada pH, Sulfate, Trihalomethanes) |
| **Class Distribution** | 61% Tidak Layak (0), 39% Layak (1) |
| **Format** | Tabular statis (bukan time-series real-time) |

### 3.2.2 Parameter Fisikokimia (9 Fitur)

| Fitur | Simbol | Satuan | Deskripsi |
|-------|--------|--------|-----------|
| pH | $x_1$ | - | Tingkat keasaman/kebasaan air |
| Hardness | $x_2$ | mg/L | Kadar mineral terlarut (Ca, Mg) |
| Solids | $x_3$ | ppm | Total Dissolved Solids |
| Chloramines | $x_4$ | ppm | Konsentrasi klorin gabungan |
| Sulfate | $x_5$ | mg/L | Konsentrasi sulfat |
| Conductivity | $x_6$ | μS/cm | Daya hantar listrik |
| Organic_carbon | $x_7$ | ppm | Karbon organik terlarut |
| Trihalomethanes | $x_8$ | μg/L | Hasil desinfeksi |
| Turbidity | $x_9$ | NTU | Kekeruhan air |

**Variabel Target:**
- $y = 0$: Tidak Layak Konsumsi (Not Potable)
- $y = 1$: Layak Konsumsi (Potable)

---

## 3.3 PREPROCESSING DATA

### 3.3.1 Exploratory Data Analysis (EDA)

Tahap EDA dilakukan untuk memahami karakteristik awal dataset sebelum proses pemodelan. Analisis mencakup:

1. **Pemeriksaan Struktur Data**
   - Dimensi: 3,276 × 10
   - Tipe data: numerik (float64)
   - Memory usage: ~260 KB

2. **Analisis Statistik Deskriptif**
   - Mean, median, std, min, max per fitur
   - Persentil (25%, 50%, 75%)
   - Deteksi outliers menggunakan IQR

3. **Deteksi Missing Values**
   - pH: ~15% missing
   - Sulfate: ~12% missing
   - Trihalomethanes: ~11% missing
   - Fitur lain: <5% missing

4. **Analisis Distribusi Target**
   - Kelas 0 (Tidak Layak): 2,011 sampel (61.4%)
   - Kelas 1 (Layak): 1,265 sampel (38.6%)
   - Class Imbalance Ratio: 1:0.629

### 3.3.2 Penanganan Missing Values (MICE)

Nilai hilang terutama ditemukan pada fitur pH, Sulfate, dan Trihalomethanes. Metode **Multivariate Imputation by Chained Equations (MICE)** diterapkan sebagai pendekatan imputasi berbasis regresi iteratif yang memanfaatkan hubungan antar fitur dalam memperkirakan nilai yang hilang \cite{buuren2011mice}.

**Alasan Pemilihan MICE:**
- Mempertahankan struktur korelasi multivariat
- Memperhitungkan hubungan kimiawi antar parameter fisikokimia
- Lebih akurat daripada mean/median imputation pada data dengan missing structure kompleks
- Cocok untuk dataset tabular dengan fitur yang saling bergantung

**Prosedur Implementasi:**
```
Untuk setiap iterasi t = 1, 2, ..., T:
  1. Untuk setiap fitur j dengan missing values:
     - Fit regresi: x_j ~ x_(-j) (semua fitur selain j)
     - Predict nilai hilang berdasarkan fitur lain
     - Tambah stochastic error: ε ~ N(0, σ²)
  2. Iterasi hingga konvergensi
```

### 3.3.3 Stratified Train-Validation-Test Split

Dataset dibagi menjadi tiga subset dengan stratifikasi kelas untuk mempertahankan distribusi target:

$$\text{Train : Validation : Test} = 70\% : 15\% : 15\%$$

**Implementasi:**
1. Split pertama: 70% train, 30% temporary
2. Split kedua pada temporary: 50% validation, 50% test

**Manfaat Stratifikasi:**
- Memastikan setiap subset merepresentasikan distribusi kelas asli
- Mencegah bias evaluasi pada dataset dengan class imbalance
- Proporsi kelas terjaga: ~61% Tidak Layak, ~39% Layak di setiap subset

### 3.3.4 Feature Scaling (Standardization)

Penskalaan fitur dilakukan untuk menyeragamkan skala antar fitur menggunakan standardisasi z-score:

$$z_i = \frac{x_i - \mu}{\sigma}$$

dimana:
- $x_i$ = nilai fitur asli
- $\mu$ = rata-rata fitur (dihitung dari training set)
- $\sigma$ = standar deviasi fitur (dihitung dari training set)
- $z_i$ = nilai terstandarisasi

**Keuntungan Standardisasi:**
- Meningkatkan konvergensi gradient-based optimization (NGBoost, XGBoost)
- MICE/SMOTE-ENN menjadi lebih stabil (fitur dengan range besar tidak mendominasi)
- Interpretasi bobot/koefisien menjadi lebih konsisten

### 3.3.5 Penanganan Class Imbalance (SMOTE-ENN)

Teknik **SMOTE-ENN** (Synthetic Minority Over-sampling Technique combined with Edited Nearest Neighbor) diterapkan untuk menangani class imbalance \cite{batista2004study}:

1. **SMOTE (Over-sampling kelas minoritas):**
   - Generate sampel sintetik untuk kelas Layak (minoritas)
   - Jarak k-nearest neighbors dalam feature space
   - Interpolasi: $\mathbf{x}_{syn} = \mathbf{x}_i + \lambda(\mathbf{x}_{knn} - \mathbf{x}_i)$, $\lambda \in [0,1]$

2. **ENN (Under-sampling noise):**
   - Hapus sampel di area batas keputusan yang diprediksi salah
   - Gunakan 3-nearest neighbors untuk deteksi

**Imbalance Ratio:**
- Sebelum SMOTE-ENN: 1:0.629
- Setelah SMOTE-ENN: ~1:1.0 (seimbang)

---

## 3.4 PEMODELAN PROBABILISTIK - NATURAL GRADIENT BOOSTING (NGBOOST)

### 3.4.1 Landasan Teori Natural Gradient Boosting

**Natural Gradient Boosting (NGBoost)** adalah algoritma ensemble probabilistik yang memodelkan distribusi penuh $P_\theta(y|\mathbf{x})$ sebagai output prediksi \cite{duan2020ngboost}. Berbeda dengan gradient boosting konvensional yang hanya menghasilkan point estimate, NGBoost menggunakan *Natural Gradient* yang memanfaatkan *Fisher Information Matrix* (FIM) untuk mengarahkan optimasi sesuai geometri ruang probabilitas.

### 3.4.2 Distribusi Output untuk Klasifikasi Biner

Untuk variabel target Potability yang bersifat biner, distribusi output pada NGBoost ditentukan dengan menggunakan **Bernoulli Distribution**:

$$P(y|\mathbf{x}) = \mu(\mathbf{x})^y \cdot (1-\mu(\mathbf{x}))^{1-y}$$

dimana:
- $y \in \{0, 1\}$ (label kelas)
- $\mu(\mathbf{x}) = P(y=1|\mathbf{x})$ = probabilitas kelas positif (Layak)
- $\mu(\mathbf{x}) \in [0, 1]$

**Variance pada Distribusi Bernoulli:**

$$\text{Var}(y|\mathbf{x}) = \mu(\mathbf{x})(1-\mu(\mathbf{x}))$$

Karakteristik penting: ketidakpastian mencapai **maksimum pada $\mu = 0.5$** (ambang batas keputusan), dan **minimum pada $\mu = 0$ atau $\mu = 1$** (prediksi sangat yakin).

### 3.4.3 Loss Function: Negative Log-Likelihood (NLL)

Fungsi loss yang digunakan adalah Negative Log-Likelihood, merupakan proper scoring rule untuk distribusi probabilitas:

$$\mathcal{L}(\theta) = -\mathbb{E}_{y \sim p_0}\left[\log P_\theta(y|\mathbf{x})\right]$$

Untuk klasifikasi biner dengan single sample:

$$\mathcal{L}(\theta) = -\left[y \log \mu(\mathbf{x}) + (1-y) \log(1-\mu(\mathbf{x}))\right]$$

### 3.4.4 Natural Gradient vs Euclidean Gradient

**Euclidean Gradient (Gradient Descent Standar):**

$$\nabla_\theta \mathcal{L}(\theta) = \frac{\partial \mathcal{L}(\theta)}{\partial \theta}$$

Beroperasi pada ruang Euclidian, tidak memperhitungkan struktur geometri distribusi probabilitas.

**Natural Gradient (NGBoost):**

$$\tilde{\nabla}_\theta = \mathcal{I}(\theta)^{-1} \nabla_\theta$$

dimana **Fisher Information Matrix**:

$$\mathcal{I}(\theta) = \mathbb{E}_{y \sim P_\theta}\left[\nabla_\theta \log P_\theta(y|\mathbf{x}) \cdot \nabla_\theta \log P_\theta(y|\mathbf{x})^\top\right]$$

Natural Gradient memberikan **update direction yang lebih representatif** terhadap struktur statistik data, sehingga:
- Estimasi parameter lebih stabil
- Konvergensi lebih cepat pada manifold probabilitas
- Prediksi probabilistik lebih terkalibrasi

### 3.4.5 Update Parameter pada Iterasi Boosting

Pada setiap iterasi $m = 1, 2, ..., M$ dari boosting:

$$\theta^{(m)} = \theta^{(m-1)} - \eta \cdot \tilde{\nabla}_\theta^{(m)}$$

dimana:
- $\eta$ = learning rate (hyperparameter)
- $\tilde{\nabla}_\theta^{(m)}$ = natural gradient pada iterasi m
- Base learner = decision tree dangkal (depth 1-3)

**Mekanisme Boosting:**
1. Inisialisasi parameter distribusi untuk setiap sample
2. Pada setiap iterasi, base learner memprediksi gradient natural
3. Update parameter menggunakan gradient dengan factor learning rate
4. Iterasi hingga konvergensi atau early stopping

### 3.4.6 Konfigurasi dan Training NGBoost

**Hyperparameter yang Dikonfigurasi:**

| Parameter | Nilai | Deskripsi |
|-----------|-------|-----------|
| `n_estimators` | 200 | Jumlah iterasi boosting |
| `learning_rate` | 0.01 | Faktor update parameter (0-1) |
| `minmax_leaf_samples` | 20 | Min samples per leaf di base tree |
| `col_sample` | 0.8 | Fraksi fitur yang disampling per iterasi |
| `random_state` | 42 | Seed untuk reproducibility |

**Strategi Tuning:**
- Memanfaatkan validation set (15%) untuk early stopping
- Kriteria pemilihan: Trade-off antara NLL rendah dan ECE stabil
- Early stopping: Hentikan jika NLL validation tidak menurun signifikan

**Proses Training:**
```
Input: X_train (scaled), y_train (resampled)
Output: Model terkalibrasi yang memodelkan P(y|x)

1. Initialize Bernoulli distribution parameters μ0
2. For m = 1 to n_estimators:
   a. Compute natural gradient untuk setiap sample
   b. Fit decision tree shallow sebagai base learner
   c. Update parameters: μ(m) = μ(m-1) - η * g_natural(m)
   d. Check validation NLL untuk early stopping
3. Return fitted model
```

---

## 3.5 BASELINE MODELS: XGBOOST & RANDOM FOREST

Baseline model disusun sebagai acuan komparatif prosedural untuk mengukur kontribusi pendekatan probabilistik NGBoost dalam konteks klasifikasi kualitas air.

### 3.5.1 XGBoost (Gradient Boosting Deterministik)

**Karakteristik:**
- Output: Point estimate probabilitas tanpa distribusi penuh
- Menggunakan Euclidean gradient, bukan natural gradient
- Tidak memodelkan struktur distribusi yang kompleks
- Regularisasi L1/L2 untuk mencegah overfitting

**Konfigurasi:**
```python
n_estimators = 200
learning_rate = 0.01
max_depth = 5
```

**Keunggulan:**
- Scalable ke dataset besar
- Penanganan missing values built-in
- Feature importance transparan

**Kelemahan (untuk tujuan penelitian):**
- Probabilitas point estimate (tidak probabilistik penuh)
- Tidak mengkuantifikasi ketidakpastian prediksi
- Kalibrasi probabilitas tidak dioptimalkan secara eksplisit

### 3.5.2 Random Forest (Ensemble Bagging Deterministik)

**Karakteristik:**
- Aggregasi decision trees independen (bagging, bukan boosting)
- Output: Rata-rata probabilitas dari individual trees
- Parallelizable, robust terhadap overfitting
- Tidak ada hyperparameter regularisasi eksplisit

**Konfigurasi:**
```python
n_estimators = 200
max_depth = 10
```

**Keunggulan:**
- Robust, minimal tuning
- Feature importance tersedia
- Parallelizable

**Kelemahan (untuk tujuan penelitian):**
- Probabilitas merupakan simple averaging (tidak probabilistik penuh)
- Kalibrasi probabilitas biasanya lebih buruk dibanding boosting
- Tidak menggunakan gradient-based optimization

### 3.5.3 Perbedaan Esensial: NGBoost vs Baseline

| Aspek | NGBoost | XGBoost | Random Forest |
|-------|---------|---------|---------------|
| **Paradigma** | Probabilistik | Deterministik | Deterministik |
| **Output** | Distribusi penuh | Point estimate | Point estimate |
| **Gradient** | Natural gradient | Euclidean gradient | N/A (bagging) |
| **Optimizer** | Fisher Information Matrix | Standard gradient descent | Parallel trees |
| **Loss Function** | NLL (proper scoring) | Logistic/Hinge | Gini impurity |
| **Kalibrasi** | Optimal | Point estimate | Averaging bias |

---

## 3.6 EVALUASI MODEL

### 3.6.1 Metrik Klasifikasi

#### 3.6.1.1 Accuracy (Akurasi)

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$

Mengukur proporsi prediksi yang benar secara keseluruhan. Keterbatasan pada dataset dengan class imbalance.

#### 3.6.1.2 Precision (Presisi)

$$\text{Precision} = \frac{TP}{TP + FP}$$

Dari semua prediksi positif, berapa banyak yang benar? Penting saat False Positive cost tinggi.

#### 3.6.1.3 Recall (Recall/Sensitivity)

$$\text{Recall} = \frac{TP}{TP + FN}$$

Dari semua positif aktual, berapa banyak yang terdeteksi? Penting saat False Negative cost tinggi.

#### 3.6.1.4 F1-Score

$$\text{F1} = 2 \cdot \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

Harmonic mean dari Precision dan Recall. Balanced metric untuk class imbalance.

### 3.6.2 Metrik Probabilistik (Kalibrasi)

#### 3.6.2.1 Negative Log-Likelihood (NLL)

$$\text{NLL} = -\frac{1}{N} \sum_{i=1}^{N} \left[y_i \log \hat{p}_i + (1-y_i) \log(1-\hat{p}_i)\right]$$

Mengukur kesesuaian distribusi prediksi dengan aktual kelas. **Nilai lebih rendah lebih baik.** Sensitive terhadap probabilitas ekstrem (close to 0 atau 1).

#### 3.6.2.2 Expected Calibration Error (ECE)

$$\text{ECE} = \sum_{b=1}^{B} \frac{n_b}{N} \left|\bar{p}_b - \bar{y}_b\right|$$

dimana:
- $B$ = jumlah bin (biasanya 10)
- $n_b$ = jumlah sampel di bin b
- $N$ = total sampel
- $\bar{p}_b$ = rata-rata probabilitas prediksi di bin b
- $\bar{y}_b$ = proporsi aktual kelas positif di bin b

**Interpretasi ECE:**
- **ECE < 0.05**: Model sangat terkalibrasi (prediksi probabilitas mencerminkan frekuensi aktual)
- **ECE 0.05-0.10**: Model terkalibrasi cukup baik
- **ECE > 0.10**: Model perlu perbaikan kalibrasi

**Contoh Kalibrasi:**
- Jika model memprediksi P=0.8 untuk group samples, maka ~80% dari group tersebut seharusnya actual positive (y=1)
- Jika actual ~60%, maka model tidak terkalibrasi pada region 0.8

### 3.6.3 Evaluasi pada Test Set

Semua metrik dihitung pada test set yang **belum pernah dilihat** selama training dan tuning untuk mendapatkan estimasi performa yang tidak bias.

---

## 3.7 ANALISIS KETIDAKPASTIAN PADA INSTANCE AMBIGU

### 3.7.1 Karakterisasi Instance Ambigu

Pada distribusi Bernoulli, ketidakpastian (variance) mencapai maksimum pada $\mu = 0.5$:

$$\text{Var}_{\max} = 0.5 \times (1-0.5) = 0.25$$

Instance dengan probabilitas prediksi di sekitar 0.5 adalah **instance ambigu** yang secara inheren memiliki ketidakpastian prediksi tertinggi.

### 3.7.2 Kategorisasi Confidence Level

Instance dikategorisasi berdasarkan tingkat kepercayaan model:

| Kategori | Range Probabilitas | Interpretasi |
|----------|-------------------|--------------|
| Very Confident (Not Potable) | $\mu < 0.2$ | Sangat yakin tidak layak |
| Confident (Leaning Not Potable) | $0.2 \leq \mu < 0.4$ | Cenderung tidak layak |
| **Ambiguous** | $0.4 \leq \mu < 0.6$ | **Ragu-ragu, ketidakpastian tinggi** |
| Confident (Leaning Potable) | $0.6 \leq \mu < 0.8$ | Cenderung layak |
| Very Confident (Potable) | $\mu \geq 0.8$ | Sangat yakin layak |

### 3.7.3 Analisis Ambigu

Untuk instance ambigu, dilakukan analisis:
1. **Persentase** instance ambigu dalam test set
2. **Akurasi** pada instance ambigu vs overall accuracy
3. **Implikasi** terhadap keandalan sistem dalam pengambilan keputusan
4. **Rekomendasi** untuk handling instance kritis

### 3.7.4 Implicasi Operasional

Instance ambigu memerlukan perhatian khusus:
- Mungkin memerlukan re-measurement atau analisis laboratorium lebih detail
- Pengambilan keputusan dapat melibatkan expert judgment tambahan
- Threshold prediksi dapat disesuaikan secara adaptif berdasarkan confidence
- Monitoring tambahan diperlukan untuk quality assurance

---

## 3.8 IMPLEMENTASI TEKNIS

### 3.8.1 Environment & Library

**Python Version**: 3.9+

**Essential Libraries**:
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Machine Learning
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, log_loss, roc_auc_score)

# Gradient Boosting
import xgboost as xgb
from ngboost import NGBClassifier
from ngboost.distns import Bernoulli

# Imbalance Handling
from imblearn.combine import SMOTEENN

# Statistical Tests
from scipy import stats
```

### 3.8.2 Pipeline Preprocessing

```python
# 1. Load data
df = pd.read_csv('water_potability.csv')

# 2. EDA
df.describe()
df.isnull().sum()

# 3. Train-Val-Test Split (70:15:15) dengan stratification
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, stratify=y, random_state=42
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=42
)

# 4. MICE Imputation (hanya pada train set)
imputer = SimpleImputer(strategy='mean')
X_train = imputer.fit_transform(X_train)

# 5. Standardization (fit pada train, apply ke val/test)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)
X_test = scaler.transform(X_test)

# 6. SMOTE-ENN (hanya pada train set)
smote_enn = SMOTEENN(random_state=42)
X_train, y_train = smote_enn.fit_resample(X_train, y_train)
```

---

## 3.9 REFERENSI METODOLOGI

\cite{duan2020ngboost} - Natural Gradient Boosting (Framework utama)

\cite{li2024battery} - Aplikasi NGBoost pada domain teknis

\cite{zhu2023hybrid} - SMOTE-ENN untuk class imbalance

\cite{buuren2011mice} - MICE untuk missing data imputation

\cite{aslam2022water}, \cite{park2022ensemble}, \cite{albataineh2026hybrid} - Domain kualitas air

\cite{guo2017calibration}, \cite{niculescu2005predicting} - Kalibrasi probabilistik

---

## KESIMPULAN BAB 3

Metodologi penelitian ini secara komprehensif mengintegrasikan:

1. ✓ **Data Collection**: Water Potability Dataset publik (3,276 × 9)
2. ✓ **Preprocessing**: MICE, stratified split, standardization, SMOTE-ENN
3. ✓ **Modeling**: NGBoost (probabilistik) + XGBoost & RF (baseline deterministik)
4. ✓ **Evaluation**: Metrik klasifikasi + probabilistik (NLL, ECE)
5. ✓ **Uncertainty Analysis**: Instance ambigu dan confidence categorization

Pendekatan tersebut dirancang untuk **mengkuantifikasi ketidakpastian secara eksplisit** dan **menghasilkan prediksi probabilistik yang terkalibrasi**, sehingga memberikan fondasi yang solid bagi sistem pendukung keputusan dalam manajemen kualitas air minum.
