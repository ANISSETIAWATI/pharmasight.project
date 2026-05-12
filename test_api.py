import requests

url = "http://127.0.0.1:8000/predict"
# Contoh data (pastikan key sesuai dengan isi feature_cols.txt)
data = {
    "GB_Yield_Total": 425.72,
    "GK_Yield_Total": 908.38,
    "Rasio_GK_GB": 2.13,
    "GB_Kadar_Air_Mean": 5.42,
    "Cetak_Yield_Kg": 712.0,
    "Cetak_Pct_Teoritis": 2.82,
    "Kemas_Pct_Teoritis": 2.78,
    "Total_Waste_Kg": 0.0,
    "Cetak_Durasi_Hari": 0.0,
    "Kemas_Durasi_Hari": 0.0,
    "Bulan_Produksi": 6.0
}

response = requests.post(url, json=data)
print(response.json())