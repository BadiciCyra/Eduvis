from fastapi import FastAPI
from pydantic import BaseModel
from sentence-transfomers.cross_encoder import CrossEncoder
from typing import List

class Document(BaseModel):
    url: str
    content: str


class ReRankRequest(BaseModel):
    original_query: str
    document: List[Document]



app = FastAPI(
    title = "Advance Re-Ranking service (Cross Encoding)",
    description = "Cross Encoder ile alaka oranına göre sıralama yapar"
)    
cross_encoder_model = None

@app.on_event("startup")
def load_model():
    global cross_encoder_model
    model_name = "cross-encoder/ms-Marco-MiniLM-L-12-v2"
    print(f"Cross-Encoder modeli yükleniyor... {model_name}")
    cross_encoder_model  = CrossEncoder(model_name, max_length = 512)
    print("Cross-Encoder modeli başarıyla yüklendi")


@app.post("/rerank")
async def rerank_documents(request: ReRankRequest)    
