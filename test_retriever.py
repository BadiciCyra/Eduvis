import requests
import time
import json

API_URL = "http://127.0.0.1:8000/retrieve"
PAYLOAD = {
    "queries": [
        "Yapay zeka etiği nedir?",
        "Türkiye'deki en iyi bilgisayar mühendisliği üniversiteleri"
    ]
}

def run_test():
    print("-" * 20)
    print("İstek gönderiliyor...")
    start_time = time.time()
    try:
        response = requests.post(API_URL, json=PAYLOAD, timeout=60)
        end_time = time.time()
        print(f"Cevap {end_time - start_time:.2f} saniyede alındı.")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nDurum: {data.get('status')}")
            for doc in data.get('data', []):
                print(f"  - URL: {doc['url']}")
        else:
            print(f"Hata Kodu: {response.status_code}, Cevap: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Servise bağlanılamadı: {e}")

if __name__ == "__main__":
    print("### İLK ÇALIŞTIRMA (CACHE DOLDURULUYOR) ###")
    run_test()
    print("\n### İKİNCİ ÇALIŞTIRMA (CACHE'DEN OKUNUYOR) ###")
    run_test()