================================================================
  LANGKAH SELANJUTNYA – PJK-GM016
  Proyek: AI-Based Pharmaceutical Data Selection & Monitoring
  Pijak x IBM SkillsBuild
  Diperbarui: April 2026
================================================================

Dokumen ini adalah panduan teknis untuk anggota tim, merujuk
langsung pada timeline proyek di dokumen Project Plan.

================================================================
  STATUS SAAT INI
================================================================
✅ Dataset xlsx → CSV mentah (rekap_produksi_granulasi_raw.csv)
✅ Script preprocessing (01_preprocessing.py)
✅ Script EDA (02_eda.py)
⬜ Feature engineering lanjutan
⬜ Model AI (Isolation Forest, Random Forest, K-Means)
⬜ Dashboard interaktif
⬜ Integrasi & pengujian

================================================================
  MINGGU 2 – SELESAIKAN PREPROCESSING & EDA
================================================================

PIC: APC248D6Y0099 (Data Preparation) + APC248D6X0446 (AI Analyst)

[1] Jalankan script secara berurutan:
    python 01_preprocessing.py
    python 02_eda.py

[2] Validasi output CSV (rekap_produksi_clean.csv):
    - Pastikan tidak ada missing value di kolom fitur kunci
    - Cek distribusi label Defect_Overall (balanced/imbalanced?)
    - Jika sangat imbalanced (>80% satu kelas), pertimbangkan
      teknik SMOTE atau class_weight='balanced' saat modeling

[3] Review EDA di folder eda_output/:
    - 01_distribusi_defect.png
    - 02_distribusi_material.png
    - 03_distribusi_numerik.png
    - 04_boxplot_normal_vs_defect.png
    - 05_heatmap_korelasi.png
    - 06_tren_pct_teoritis.png
    - 07_defect_rate_per_material.png
    - 08_scatter_cetak_vs_kemas.png
    - ringkasan_statistik.txt

[4] Catat temuan EDA untuk insight awal:
    - Variabel mana yang paling berkorelasi dengan defect?
    - Produk mana yang paling sering defect?
    - Ada outlier ekstrem? Perlu dibuang atau dikap?

[5] Feature tambahan yang bisa dipertimbangkan:
    - Encode kolom Cetak_Mesin, Kemas_Mesin, GB_Mesin_L1
      menggunakan Label Encoding atau One-Hot Encoding
    - Interaksi fitur: GB_Kadar_Air_Mean * Rasio_GK_GB
    - Lag batch: apakah batch sebelumnya mempengaruhi kualitas?

================================================================
  MINGGU 3 – PENGEMBANGAN MODEL AI
================================================================

PIC: APC248D6X0317 (ML Engineer) + APC248D6X0446 (AI Analyst)

--- FILE YANG PERLU DIBUAT: 03_modeling.py ---

[A] PERSIAPAN FITUR MODEL
    Kolom fitur yang direkomendasikan:
      - GB_Yield_Total
      - GK_Yield_Total
      - Rasio_GK_GB
      - GB_Kadar_Air_Mean
      - Cetak_Yield_Kg
      - Cetak_Pct_Teoritis
      - Kemas_Pct_Teoritis
      - Total_Waste_Kg
      - Cetak_Durasi_Hari
      - Kemas_Durasi_Hari
      - (Encode) GB_Mesin_L1, Cetak_Mesin, Kemas_Mesin

    Label: Defect_Overall (0=Normal, 1=Defect)

[B] MODEL 1: ISOLATION FOREST (Deteksi Anomali)
    from sklearn.ensemble import IsolationForest

    Langkah:
    1. Latih hanya pada data fitur numerik (tanpa label)
    2. contamination = proporsi defect yang ditemukan di EDA
    3. Prediksi: -1 = anomali, 1 = normal
    4. Konversi ke 0/1 untuk evaluasi
    5. Evaluasi dengan: precision, recall, F1-score

    Contoh:
      clf = IsolationForest(contamination=0.15, random_state=42)
      clf.fit(X_scaled)
      df['IF_Pred'] = (clf.predict(X_scaled) == -1).astype(int)

[C] MODEL 2: RANDOM FOREST (Klasifikasi)
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, confusion_matrix

    Langkah:
    1. Split data: 80% train, 20% test (stratify=y)
    2. Scale fitur dengan StandardScaler
    3. Latih model
    4. Evaluasi: accuracy, precision, recall, F1, ROC-AUC
    5. Plot feature importance (bar chart)
    6. Hyperparameter tuning dengan GridSearchCV atau
       RandomizedSearchCV (n_estimators, max_depth, min_samples_leaf)

    Contoh:
      X_train, X_test, y_train, y_test = train_test_split(
          X, y, test_size=0.2, random_state=42, stratify=y
      )
      rf = RandomForestClassifier(n_estimators=200,
                                   class_weight='balanced',
                                   random_state=42)
      rf.fit(X_train, y_train)
      print(classification_report(y_test, rf.predict(X_test)))

[D] MODEL 3: K-MEANS (Clustering – Minggu 4)
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    Langkah:
    1. Scale fitur numerik
    2. Tentukan jumlah klaster optimal dengan Elbow Method
    3. Latih K-Means (k=3 sebagai starting point)
    4. Analisis profil setiap klaster
    5. Visualisasi dengan PCA 2D scatter plot

[E] EVALUASI MODEL
    Metrik utama (sesuai Project Plan):
      - Accuracy
      - Precision
      - Recall (penting! untuk mendeteksi defect)
      - F1-Score
      - Confusion Matrix (plot heatmap)
      - ROC-AUC Curve

    Simpan model dengan joblib:
      import joblib
      joblib.dump(rf, 'models/random_forest_model.pkl')
      joblib.dump(scaler, 'models/scaler.pkl')
      joblib.dump(clf, 'models/isolation_forest_model.pkl')

================================================================
  MINGGU 4 – CLUSTERING & DASHBOARD
================================================================

PIC: APC248D6X0317 (Clustering) + APC248D6Y0173 (Dashboard)

--- FILE YANG PERLU DIBUAT: 04_clustering.py & 05_dashboard.py ---

[A] CLUSTERING (K-Means)
    - Jalankan Elbow Method untuk k=2..10
    - Analisis klaster: rata-rata fitur per klaster
    - Identifikasi klaster "high defect"
    - Visualisasi PCA 2D colored by cluster
    - Analisis feature importance (korelasi dengan klaster defect)

[B] DASHBOARD (Streamlit)
    Fitur dashboard yang harus ada:
    1. Tab Overview:
       - KPI: total batch, % defect, yield rata-rata
       - Distribusi defect per produk (bar/pie chart)
    2. Tab Monitoring:
       - Tren % teoritis cetak & kemas (line chart interaktif)
       - Filter by: Material, Mesin, Bulan
    3. Tab Prediksi:
       - Input form: masukkan parameter batch baru
       - Output: prediksi Normal/Defect + probabilitas
       - Tombol "Analisis Batch"
    4. Tab Clustering:
       - Scatter plot klaster (PCA)
       - Profil setiap klaster
    5. Tab Insight:
       - Feature importance Random Forest (bar chart)
       - Faktor utama penyebab defect
       - Rekomendasi actionable

    Cara menjalankan:
      pip install streamlit
      streamlit run 05_dashboard.py

================================================================
  MINGGU 5 – INTEGRASI, TESTING & DOKUMENTASI
================================================================

PIC: APC248D6X0323 (Project Lead & MLOps)

[A] INTEGRASI SISTEM
    - Satukan pipeline: preprocessing → model → dashboard
    - Pastikan model .pkl dapat dipanggil dari dashboard
    - Uji end-to-end dengan data baru (simulasi)

[B] ALPHA TESTING (Internal)
    - Semua anggota tim menguji dashboard
    - Catat bug dan inkonsistensi
    - Fix bug prioritas tinggi

[C] BETA TESTING (Pengguna)
    - Presentasikan ke mentor/reviewer Pijak
    - Kumpulkan feedback form
    - Iterasi perbaikan berdasarkan feedback

[D] DOKUMENTASI
    File yang harus disiapkan:
    - README.md: cara install dan menjalankan sistem
    - requirements.txt: semua library yang digunakan
    - docs/technical_doc.pdf: dokumentasi teknis (arsitektur, model)
    - docs/user_guide.pdf: panduan penggunaan dashboard

    requirements.txt (minimal):
      pandas>=1.5
      numpy>=1.23
      scikit-learn>=1.1
      matplotlib>=3.6
      seaborn>=0.12
      streamlit>=1.22
      joblib>=1.2
      plotly>=5.13
      openpyxl>=3.0

[E] FINAL REVIEW & SERAH TERIMA
    Checklist:
    ☐ Semua model terlatih dan tersimpan di folder models/
    ☐ Dashboard berjalan tanpa error
    ☐ Akurasi model ≥ 85% (target awal)
    ☐ Dokumentasi teknis & user guide selesai
    ☐ Repository GitHub diperbarui (clean commit)
    ☐ Demo video (opsional, +nilai)

================================================================
  STRUKTUR FOLDER YANG DISARANKAN
================================================================

project_pjkgm016/
├── data/
│   ├── rekap_produksi_granulasi_raw.csv     ← output Langkah 0
│   └── rekap_produksi_clean.csv             ← output 01_preprocessing
├── eda_output/                              ← output 02_eda
│   ├── 01_distribusi_defect.png
│   ├── 02_distribusi_material.png
│   ├── ...
│   └── ringkasan_statistik.txt
├── models/
│   ├── random_forest_model.pkl
│   ├── isolation_forest_model.pkl
│   ├── kmeans_model.pkl
│   └── scaler.pkl
├── notebooks/
│   └── explorasi.ipynb                      ← (opsional, Jupyter)
├── 01_preprocessing.py
├── 02_eda.py
├── 03_modeling.py                           ← BUAT Minggu 3
├── 04_clustering.py                         ← BUAT Minggu 4
├── 05_dashboard.py                          ← BUAT Minggu 4
├── requirements.txt
└── README.md

================================================================
  CATATAN PENTING
================================================================

1. IMBALANCED DATA:
   Jika proporsi defect < 20%, gunakan class_weight='balanced'
   pada Random Forest, atau pertimbangkan SMOTE dari imblearn.

2. DATA LEAKAGE:
   Pastikan preprocessing (StandardScaler) hanya di-fit pada
   data train, bukan seluruh dataset.

3. CROSS-VALIDATION:
   Gunakan StratifiedKFold (k=5) untuk evaluasi model yang
   lebih robust, terutama pada dataset kecil.

4. INTERPRETASI MODEL:
   Pertimbangkan SHAP values untuk menjelaskan prediksi model
   kepada stakeholder non-teknis (sangat relevan untuk farmasi).
     pip install shap
     import shap
     explainer = shap.TreeExplainer(rf)
     shap_values = explainer.shap_values(X_test)
     shap.summary_plot(shap_values[1], X_test)

5. VERSION CONTROL:
   Commit setiap milestone ke GitHub dengan pesan yang jelas.
   Contoh commit message:
     "feat: tambah model Random Forest dengan akurasi 87%"
     "fix: perbaiki parsing kadar air"
     "docs: update README cara menjalankan dashboard"

================================================================
  KONTAK TIM
================================================================
1. Dwi Cahyani Desri     (APC248D6X0323) – AI Project Lead
2. Daniel D.P. Saragih   (APC248D6Y0099) – Data Preparation
3. Ovalia Dwi Rahmadani  (APC248D6X0317) – ML Engineer
4. Anis Setiawati        (APC248D6X0446) – AI Analyst
5. M. Sidiq Firdaus      (APC248D6Y0173) – App Developer

================================================================
  END OF DOCUMENT
================================================================
