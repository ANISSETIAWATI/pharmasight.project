"""
================================================================
  07_ai_analyst.py
  Proyek: AI-Based Pharmaceutical Data Selection & Monitoring
  PJK-GM016 | Pijak x IBM SkillsBuild
  
  FUNGSI: AI Analyst – RAG + LLM untuk analisis batch produksi
  
  Mode yang tersedia:
    1. chat     – tanya jawab interaktif via terminal
    2. api      – FastAPI endpoint untuk integrasi dashboard
    3. streamlit– siap diintegrasikan ke 05_dashboard.py
  
  Cara menjalankan:
    # Mode chat interaktif:
    python 07_ai_analyst.py --mode chat
    
    # Mode API server:
    pip install fastapi uvicorn
    python 07_ai_analyst.py --mode api
    # Akses: http://localhost:8001/docs

  Konfigurasi LLM (pilih salah satu di bagian CONFIG):
    LLM_PROVIDER = "groq"       → ✅ GRATIS, daftar di console.groq.com
    LLM_PROVIDER = "anthropic"  → Berbayar, ANTHROPIC_API_KEY
    LLM_PROVIDER = "openai"     → Berbayar, OPENAI_API_KEY
    LLM_PROVIDER = "ollama"     → Gratis lokal, perlu install Ollama

  Setup Groq (gratis):
    1. Daftar di https://console.groq.com
    2. Buat API key (gratis, tidak perlu kartu kredit)
    3. export GROQ_API_KEY="gsk_..."
    4. python 07_ai_analyst.py --mode chat
================================================================
"""

import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

# ── Vector Store & Embeddings ─────────────────────────────────
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ── LLM (import kondisional sesuai provider) ──────────────────
# from langchain_anthropic        import ChatAnthropic
# from langchain_openai           import ChatOpenAI
# from langchain_community.llms   import Ollama

# ── LangChain Core ────────────────────────────────────────────
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

# ════════════════════════════════════════════════════════════════
#  KONFIGURASI – SESUAIKAN DI SINI
# ════════════════════════════════════════════════════════════════

# ✅ DEFAULT: GROQ (gratis, daftar di https://console.groq.com)
# Pilih provider: "groq" | "anthropic" | "openai" | "ollama"
LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "groq")

# Model Groq (semua GRATIS):
#   "llama3-8b-8192"      → ringan & cepat
#   "llama3-70b-8192"     → lebih pintar (rekomendasi)
#   "mixtral-8x7b-32768"  → context window 32K token
#   "gemma2-9b-it"        → alternatif dari Google
GROQ_MODEL     = os.getenv("GROQ_MODEL", "llama3-70b-8192")

# Path ke vector store yang sudah dibangun oleh 06_build_rag.py
RAG_DB_DIR     = "./rag_db"
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

# Jumlah dokumen yang diambil dari vector store per query
RETRIEVER_K    = 5

# Warna terminal
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


# ════════════════════════════════════════════════════════════════
#  BAGIAN 1 – INISIALISASI LLM
# ════════════════════════════════════════════════════════════════

def get_llm():
    """
    Mengembalikan instance LLM berdasarkan LLM_PROVIDER.
    Pastikan API key sudah di-set sebagai environment variable.
    
    Setup Groq (GRATIS):
      1. Daftar di https://console.groq.com (tidak perlu kartu kredit)
      2. Buat API Key di menu "API Keys"
      3. Jalankan: export GROQ_API_KEY="gsk_xxxx"
    """
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY tidak ditemukan!\n"
                "Cara mendapatkan (GRATIS):\n"
                "  1. Daftar di https://console.groq.com\n"
                "  2. Buat API Key di menu API Keys\n"
                "  3. set GROQ_API_KEY=gsk_..."
            )
        print(f"  Model Groq: {GROQ_MODEL}")
        return ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=api_key,
            max_tokens=2048,
            temperature=0.1
        )

    elif LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY tidak ditemukan!\n"
                "Set dengan: export ANTHROPIC_API_KEY='sk-ant-...'"
            )
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=api_key,
            max_tokens=2048,
            temperature=0.1
        )
    
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY tidak ditemukan!\n"
                "Set dengan: export OPENAI_API_KEY='sk-...'"
            )
        return ChatOpenAI(
            model="gpt-4o",
            openai_api_key=api_key,
            max_tokens=2048,
            temperature=0.1
        )
    
    elif LLM_PROVIDER == "ollama":
        from langchain_community.llms import Ollama
        # Pastikan Ollama sudah berjalan: ollama serve
        # dan model sudah diunduh: ollama pull llama3
        return Ollama(
            model="llama3",
            temperature=0.1
        )
    
    else:
        raise ValueError(f"LLM_PROVIDER tidak valid: {LLM_PROVIDER}")


# ════════════════════════════════════════════════════════════════
#  BAGIAN 2 – SETUP RAG CHAIN
# ════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_TEMPLATE = """Kamu adalah AI Analyst untuk sistem monitoring kualitas produksi farmasi 
di perusahaan farmasi Indonesia (Proyek PJK-GM016).

Tugasmu adalah:
1. Menganalisis data batch produksi (granulasi, cetak, kemas)
2. Mengidentifikasi penyebab potensial defect
3. Memberikan rekomendasi actionable yang spesifik
4. Menjelaskan hasil model AI (Random Forest, K-Means) dengan bahasa yang mudah dipahami

Konteks dari knowledge base:
{context}

Aturan penting:
- Jawab dalam Bahasa Indonesia yang jelas dan profesional
- Gunakan data dan angka spesifik dari konteks jika tersedia
- Berikan rekomendasi yang bisa langsung dieksekusi oleh tim produksi
- Jika data tidak tersedia dalam konteks, katakan dengan jelas
- Jangan mengarang fakta atau angka

Pertanyaan: {question}

Analisis dan Rekomendasi:"""


def build_rag_chain():
    """Membangun RAG chain dari vector store yang sudah ada."""
    
    print(f"  🔍 Memuat vector store dari {RAG_DB_DIR}...")
    
    if not os.path.exists(RAG_DB_DIR):
        raise FileNotFoundError(
            f"Vector store tidak ditemukan di '{RAG_DB_DIR}'!\n"
            f"Jalankan dulu: python 06_build_rag.py"
        )
    
    # Load embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    
    # Load Chroma vector store
    vectorstore = Chroma(
        persist_directory=RAG_DB_DIR,
        embedding_function=embeddings,
        collection_name="pjkgm016_pharma"
    )
    
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K}
    )
    
    # Load LLM
    print(f"  🤖 Menginisialisasi LLM ({LLM_PROVIDER})...")
    llm = get_llm()
    
    # Buat prompt template
    prompt = PromptTemplate(
        template=SYSTEM_PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )
    
    # Bangun RAG chain
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
    
    print(f"  {GREEN}✅ RAG Chain siap!{RESET}")
    return rag_chain, vectorstore


# ════════════════════════════════════════════════════════════════
#  BAGIAN 3 – FUNGSI ANALISIS UTAMA
# ════════════════════════════════════════════════════════════════

def analyze_batch(
    batch_data: dict,
    rf_prediction: int,
    rf_probability: float,
    cluster_id: int,
    rag_chain
) -> dict:
    """
    Fungsi utama: analisis batch baru menggunakan RAG + LLM.
    
    Parameters:
        batch_data      : dict fitur batch yang akan dianalisis
        rf_prediction   : 0 (Normal) atau 1 (Defect) dari Random Forest
        rf_probability  : probabilitas defect (0.0 – 1.0)
        cluster_id      : nomor klaster K-Means (0, 1, atau 2)
        rag_chain       : instance RAG chain
    
    Returns:
        dict berisi analisis, rekomendasi, dan sumber referensi
    """
    cluster_labels = {0: "Medium Risk", 1: "Low Risk", 2: "High Risk"}
    cluster_label  = cluster_labels.get(cluster_id, f"Klaster {cluster_id}")
    pred_label     = "⚠️ DEFECT" if rf_prediction == 1 else "✅ NORMAL"
    
    # Susun query yang kaya konteks
    query = f"""
Analisis batch produksi farmasi berikut:

DATA BATCH:
- GB_Yield_Total      : {batch_data.get('GB_Yield_Total', 'N/A')} kg
- GK_Yield_Total      : {batch_data.get('GK_Yield_Total', 'N/A')} kg
- Rasio_GK_GB         : {batch_data.get('Rasio_GK_GB', 'N/A')}
- GB_Kadar_Air_Mean   : {batch_data.get('GB_Kadar_Air_Mean', 'N/A')}%
- Cetak_Yield_Kg      : {batch_data.get('Cetak_Yield_Kg', 'N/A')} kg
- Cetak_Pct_Teoritis  : {batch_data.get('Cetak_Pct_Teoritis', 'N/A')}
- Kemas_Pct_Teoritis  : {batch_data.get('Kemas_Pct_Teoritis', 'N/A')}
- Total_Waste_Kg      : {batch_data.get('Total_Waste_Kg', 'N/A')} kg
- Cetak_Durasi_Hari   : {batch_data.get('Cetak_Durasi_Hari', 'N/A')} hari
- Kemas_Durasi_Hari   : {batch_data.get('Kemas_Durasi_Hari', 'N/A')} hari

HASIL MODEL AI:
- Prediksi Random Forest : {pred_label}
- Probabilitas Defect    : {rf_probability:.1%}
- Klaster K-Means        : Klaster {cluster_id} ({cluster_label})

Berikan:
1. Analisis mengapa batch ini diprediksi {pred_label}
2. Identifikasi 2-3 faktor risiko utama berdasarkan data di atas
3. Rekomendasi tindakan spesifik yang harus diambil tim produksi
4. Apakah batch ini perlu ditahan atau bisa lanjut ke proses berikutnya?
"""
    
    result = rag_chain({"query": query})
    
    return {
        "batch_data":        batch_data,
        "rf_prediction":     pred_label,
        "rf_probability":    f"{rf_probability:.1%}",
        "cluster":           f"Klaster {cluster_id} ({cluster_label})",
        "analysis":          result["result"],
        "source_documents":  [d.page_content[:200] + "..." for d in result["source_documents"]],
        "timestamp":         datetime.now().isoformat()
    }


def general_query(question: str, rag_chain) -> dict:
    """Query umum tentang data produksi atau model AI."""
    result = rag_chain({"query": question})
    return {
        "question": question,
        "answer":   result["result"],
        "sources":  [d.metadata.get("source", "unknown") for d in result["source_documents"]],
        "timestamp": datetime.now().isoformat()
    }


def get_high_risk_summary(csv_path: str, rag_chain) -> str:
    """Ringkasan batch high-risk dengan analisis LLM."""
    try:
        df = pd.read_csv(csv_path)
        if "Cluster_Label" in df.columns:
            high_risk = df[df["Cluster_Label"].str.contains("High", na=False)]
        elif "Cluster" in df.columns:
            high_risk = df[df["Cluster"] == 2]
        else:
            return "Data klaster tidak tersedia."
        
        if high_risk.empty:
            return "Tidak ada batch high-risk ditemukan."
        
        summary = f"Terdapat {len(high_risk)} batch high-risk. "
        summary += f"Rata-rata Kemas_Pct_Teoritis: {high_risk['Kemas_Pct_Teoritis'].mean():.3f}. "
        summary += f"Rata-rata Total_Waste_Kg: {high_risk['Total_Waste_Kg'].mean():.2f} kg. "
        
        if "Material_Description" in high_risk.columns:
            top_material = high_risk["Material_Description"].value_counts().index[0]
            summary += f"Produk paling sering high-risk: {top_material}."
        
        result = rag_chain({"query": f"Berikan analisis mendalam tentang: {summary} Apa penyebab dan rekomendasi penanganannya?"})
        return result["result"]
    
    except Exception as e:
        return f"Error membaca data: {e}"


# ════════════════════════════════════════════════════════════════
#  BAGIAN 4 – MODE CHAT INTERAKTIF
# ════════════════════════════════════════════════════════════════

CONTOH_PERTANYAAN = [
    "Apa faktor utama penyebab defect berdasarkan model Random Forest?",
    "Bagaimana cara membedakan batch normal dan defect dari data Kemas_Pct_Teoritis?",
    "Klaster mana yang paling berisiko dan apa rekomendasinya?",
    "Apa threshold Kemas_Durasi_Hari yang normal untuk proses pengemasan?",
    "Bagaimana interpretasi nilai Rasio_GK_GB = 2.5?",
]

def run_chat_mode(rag_chain):
    """Mode chat interaktif di terminal."""
    print(f"\n{BOLD}{CYAN}{'='*60}")
    print(f"  🤖 AI ANALYST – PJK-GM016")
    print(f"  Mode: Chat Interaktif")
    print(f"  LLM : {LLM_PROVIDER.upper()}")
    print(f"{'='*60}{RESET}\n")
    
    print(f"{YELLOW}Contoh pertanyaan yang bisa kamu tanyakan:{RESET}")
    for i, q in enumerate(CONTOH_PERTANYAAN, 1):
        print(f"  {i}. {q}")
    
    print(f"\n{YELLOW}Ketik 'quit' atau 'exit' untuk keluar.{RESET}")
    print(f"{YELLOW}Ketik 'batch' untuk demo analisis batch otomatis.{RESET}\n")
    
    while True:
        try:
            user_input = input(f"{BOLD}{CYAN}Kamu: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{GREEN}Sampai jumpa!{RESET}")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ["quit", "exit"]:
            print(f"{GREEN}Sampai jumpa!{RESET}")
            break
        
        if user_input.lower() == "batch":
            # Demo analisis batch dengan data contoh
            demo_batch = {
                "GB_Yield_Total":     425.72,
                "GK_Yield_Total":     908.38,
                "Rasio_GK_GB":        2.13,
                "GB_Kadar_Air_Mean":  5.42,
                "Cetak_Yield_Kg":     712.0,
                "Cetak_Pct_Teoritis": 2.82,
                "Kemas_Pct_Teoritis": 2.78,
                "Total_Waste_Kg":     0.0,
                "Cetak_Durasi_Hari":  0.0,
                "Kemas_Durasi_Hari":  0.0,
            }
            print(f"\n{YELLOW}[Demo] Menganalisis batch contoh...{RESET}")
            result = analyze_batch(demo_batch, rf_prediction=0, rf_probability=0.12,
                                   cluster_id=1, rag_chain=rag_chain)
            print(f"\n{BOLD}{GREEN}AI Analyst:{RESET}")
            print(result["analysis"])
            print()
            continue
        
        print(f"\n{YELLOW}[Menganalisis...]{RESET}")
        try:
            result = general_query(user_input, rag_chain)
            print(f"\n{BOLD}{GREEN}AI Analyst:{RESET}")
            print(result["answer"])
            print()
        except Exception as e:
            print(f"{RED}[ERROR] {e}{RESET}\n")


# ════════════════════════════════════════════════════════════════
#  BAGIAN 5 – MODE API (FastAPI)
# ════════════════════════════════════════════════════════════════

def run_api_mode(rag_chain):
    """
    Jalankan FastAPI server untuk integrasi dengan dashboard.
    Endpoint tersedia di http://localhost:8001/docs
    """
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        import uvicorn
    except ImportError:
        print(f"{RED}[ERROR] Instal dulu: pip install fastapi uvicorn{RESET}")
        sys.exit(1)
    
    app = FastAPI(
        title="PJK-GM016 AI Analyst API",
        description="RAG + LLM untuk analisis batch produksi farmasi",
        version="1.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # ── Schema ────────────────────────────────────────────────
    class BatchAnalysisRequest(BaseModel):
        batch_data:      dict
        rf_prediction:   int   = 0
        rf_probability:  float = 0.0
        cluster_id:      int   = 0
    
    class QuestionRequest(BaseModel):
        question: str
    
    # ── Endpoints ─────────────────────────────────────────────
    @app.get("/")
    def root():
        return {"message": "PJK-GM016 AI Analyst API", "status": "running"}
    
    @app.get("/health")
    def health():
        return {
            "status": "healthy",
            "llm_provider": LLM_PROVIDER,
            "rag_db": RAG_DB_DIR,
            "timestamp": datetime.now().isoformat()
        }
    
    @app.post("/analyze/batch")
    def api_analyze_batch(req: BatchAnalysisRequest):
        """Analisis batch baru dengan konteks prediksi model ML."""
        try:
            result = analyze_batch(
                batch_data=req.batch_data,
                rf_prediction=req.rf_prediction,
                rf_probability=req.rf_probability,
                cluster_id=req.cluster_id,
                rag_chain=rag_chain
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/analyze/question")
    def api_general_question(req: QuestionRequest):
        """Pertanyaan umum tentang data produksi atau model AI."""
        try:
            return general_query(req.question, rag_chain)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/analyze/high-risk-summary")
    def api_high_risk_summary(csv_path: str = "./data/rekap_produksi_clustered.csv"):
        """Ringkasan analisis batch high-risk."""
        summary = get_high_risk_summary(csv_path, rag_chain)
        return {"summary": summary, "timestamp": datetime.now().isoformat()}
    
    # ── Contoh pertanyaan preset ──────────────────────────────
    @app.get("/examples")
    def api_examples():
        return {"example_questions": CONTOH_PERTANYAAN}
    
    print(f"\n{GREEN}{BOLD}API Server berjalan di: http://localhost:8001{RESET}")
    print(f"Dokumentasi API    : http://localhost:8001/docs")
    print(f"Tekan CTRL+C untuk berhenti.\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")


# ════════════════════════════════════════════════════════════════
#  BAGIAN 6 – FUNGSI SIAP PAKAI UNTUK DASHBOARD STREAMLIT
# ════════════════════════════════════════════════════════════════

def get_analyst_for_streamlit():
    """
    Fungsi ini dipanggil dari 05_dashboard.py.
    Mengembalikan fungsi analyze dan query yang siap dipakai.
    
    Contoh penggunaan di 05_dashboard.py:
    
        from 07_ai_analyst import get_analyst_for_streamlit
        analyze_fn, query_fn = get_analyst_for_streamlit()
        
        # Di dalam tab AI:
        result = analyze_fn(batch_data, rf_pred, rf_prob, cluster)
        st.write(result["analysis"])
    """
    rag_chain, _ = build_rag_chain()
    
    def _analyze(batch_data, rf_prediction, rf_probability, cluster_id):
        return analyze_batch(batch_data, rf_prediction, rf_probability,
                             cluster_id, rag_chain)
    
    def _query(question):
        return general_query(question, rag_chain)
    
    return _analyze, _query


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="PJK-GM016 AI Analyst – RAG + LLM"
    )
    parser.add_argument(
        "--mode",
        choices=["chat", "api"],
        default="chat",
        help="Mode: 'chat' (terminal interaktif) atau 'api' (FastAPI server)"
    )
    parser.add_argument(
        "--provider",
        choices=["groq", "anthropic", "openai", "ollama"],
        default=None,
        help="Override LLM provider"
    )
    args = parser.parse_args()
    
    # Override provider jika diberikan via CLI
    global LLM_PROVIDER
    if args.provider:
        LLM_PROVIDER = args.provider
    
    print(f"\n{BOLD}{'='*60}")
    print(f"  07_AI_ANALYST.PY – PJK-GM016")
    print(f"  LLM Provider: {LLM_PROVIDER.upper()}")
    print(f"  Mode        : {args.mode.upper()}")
    print(f"{'='*60}{RESET}\n")
    
    # Build RAG chain
    print(f"{BOLD}[Inisialisasi]{RESET}")
    rag_chain, _ = build_rag_chain()
    
    # Jalankan mode yang dipilih
    if args.mode == "chat":
        run_chat_mode(rag_chain)
    elif args.mode == "api":
        run_api_mode(rag_chain)


if __name__ == "__main__":
    main()