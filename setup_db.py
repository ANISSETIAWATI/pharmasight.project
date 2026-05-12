import pandas as pd
import chromadb
import os

print("1. Membaca data CSV...")
# Pastikan nama file CSV sesuai dengan yang kamu miliki
df = pd.read_csv("rekap_produksi_clustered.csv")

# Kita ambil 100 data terakhir agar proses pembuatan DB cepat
df = df.tail(100).reset_index(drop=True) 

print("2. Menyiapkan ChromaDB lokal...")
# Database akan disimpan di folder bernama 'chroma_db'
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="koleksi_produksi")

print("3. Memproses data menjadi vektor (mungkin butuh waktu 1-2 menit untuk unduh model pertama kali)...")
documents = []
metadatas = []
ids = []

for i, row in df.iterrows():
    # Mengubah baris CSV menjadi narasi teks untuk dipahami LLM
    status_kualitas = "Defect/Bad" if row['Defect_Overall'] == 1 else "Normal/Good"
    teks_dokumen = (
        f"Material {row['Material_Description']} diproduksi dengan hasil kualitas {status_kualitas}. "
        f"Karakteristik: Masuk dalam {row['Cluster_Label']}, "
        f"Total Waste: {row['Total_Waste_Kg']} Kg, Rasio GK/GB: {row['Rasio_GK_GB']}."
    )
    documents.append(teks_dokumen)
    metadatas.append({"material": str(row['Material_Description']), "status": status_kualitas})
    ids.append(f"batch_histori_{i}")

# Memasukkan data ke dalam database
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("✅ Selesai! Database ChromaDB berhasil dibuat dan disimpan di folder ./chroma_db")