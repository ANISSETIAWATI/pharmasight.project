import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
from groq import Groq
import chromadb

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Izinkan React kamu
    allow_credentials=True,
    allow_methods=["*"], # Izinkan semua jenis perintah (GET, POST, dll)
    allow_headers=["*"], # Izinkan semua jenis header
)

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
# 1. Load Model, Scaler, dan Features
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(BASE_DIR, "rekap_produksi_clustered.csv")
# Menyambungkan jalur ke file model dengan aman
model_path = os.path.join(BASE_DIR, "models", "random_forest_model.pkl")
scaler_path = os.path.join(BASE_DIR, "models", "scaler.pkl")

df = pd.read_csv(csv_path)

# Load model & scaler
model = joblib.load(model_path)
scaler = joblib.load(scaler_path)
with open("models/feature_cols.txt", "r") as f:
    feature_cols = f.read().splitlines()

# 2. Setup Koneksi ke Groq & ChromaDB (RAG)
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # <--- ISI API KEY KAMU DI SINI
groq_client = Groq(api_key=GROQ_API_KEY)

# Membuka database ChromaDB lokal yang baru saja dibuat
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="koleksi_produksi")

# 3. Endpoint khusus /predict
@app.post("/predict")
async def predict(data: dict):
    # 1. Ambil data dari React
    user_query = data.get("user_query", "")
    chat_history = data.get("history", []) # Mengambil riwayat chat
    
    # --- PROSES MACHINE LEARNING (Tetap dipertahankan sebagai konteks) ---
    df = pd.DataFrame([data])
    # Pastikan hanya kolom fitur yang masuk ke model
    df_input = df.reindex(columns=feature_cols, fill_value=0)
    df_scaled = scaler.transform(df_input)
    pred_value = model.predict(df_scaled)[0]
    hasil_prediksi = "Bad/Defect" if pred_value == 1 else "Good/Lolos"
    
    # --- PROSES RAG (KONTEKS HISTORIS) ---
    query_text = f"Material {data.get('Material_Description')} dengan status {hasil_prediksi}"
    pencarian = collection.query(query_texts=[query_text], n_results=2)
    konteks_sejarah = "\n".join(pencarian['documents'][0])
    
    # --- PROSES LLM (GROQ) DENGAN RIWAYAT CHAT ---
    # Instruksi sistem agar AI tidak kaku
    system_instruction = f"""
    Anda adalah PharmaSight AI Analyst yang profesional.
    Tugas Anda adalah memberikan laporan analisis kualitas yang rapi, terstruktur, dan mudah dibaca oleh operator pabrik.

    FORMAT PENULISAN:
    1. Gunakan **Markdown** untuk memperjelas informasi.
    2. Gunakan **Bold** (tebal) untuk istilah teknis, status batch, dan angka penting.
    3. Gunakan **Bullet Points** (poin-poin) jika ada lebih dari satu alasan atau histori.
    4. Pisahkan setiap bagian (Pendahuluan, Analisis Parameter, Histori RAG, dan Rekomendasi) dengan baris baru.

    KONTEKS BATCH SAAT INI:
    - Produk: {data.get('Material_Description')}
    - Hasil Prediksi: **{hasil_prediksi}**
    - Parameter Utama: GK/GB {data.get('Rasio_GK_GB')}, Air {data.get('GB_Kadar_Air_Mean')}%, Waste {data.get('Total_Waste_Kg')}kg.

    DATA HISTORIS (RAG):
    {konteks_sejarah}

    Aturan Respon:
    - Jika memberikan analisis, bagi menjadi poin-poin agar tidak menumpuk.
    - Pastikan nada bicara tetap profesional namun membantu.
    """

    # Menyusun pesan untuk Groq (System + History + Query Terbaru)
    messages = [{"role": "system", "content": system_instruction}]
    
    # Tambahkan riwayat chat agar AI "ingat" konteks sebelumnya
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Tambahkan pertanyaan user saat ini
    messages.append({"role": "user", "content": user_query})

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=messages, # Menggunakan variabel messages yang sudah lengkap
            model="llama-3.1-8b-instant",
            temperature=0.5 # Sedikit dinaikkan agar lebih kreatif saat chatting
        )
        llm_explanation = chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error Groq: {e}")
        llm_explanation = "Maaf, koneksi ke otak AI sedang terganggu. Coba kirim pesan lagi ya."

    return {
        "prediction_code": int(pred_value),
        "prediction_status": hasil_prediksi,
        "llm_explanation": llm_explanation
    }

@app.get("/api/dashboard-stats")
def get_dashboard_stats():
    # 1. Load dataset asli
    df = pd.read_csv("rekap_produksi_clustered.csv")

    # 2. Hitung statistik untuk KPI
    total_batches = len(df)
    defect_count = len(df[df['Defect_Overall'] == 1])
    defect_rate = round((defect_count / total_batches) * 100, 2)
    
    # 3. Ambil 10 data terbaru untuk tabel di React
    recent_batches = df.tail(10).to_dict(orient="records")

    # 4. Ambil 7 data terakhir untuk grafik tren sederhana
    trend_df = df.tail(7)
    trend_data = []
    for i, row in trend_df.iterrows():
        trend_data.append({
            "name": f"B{i}", 
            "good": 1 if row['Defect_Overall'] == 0 else 0,
            "bad": 1 if row['Defect_Overall'] == 1 else 0
        })

    # 5. Kembalikan semua data yang dibutuhkan dashboard
    return {
        "total_batches": total_batches,
        "defect_rate": defect_rate,
        "good_batches": total_batches - defect_count,
        "bad_batches": defect_count,
        "recent_batches": recent_batches,
        "trend_data": trend_data
    }

@app.get("/api/batch-history")
def get_batch_history(skip: int = 0, limit: int = 50, status: str = "all"):
    # 1. Load dataset asli
    df = pd.read_csv("rekap_produksi_clustered.csv")

    # 2. Filter berdasarkan status jika diperlukan
    if status == "good":
        df = df[df['Defect_Overall'] == 0]
    elif status == "bad":
        df = df[df['Defect_Overall'] == 1]

    # 3. Sort descending (data terbaru dulu)
    df = df.iloc[::-1]

    # 4. Apply pagination
    total_records = len(df)
    df_paginated = df.iloc[skip:skip + limit]

    # 5. Format data untuk frontend
    batches = []
    for i, row in df_paginated.iterrows():
        batches.append({
            "id": f"B{i:04d}",
            "material": row['Material_Description'],
            "gk_gb": float(row['Rasio_GK_GB']),
            "air": float(row['GB_Kadar_Air_Mean']),
            "waste": float(row['Total_Waste_Kg']),
            "defect": int(row['Defect_Overall']),
            "cluster": row['Cluster_Label'],
            "bulan": int(row['Bulan_Produksi'])
        })

    return {
        "total": total_records,
        "skip": skip,
        "limit": limit,
        "batches": batches
    }