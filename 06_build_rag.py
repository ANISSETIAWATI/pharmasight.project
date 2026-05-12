"""
================================================================
  06_build_rag.py
  Proyek: AI-Based Pharmaceutical Data Selection & Monitoring
  PJK-GM016 | Pijak x IBM SkillsBuild
  
  FUNGSI: Membangun Knowledge Base (Vector Store) untuk RAG
  
  Cara menjalankan:
    pip install langchain langchain-community chromadb \
                sentence-transformers pandas
    python 06_build_rag.py
================================================================
"""

import os
import json
import pandas as pd
from pathlib import Path

# ── LangChain & Vector Store ──────────────────────────────────
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ── Konfigurasi ───────────────────────────────────────────────
RAG_DB_DIR     = "./rag_db"
KB_DIR         = "./knowledge_base"

# ── Sesuaikan path CSV dengan lokasi file kamu ────────────────
# Cari otomatis di folder yang sama dengan script ini
import pathlib
_SCRIPT_DIR    = pathlib.Path(__file__).parent.resolve()
DATA_CLUSTERED = str(_SCRIPT_DIR / "rekap_produksi_clustered.csv")
DATA_CLEAN     = str(_SCRIPT_DIR / "rekap_produksi_clean.csv")
# Kalau CSV ada di subfolder data/, ubah jadi:
# DATA_CLUSTERED = str(_SCRIPT_DIR / "data" / "rekap_produksi_clustered.csv")
# DATA_CLEAN     = str(_SCRIPT_DIR / "data" / "rekap_produksi_clean.csv")

# Model embedding multilingual (gratis, berjalan lokal)
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

# ── Warna terminal (opsional, untuk log yang lebih rapi) ──────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


# ════════════════════════════════════════════════════════════════
#  BAGIAN 1 – GENERATE KNOWLEDGE BASE OTOMATIS DARI DATA
# ════════════════════════════════════════════════════════════════

def generate_eda_summary(df_clean: pd.DataFrame) -> str:
    """Membuat ringkasan EDA dari DataFrame clean."""
    defect_rate = df_clean["Defect_Overall"].mean() * 100
    total_batch = len(df_clean)
    
    material_defect = (
        df_clean.groupby("Material_Description")["Defect_Overall"]
        .mean()
        .sort_values(ascending=False)
        .head(5)
    )
    
    summary = f"""
RINGKASAN DATASET PRODUKSI FARMASI – PJK-GM016
===============================================

STATISTIK UMUM:
- Total batch produksi: {total_batch}
- Defect rate keseluruhan: {defect_rate:.2f}%
- Batch normal: {(df_clean['Defect_Overall'] == 0).sum()} ({100 - defect_rate:.2f}%)
- Batch defect: {(df_clean['Defect_Overall'] == 1).sum()} ({defect_rate:.2f}%)

STATISTIK FITUR UTAMA (rata-rata):
- GB_Yield_Total rata-rata    : {df_clean['GB_Yield_Total'].mean():.2f} kg
- GK_Yield_Total rata-rata    : {df_clean['GK_Yield_Total'].mean():.2f} kg
- Rasio_GK_GB rata-rata       : {df_clean['Rasio_GK_GB'].mean():.3f}
- GB_Kadar_Air_Mean rata-rata : {df_clean['GB_Kadar_Air_Mean'].mean():.2f}%
- Cetak_Pct_Teoritis rata-rata: {df_clean['Cetak_Pct_Teoritis'].mean():.3f}
- Kemas_Pct_Teoritis rata-rata: {df_clean['Kemas_Pct_Teoritis'].mean():.3f}
- Total_Waste_Kg rata-rata    : {df_clean['Total_Waste_Kg'].mean():.2f} kg

TOP 5 MATERIAL DENGAN DEFECT RATE TERTINGGI:
"""
    for material, rate in material_defect.items():
        summary += f"  - {material}: {rate*100:.1f}%\n"
    
    return summary


def generate_cluster_interpretation() -> str:
    return """
INTERPRETASI KLASTER:
- Klaster 0 (Medium Risk): Batch dengan volume GB tinggi,
  kadar air rendah (~3.7%), persen teoritis rendah (~0.97).
  Risiko defect sedang, perlu monitoring pada Kemas_Pct_Teoritis.

- Klaster 1 (Low Risk): Batch dengan Rasio_GK_GB tertinggi (2.15),
  kadar air tertinggi (~5.5%), persen teoritis cetak/kemas tinggi (~2.9).
  Hampir tidak ada defect, produksi berjalan optimal.

- Klaster 2 (High Risk): Batch dengan volume GK kecil (351 kg),
  total waste tertinggi (~11.3 kg), durasi kemas paling lama (~2 hari).
  Defect rate tertinggi. Waspadai batch pada klaster ini.
"""

def generate_cluster_profile(df_clustered: pd.DataFrame) -> str:
    """Membuat profil setiap klaster untuk knowledge base."""
    cluster_labels = {
        0: "Medium Risk (defect ~2.0%)",
        1: "Low Risk (defect ~0.0%)",
        2: "High Risk (defect ~2.9%)"
    }
    
    feature_cols = [
        "GB_Yield_Total", "GK_Yield_Total", "Rasio_GK_GB",
        "GB_Kadar_Air_Mean", "Cetak_Yield_Kg", "Cetak_Pct_Teoritis",
        "Kemas_Pct_Teoritis", "Total_Waste_Kg", "Cetak_Durasi_Hari",
        "Kemas_Durasi_Hari", "Bulan_Produksi"
    ]
    
    text = "PROFIL KLASTER K-MEANS (K=3) – HASIL ANALISIS CLUSTERING\n"
    text += "=" * 60 + "\n\n"
    
    # Jika DataFrame kosong, gunakan profil statis dari hasil analisis
    if df_clustered.empty or "Cluster" not in df_clustered.columns:
        text += """KLASTER 0 – Medium Risk (defect ~2.0%)
  Jumlah batch: ~200
  GB_Yield_Total rata-rata  : 623.35
  GK_Yield_Total rata-rata  : 965.59
  Rasio_GK_GB rata-rata     : 1.57
  GB_Kadar_Air_Mean         : 3.72
  Cetak_Pct_Teoritis        : 0.97
  Kemas_Pct_Teoritis        : 0.97
  Total_Waste_Kg            : 0.0

KLASTER 1 – Low Risk (defect ~0.0%)
  Jumlah batch: ~350
  GB_Yield_Total rata-rata  : 427.44
  GK_Yield_Total rata-rata  : 920.82
  Rasio_GK_GB rata-rata     : 2.15
  GB_Kadar_Air_Mean         : 5.47
  Cetak_Pct_Teoritis        : 2.91
  Kemas_Pct_Teoritis        : 2.86
  Total_Waste_Kg            : 0.0

KLASTER 2 – High Risk (defect ~2.9%)
  Jumlah batch: ~70
  GB_Yield_Total rata-rata  : 601.09
  GK_Yield_Total rata-rata  : 351.62
  Rasio_GK_GB rata-rata     : 0.64
  GB_Kadar_Air_Mean         : 4.73
  Cetak_Pct_Teoritis        : 0.97
  Kemas_Pct_Teoritis        : 0.96
  Total_Waste_Kg            : 11.28
"""
        text += generate_cluster_interpretation()
        return text

    for cluster_id in sorted(df_clustered["Cluster"].unique()):
        subset = df_clustered[df_clustered["Cluster"] == cluster_id]
        label  = cluster_labels.get(cluster_id, f"Klaster {cluster_id}")
        
        text += f"KLASTER {cluster_id} – {label}\n"
        text += f"  Jumlah batch: {len(subset)}\n"
        text += f"  Karakteristik rata-rata:\n"
        
        for col in feature_cols:
            if col in subset.columns:
                text += f"    - {col}: {subset[col].mean():.3f}\n"
        
        text += "\n"
    
    text += """
INTERPRETASI KLASTER:
- Klaster 0 (Medium Risk): Batch dengan volume GB tinggi, 
  kadar air rendah (~3.7%), persen teoritis rendah (~0.97). 
  Risiko defect sedang, perlu monitoring pada Kemas_Pct_Teoritis.

- Klaster 1 (Low Risk): Batch dengan Rasio_GK_GB tertinggi (2.15),
  kadar air tertinggi (~5.5%), persen teoritis cetak/kemas tinggi (~2.9).
  Hampir tidak ada defect, produksi berjalan optimal.

- Klaster 2 (High Risk): Batch dengan volume GK kecil (351 kg),
  total waste tertinggi (~11.3 kg), durasi kemas paling lama (~2 hari).
  Defect rate tertinggi. Waspadai batch pada klaster ini.
"""
    return text


def generate_feature_importance_doc() -> str:
    """Dokumen penjelasan feature importance dari Random Forest."""
    return """
FEATURE IMPORTANCE – RANDOM FOREST (PJK-GM016)
===============================================

Berdasarkan hasil pelatihan model Random Forest, berikut urutan
fitur yang paling berpengaruh terhadap prediksi defect:

TOP 5 FITUR PALING PENTING:
1. Kemas_Pct_Teoritis  (0.4565) ← DOMINAN, ~45.6% pengaruh total
2. Kemas_Durasi_Hari   (0.1488) ← Durasi pengemasan
3. Cetak_Pct_Teoritis  (0.0696) ← Persen teoritis pencetakan
4. GB_Yield_Total      (0.0690) ← Yield granulasi basah
5. GK_Yield_Total      (0.0579) ← Yield granulasi kering

FITUR LAINNYA (kontribusi lebih kecil):
6.  Cetak_Yield_Kg     (0.0433)
7.  Rasio_GK_GB        (0.0427)
8.  GB_Kadar_Air_Mean  (0.0400)
9.  Kemas_Mesin_enc    (0.0210)
10. Cetak_Durasi_Hari  (0.0170)
11. Bulan_Produksi     (0.0163)
12. Cetak_Mesin_enc    (0.0113)
13. GB_Mesin_L1_enc    (0.0056)
14. Total_Waste_Kg     (0.0009)

IMPLIKASI OPERASIONAL:
- Kemas_Pct_Teoritis adalah indikator utama kualitas batch.
  Nilai > 1.0 menandakan efisiensi di atas teori (anomali).
  Nilai < 0.95 menandakan loss signifikan.
- Kemas_Durasi_Hari yang terlalu panjang (>2 hari) berkorelasi
  dengan peningkatan risiko defect.
- Pemantauan ketat pada proses pengemasan (Kemas) lebih kritikal
  dibanding proses sebelumnya (Granulasi, Cetak).

PERFORMA MODEL:
- Random Forest Default: F1-Score = 0.800
- Random Forest Tuned  : F1-Score = 0.800  
- ROC-AUC              : 1.000
- 5-Fold CV Mean F1    : 0.880
- Isolation Forest     : F1-Score = 0.000 (tidak efektif untuk dataset ini)
"""


def generate_domain_knowledge() -> str:
    """Pengetahuan domain farmasi untuk konteks RAG."""
    return """
PENGETAHUAN DOMAIN – PROSES PRODUKSI FARMASI (TABLET)
======================================================

TAHAPAN PRODUKSI:
1. GRANULASI BASAH (GB):
   - Tujuan: Membentuk granul dari serbuk aktif + eksipien
   - Parameter kritis: Kadar air granul (biasanya 2-6%)
   - Mesin: Fluid Bed Dryer, High Shear Mixer
   - Yield: Berat granul kering / berat bahan awal × 100%
   - Defect umum: Kadar air terlalu tinggi → lengket, terlalu 
     rendah → friabel

2. GRANULASI KERING (GK):
   - Tujuan: Kompaksi granul yang tidak tahan panas/air
   - Parameter kritis: Rasio GK/GB (idealnya 1.5–2.5)
   - Yield: Berat granul kering / yield GB × 100%

3. PENCETAKAN / CETAK (Tablet Press):
   - Tujuan: Mengompres granul menjadi tablet
   - Parameter kritis: Kekerasan, friabilitas, disintegrasi
   - Pct_Teoritis: Yield aktual / yield teoritis × 100%
   - Nilai ideal: mendekati 1.0 (100% dari teori)
   - Durasi: Normalnya selesai dalam 1 hari

4. PENGEMASAN / KEMAS (Blister & Strip):
   - Tujuan: Pengemasan tablet ke blister/strip
   - Parameter kritis: Sealing kualitas, forming, reject blister
   - Pct_Teoritis: Tablet dikemas / tablet tersedia × 100%
   - Nilai ideal: mendekati 1.0
   - Durasi: Normalnya 1–2 hari

DEFINISI DEFECT:
- Defect_Cetak: Yield pencetakan di bawah batas minimum atau 
  ada catatan keterangan masalah kualitas
- Defect_Kemas: Yield pengemasan di bawah batas atau reject tinggi
- Defect_Overall: 1 jika Defect_Cetak ATAU Defect_Kemas = 1

THRESHOLD KRITIS (berdasarkan data historis):
- Kemas_Pct_Teoritis > 1.5 : sangat mencurigakan, kemungkinan 
  data error atau pengemasan tidak sesuai SOP
- Kemas_Durasi_Hari > 2    : perlu investigasi penyebab delay
- Total_Waste_Kg > 50       : waste berlebih, perlu audit proses
- GB_Kadar_Air_Mean > 6%   : granul terlalu basah

REKOMENDASI TINDAKAN BERDASARKAN KLASTER:
- High Risk (K2): Audit segera, tinjau SOP kemas, cek mesin sealing
- Medium Risk (K0): Monitoring ketat Kemas_Pct_Teoritis
- Low Risk (K1)  : Lanjutkan dengan monitoring rutin

REFERENSI REGULASI:
- CPOB (Cara Pembuatan Obat yang Baik) – BPOM RI
- Good Manufacturing Practice (GMP) – WHO
- ICH Q10 Pharmaceutical Quality System
"""


# ════════════════════════════════════════════════════════════════
#  BAGIAN 2 – MEMUAT & MEMPROSES DOKUMEN DARI FOLDER KB
# ════════════════════════════════════════════════════════════════

def load_knowledge_base_files(kb_dir: str) -> list[Document]:
    """Memuat semua file .txt dan .md dari folder knowledge_base/."""
    docs = []
    kb_path = Path(kb_dir)
    
    if not kb_path.exists():
        print(f"{YELLOW}[WARN] Folder {kb_dir} tidak ditemukan, dilewati.{RESET}")
        return docs
    
    for file_path in kb_path.glob("**/*"):
        if file_path.suffix in [".txt", ".md", ".pdf"]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                docs.append(Document(
                    page_content=content,
                    metadata={"source": str(file_path), "type": "knowledge_base"}
                ))
                print(f"  ✅ Loaded: {file_path.name}")
            except Exception as e:
                print(f"  {RED}❌ Error loading {file_path}: {e}{RESET}")
    
    return docs


def load_csv_as_documents(csv_path: str, max_rows: int = 200) -> list[Document]:
    """
    Konversi baris-baris CSV menjadi dokumen teks untuk RAG.
    Hanya ambil max_rows baris untuk menghindari token overflow.
    """
    docs = []
    try:
        df = pd.read_csv(csv_path)
        # Ambil sampel representatif: defect + normal
        if "Defect_Overall" in df.columns:
            defect_df = df[df["Defect_Overall"] == 1]
            normal_df = df[df["Defect_Overall"] == 0].sample(
                min(max_rows - len(defect_df), len(df[df["Defect_Overall"] == 0])),
                random_state=42
            )
            sample_df = pd.concat([defect_df, normal_df])
        else:
            sample_df = df.head(max_rows)
        
        for _, row in sample_df.iterrows():
            text = f"Data Batch Produksi:\n"
            for col in row.index:
                text += f"  {col}: {row[col]}\n"
            
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": csv_path,
                    "type": "batch_data",
                    "defect": str(row.get("Defect_Overall", "unknown"))
                }
            ))
    except Exception as e:
        print(f"{RED}[ERROR] Gagal memuat CSV {csv_path}: {e}{RESET}")
    
    return docs


# ════════════════════════════════════════════════════════════════
#  BAGIAN 3 – MAIN: BUILD VECTOR STORE
# ════════════════════════════════════════════════════════════════

def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  06_BUILD_RAG.PY – PJK-GM016{RESET}")
    print(f"{BOLD}  Membangun Knowledge Base untuk AI Analyst{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    # ── Step 1: Buat folder knowledge_base jika belum ada ─────
    os.makedirs(KB_DIR, exist_ok=True)
    os.makedirs(RAG_DB_DIR, exist_ok=True)
    
    # ── Step 2: Generate dokumen domain otomatis ──────────────
    print(f"{BOLD}[1/5] Generating domain knowledge documents...{RESET}")
    
    auto_docs_content = {}
    
    # Load data untuk generate summary
    # Coba load CSV, fallback ke template statis jika tidak ditemukan
    df_clean_loaded     = False
    df_clustered_loaded = False

    if os.path.exists(DATA_CLEAN):
        try:
            df_clean = pd.read_csv(DATA_CLEAN)
            auto_docs_content["01_eda_summary.txt"] = generate_eda_summary(df_clean)
            df_clean_loaded = True
            print(f"  {GREEN}✅ rekap_produksi_clean.csv loaded{RESET}")
        except Exception as e:
            print(f"  {YELLOW}[WARN] Gagal baca clean CSV: {e}{RESET}")
    else:
        print(f"  {YELLOW}[WARN] rekap_produksi_clean.csv tidak ditemukan di: {DATA_CLEAN}{RESET}")
        print(f"  {YELLOW}        Gunakan template statis.{RESET}")

    if os.path.exists(DATA_CLUSTERED):
        try:
            df_clustered = pd.read_csv(DATA_CLUSTERED)
            auto_docs_content["02_cluster_profile.txt"] = generate_cluster_profile(df_clustered)
            df_clustered_loaded = True
            print(f"  {GREEN}✅ rekap_produksi_clustered.csv loaded{RESET}")
        except Exception as e:
            print(f"  {YELLOW}[WARN] Gagal baca clustered CSV: {e}{RESET}")
            auto_docs_content["02_cluster_profile.txt"] = generate_cluster_profile(pd.DataFrame())
    else:
        print(f"  {YELLOW}[WARN] rekap_produksi_clustered.csv tidak ditemukan di: {DATA_CLUSTERED}{RESET}")
        print(f"  {YELLOW}        Gunakan template statis.{RESET}")
        auto_docs_content["02_cluster_profile.txt"] = generate_cluster_profile(pd.DataFrame())
    
    auto_docs_content["03_feature_importance.txt"] = generate_feature_importance_doc()
    auto_docs_content["04_domain_knowledge.txt"]   = generate_domain_knowledge()
    
    # Simpan ke folder knowledge_base/
    for filename, content in auto_docs_content.items():
        filepath = os.path.join(KB_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  {GREEN}✅ Saved: {filename}{RESET}")
    
    # ── Step 3: Kumpulkan semua dokumen ───────────────────────
    print(f"\n{BOLD}[2/5] Mengumpulkan semua dokumen...{RESET}")
    all_documents = []
    
    # Dokumen dari auto-generate
    for filename, content in auto_docs_content.items():
        all_documents.append(Document(
            page_content=content,
            metadata={"source": filename, "type": "auto_generated"}
        ))
    
    # Dokumen tambahan dari folder knowledge_base/ (SOP manual, dll)
    kb_docs = load_knowledge_base_files(KB_DIR)
    # Filter yang sudah di-generate agar tidak dobel
    extra_kb = [d for d in kb_docs if "auto_generated" not in d.metadata.get("type", "")]
    all_documents.extend(extra_kb)
    
    # Data batch dari CSV (untuk query berbasis data aktual)
    try:
        csv_docs = load_csv_as_documents(DATA_CLUSTERED, max_rows=150)
        all_documents.extend(csv_docs)
        print(f"  {GREEN}✅ {len(csv_docs)} dokumen batch dari CSV{RESET}")
    except Exception as e:
        print(f"  {YELLOW}[WARN] Skip CSV docs: {e}{RESET}")
    
    print(f"  {GREEN}✅ Total dokumen terkumpul: {len(all_documents)}{RESET}")
    
    # ── Step 4: Chunking ──────────────────────────────────────
    print(f"\n{BOLD}[3/5] Memotong dokumen menjadi chunks...{RESET}")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(all_documents)
    print(f"  {GREEN}✅ Total chunks: {len(chunks)}{RESET}")
    
    # ── Step 5: Buat Embeddings & Simpan ke Chroma ───────────
    print(f"\n{BOLD}[4/5] Membuat embeddings (ini bisa memakan waktu)...{RESET}")
    print(f"  Model: {EMBEDDING_MODEL}")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    
    print(f"\n{BOLD}[5/5] Menyimpan ke ChromaDB...{RESET}")
    
    # Hapus DB lama jika ada untuk rebuild
    import shutil
    if os.path.exists(RAG_DB_DIR):
        shutil.rmtree(RAG_DB_DIR)
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=RAG_DB_DIR,
        collection_name="pjkgm016_pharma"
    )
    vectorstore.persist()
    
    # ── Simpan metadata ───────────────────────────────────────
    metadata = {
        "total_documents": len(all_documents),
        "total_chunks":    len(chunks),
        "embedding_model": EMBEDDING_MODEL,
        "rag_db_dir":      RAG_DB_DIR,
        "kb_dir":          KB_DIR,
        "files_generated": list(auto_docs_content.keys())
    }
    with open(os.path.join(RAG_DB_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{GREEN}{BOLD}{'='*60}")
    print(f"  ✅ RAG Knowledge Base berhasil dibangun!")
    print(f"  📁 Lokasi DB   : {RAG_DB_DIR}/")
    print(f"  📚 Total Chunks: {len(chunks)}")
    print(f"  🔤 Model Embed : {EMBEDDING_MODEL}")
    print(f"{'='*60}{RESET}\n")
    print(f"Langkah selanjutnya: jalankan {BOLD}python 07_ai_analyst.py{RESET}")


if __name__ == "__main__":
    main()