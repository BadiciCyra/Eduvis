import asyncio
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from googleapiclient.discovery import build
from trafilatura import fetch_url, extract
from typing import List
from contextlib import asynccontextmanager

# Ayarlar
GOOGLE_API_KEY = "AIzaSyCM8sL2S13733x5F1fh7J-wOTc0X996dqc"
SEARCH_ENGINE_ID = "7591159fd88734d3d"
REDIS_URL = "redis://localhost:6379"

redis_client = None

# Lifespan sistemi (startup/shutdown işlemleri)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        await redis_client.ping()
        print("✅ Redis cache bağlantısı kuruldu.")
    except Exception as e:
        print(f"❌ Redis cache bağlantısı kurulamadı: {e}")
        redis_client = None
    yield
    if redis_client:
        await redis_client.close()
        print("🔌 Redis bağlantısı kapatıldı.")

# FastAPI app tanımı (en başta olmalı)
app = FastAPI(
    title="Retrieve Service",
    description="Arama ve veri çekme servisi",
    lifespan=lifespan
)

# Request modeli
class RetrieveRequests(BaseModel):
    queries: List[str]

# Google'dan asenkron arama
async def search_google_async(query: str) -> list:
    loop = asyncio.get_event_loop()
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)

    def do_search():
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=3)
        return [item['link'] for item in res.execute().get('items', [])]

    try:
        urls = await loop.run_in_executor(None, do_search)
        print(f"🔎 Google arama sonuçları: {urls}")
        return urls
    except Exception as e:
        print(f"❌ Google arama hatası: {e}")
        return []

# İçerik çekme ve önbellekleme
async def fetch_and_extract(url: str) -> dict:
    if not redis_client:
        return None

    cached_content = await redis_client.get(url)
    if cached_content:
        print(f"✅ [CACHE_HIT] {url}")
        return {"url": url, "content": cached_content}

    print(f"📥 [CACHE_MISS] {url} webden çekiliyor...")

    loop = asyncio.get_event_loop()
    try:
        content = await loop.run_in_executor(None, lambda: extract(fetch_url(url)))
        if content:
            await redis_client.set(url, content, ex=86400)
            print(f"✅ [İçerik OK] {url}")
            return {"url": url, "content": content}
        return None
    except Exception as e:
        print(f"❌ [İçerik Hatası] {url} - {e}")
        return None

# API route
@app.post("/retrieve")
async def retrieve(request: RetrieveRequests):
    if not request.queries:
        raise HTTPException(status_code=400, detail="Sorgu listesi boş olamaz.")

    search_tasks = [search_google_async(query) for query in request.queries]
    list_of_urls = await asyncio.gather(*search_tasks)

    unique_urls = set(url for urls in list_of_urls for url in urls if urls)
    if not unique_urls:
        raise HTTPException(status_code=404, detail="Hiçbir sonuç bulunamadı.")

    extract_tasks = [fetch_and_extract(url) for url in unique_urls]
    results = await asyncio.gather(*extract_tasks)

    successful_results = [result for result in results if result]
    if not successful_results:
        raise HTTPException(status_code=404, detail="Hiçbir içerik bulunamadı.")

    return {
        "status": f"{len(successful_results)/len(unique_urls) * 100:.2f}% başarıyla çekildi.",
        "data": successful_results
    }
