# reranker_service_v2.py

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers.cross_encoder import CrossEncoder
from typing import List

# --- Pydantic Modelleri (API'nin kural seti - Değişmedi) ---
class Document(BaseModel):
    url: str
    content: str

class RerankRequest(BaseModel):
    original_query: str
    documents: List[Document]

# --- Uygulama ---
app = FastAPI(
    title="Advanced Re-Ranking Service (Cross-Encoder)",
    description="Cross-Encoder modeli ile alaka düzeyine göre yeniden sıralama yapar."
)
# Cross-Encoder modelini global olarak tanımlıyoruz
cross_encoder_model = None

@app.on_event("startup")
def load_model():
    """Servis başladığında Cross-Encoder modelini bir kereliğine belleğe yükler."""
    global cross_encoder_model
    # Bu model, özellikle arama sonuçlarını yeniden sıralamak için eğitilmiştir.
    # Çoklu dil desteği de vardır.
    model_name = 'cross-encoder/ms-marco-MiniLM-L-12-v2'
    print(f"Cross-Encoder modeli yükleniyor: {model_name}...")
    # Cihazı otomatik olarak seç (GPU varsa GPU, yoksa CPU)
    cross_encoder_model = CrossEncoder(model_name, max_length=512)
    print("Cross-Encoder modeli başarıyla yüklendi.")

@app.post("/rerank")
async def rerank_documents(request: RerankRequest):
    """Dökümanları, Cross-Encoder ile hesaplanan alaka düzeyi skorlarına göre yeniden sıralar."""
    if not request.documents or not cross_encoder_model:
        return {"ranked_documents": []}
        
    # Modelin beklediği format: [(sorgu, döküman_içeriği), (sorgu, döküman_içeriği_2), ...]
    query_doc_pairs = [(request.original_query, doc.content) for doc in request.documents]

    # Tüm çiftler için skorları tek seferde hesapla
    print(f"{len(query_doc_pairs)} adet döküman-sorgu çifti için alaka skoru hesaplanıyor...")
    scores = cross_encoder_model.predict(query_doc_pairs)
    print("Skorlar hesaplandı.")

    # Her dökümana kendi skorunu ekle
    doc_scores = []
    for i, doc in enumerate(request.documents):
        doc_scores.append({
            "score": scores[i].item(), # Skoru al
            "document": doc.dict()
        })

    # Skorlara göre büyükten küçüpe doğru sırala
    ranked_docs = sorted(doc_scores, key=lambda x: x['score'], reverse=True)
    
    return {"ranked_documents": ranked_docs}
