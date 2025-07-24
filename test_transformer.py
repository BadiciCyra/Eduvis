# test_transformer.py
import requests

API_URL = "http://127.0.0.1:8001/create_plan"
# Test 1: Arama gerektiren sorgu
payload1 = {"user_query": "Kanka 400.000 sıralamada hangi üniversiteler var?"}
# Test 2: Arama gerektirmeyen sorgu
payload2 = {"user_query": "YKS'ye çalışırken nasıl motive olabilirim?"}

print("--- TEST 1 (Arama Gerekli) ---")
response1 = requests.post(API_URL, json=payload1)
print(response1.json())

print("\n--- TEST 2 (Arama Gerekli Değil) ---")
response2 = requests.post(API_URL, json=payload2)
print(response2.json())