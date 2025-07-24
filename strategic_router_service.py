# strategic_router_service.py (Nihai, Kararlı Versiyon)

from fastapi import FastAPI
from pydantic import BaseModel, Field
import google.generativeai as genai
import json
from typing import List, Optional

# --- Ayarlar ---
GEMINI_API_KEY = "AIzaSyCM8sL2S13733x5F1fh7J-wOTc0X996dqc"

# --- Niyet ve Kategori Listeleri ---
INTENT_LIST = [
    "universite_bilgisi_isteme", "bolum_bilgisi_isteme", "kontenjan_bilgisi_isteme",
    "taban_puan_bilgisi_isteme", "burs_bilgisi_isteme", "yurt_bilgisi_isteme",
    "iletisim_bilgisi_isteme", "konum_bilgisi_isteme", "etkinlik_bilgisi_isteme",
    "universite_karsilastirma", "bolum_karsilastirma", "puan_kontenjan_karsilastirma",
    "tercih_tavsiyesi_isteme", "kariyer_rehberligi_isteme", "universite_hayati_sorulari",
    "tesekkur_etme", "selamlasma", "genel_sohbet", "anlasilmadi"
]

TASK_ORIENTED_INTENTS = [
    "universite_bilgisi_isteme", "bolum_bilgisi_isteme", "kontenjan_bilgisi_isteme",
    "taban_puan_bilgisi_isteme", "burs_bilgisi_isteme", "iletisim_bilgisi_isteme",
    "konum_bilgisi_isteme", "universite_karsilastirma", "bolum_karsilastirma",
    "puan_kontenjan_karsilastirma", "tercih_tavsiyesi_isteme"
]

# --- Pydantic Modelleri ---
class QueryRequest(BaseModel):
    user_query: str

class ExecutionPlan(BaseModel):
    detected_intent: str
    action_type: str
    optimized_queries: Optional[List[str]] = None

# --- Odaklanmış, Basit Prompt'lar ---

PROMPT_DETECT_INTENT_ONLY = """
Görevin, kullanıcının sorgusuna en uygun niyeti aşağıdaki listeden seçmek ve SADECE niyetin adını tek bir kelime olarak döndürmektir.
Niyet Listesi: {intent_list_str}
Eğer hiçbirine uymuyorsa "anlasilmadi" de. Başka hiçbir açıklama yapma, sadece niyetin adını yaz.
Kullanıcı Sorgusu: "{user_query}"
"""

PROMPT_CREATE_SEARCH_QUERIES_ONLY = """
Görevin, bir kullanıcının sorusunu en iyi cevaplayacak, etkili ve kısa 1 ila 3 adet Google arama sorgusu üretmektir.
Cevabını SADECE bir JSON listesi olarak ver. Örnek: ["sorgu 1", "sorgu 2"]
Kullanıcı Sorusu: "{user_query}"
"""

# --- Uygulama ---
app = FastAPI(title="Strategic Router Service (Stable Version)")
genai.configure(api_key=GEMINI_API_KEY)

async def call_gemini_async(prompt: str, is_json_output: bool = False):
    """Merkezi async Gemini çağrı fonksiyonu"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        config = {"response_mime_type": "application/json"} if is_json_output else {}
        response = await model.generate_content_async(prompt, generation_config=config)
        return response.text.strip()
    except Exception as e:
        print(f"!! Gemini Çağrı Hatası: {e}")
        return None

@app.post("/create_plan", response_model=ExecutionPlan)
async def create_execution_plan(request: QueryRequest):
    """Kullanıcı sorgusunu analiz eder ve kararlı bir eylem planı oluşturur."""
    
    # --- ADIM 1: NİYET TESPİTİ (Basit ve Odaklanmış Görev) ---
    intent_prompt = PROMPT_DETECT_INTENT_ONLY.format(
        user_query=request.user_query,
        intent_list_str=", ".join(INTENT_LIST)
    )
    detected_intent = await call_gemini_async(intent_prompt)
    if not detected_intent or detected_intent not in INTENT_LIST:
        detected_intent = "anlasilmadi" # Güvenlik ağı
    
    print(f"-> Adım 1 - Niyet Tespiti Sonucu: {detected_intent}")
    
    # --- ADIM 2: KARAR VERME (Deterministik Python Kodu) ---
    action_type = "RAG_SEARCH" if detected_intent in TASK_ORIENTED_INTENTS else "DIRECT_CHAT"
    print(f"-> Adım 2 - Eylem Kararı: {action_type}")

    # --- ADIM 3: SORGU ÜRETİMİ (Koşullu ve Odaklanmış Görev) ---
    optimized_queries = None
    if action_type == "RAG_SEARCH":
        queries_prompt = PROMPT_CREATE_SEARCH_QUERIES_ONLY.format(user_query=request.user_query)
        queries_response_str = await call_gemini_async(queries_prompt, is_json_output=True)
        if queries_response_str:
            try:
                optimized_queries = json.loads(queries_response_str)
            except json.JSONDecodeError:
                print(f"!! Sorgu üretimi JSON parse hatası. Ham yanıt: {queries_response_str}")
                optimized_queries = [request.user_query] # Fallback
        else:
            optimized_queries = [request.user_query] # Fallback
        print(f"-> Adım 3 - Optimize Edilmiş Sorgular: {optimized_queries}")

    return ExecutionPlan(
        detected_intent=detected_intent,
        action_type=action_type,
        optimized_queries=optimized_queries
    )