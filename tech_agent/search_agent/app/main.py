from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from PIL import Image
import io

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TechStore Search Agent", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
QDRANT_URL = "http://localhost:6333"
COLLECTION_TEXT = "tech_products"
COLLECTION_IMAGE = "tech_products_images" # Collection mới dành riêng cho ảnh
MODEL_TEXT_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_CLIP_NAME = "clip-ViT-B-32" # Model CLIP của OpenAI

# Global Variables
text_model = None
clip_model = None
qdrant_client = None

@app.on_event("startup")
async def startup_event():
    global text_model, clip_model, qdrant_client
    try:
        logger.info("Loading Text Model...")
        text_model = SentenceTransformer(MODEL_TEXT_NAME)
        
        logger.info("Loading CLIP Image Model... (This takes a moment)")
        clip_model = SentenceTransformer(MODEL_CLIP_NAME)
        
        logger.info("Connecting to Qdrant...")
        qdrant_client = QdrantClient(url=QDRANT_URL)
        logger.info("Search Agent is READY with Hybrid & Image Search!")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

@app.post("/api/search")
async def perform_text_search(request: SearchRequest):
    """Text Semantic Search"""
    query_vector = text_model.encode(request.query).tolist()
    search_result = qdrant_client.search(
        collection_name=COLLECTION_TEXT,
        query_vector=query_vector,
        limit=request.limit,
        score_threshold=0.3
    )
    
    results = [{"product_id": hit.payload.get("product_id"), "title": hit.payload.get("title"), "price": hit.payload.get("price"), "slug": hit.payload.get("slug"), "thumb": hit.payload.get("thumb"), "match_score": round(hit.score, 4)} for hit in search_result]
    return {"query": request.query, "total_found": len(results), "results": results}

@app.post("/api/search/image")
async def perform_image_search(file: UploadFile = File(...), limit: int = 5):
    """Image Search using CLIP"""
    if not clip_model or not qdrant_client:
        raise HTTPException(status_code=500, detail="Models not loaded")

    try:
        # 1. Read uploaded image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # 2. Embed Image to Vector (512 dimensions for CLIP)
        image_vector = clip_model.encode(image).tolist()
        
        # 3. Search in Image Collection (Assuming you will ingest images later)
        # Note: We wrap in try-except because the collection might not exist yet
        try:
            search_result = qdrant_client.search(
                collection_name=COLLECTION_IMAGE,
                query_vector=image_vector,
                limit=limit
            )
            results = [{"product_id": hit.payload.get("product_id"), "title": hit.payload.get("title"), "thumb": hit.payload.get("thumb"), "match_score": round(hit.score, 4)} for hit in search_result]
        except Exception as e:
            logger.warning("Image collection might not be initialized yet.")
            results = []

        return {
            "query_type": "image",
            "filename": file.filename,
            "total_found": len(results),
            "results": results,
            "message": "Cần chạy script ingest_images.py để nạp data ảnh thật vào Qdrant" if not results else "Success"
        }
    except Exception as e:
        logger.error(f"Image search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))