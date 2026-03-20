from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from PIL import Image
import io

load_dotenv()

from app.core.logging_config import setup_logging

# Configure Logging
logger = setup_logging(__name__)

# Constants — read from env
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLLECTION_TEXT = "tech_products"
COLLECTION_IMAGE = "tech_products_images"
MODEL_TEXT_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
MODEL_CLIP_NAME = "clip-ViT-B-32"


# ---------------------------------------------------------
# App State — thay thế global mutable variables
# ---------------------------------------------------------
@dataclass
class AppState:
    """Encapsulates all runtime state. Avoids global mutable variables."""
    text_model: Optional[SentenceTransformer] = None
    clip_model: Optional[SentenceTransformer] = None
    qdrant_client: Optional[QdrantClient] = None
    is_ready: bool = False

app_state = AppState()


# ---------------------------------------------------------
# Lifespan — thay thế @app.on_event("startup") đã deprecated
# ---------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan handler (replaces deprecated on_event)."""
    # === STARTUP ===
    try:
        logger.info("Loading Text Model...")
        app_state.text_model = SentenceTransformer(MODEL_TEXT_NAME)

        logger.info("Loading CLIP Image Model... (This takes a moment)")
        app_state.clip_model = SentenceTransformer(MODEL_CLIP_NAME)

        logger.info("Connecting to Qdrant...")
        app_state.qdrant_client = QdrantClient(url=QDRANT_URL)

        app_state.is_ready = True
        logger.info("Search Agent is READY with Hybrid & Image Search!")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        # is_ready remains False — requests will get proper error messages

    yield  # App runs here

    # === SHUTDOWN ===
    logger.info("Search Agent shutting down...")
    if app_state.qdrant_client:
        app_state.qdrant_client.close()


app = FastAPI(
    title="TechStore Search Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------
class SearchRequest(BaseModel):
    query: str
    limit: int = 5


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------
@app.get("/health")
async def health_check():
    return {
        "status": "online" if app_state.is_ready else "initializing",
        "service": "Search Agent",
        "models_loaded": app_state.is_ready,
    }


@app.post("/api/search")
async def perform_text_search(request: SearchRequest):
    """Text Semantic Search"""
    if not app_state.text_model or not app_state.qdrant_client:
        raise HTTPException(
            status_code=503,
            detail="Search Agent chưa sẵn sàng. Models đang được tải, vui lòng thử lại sau."
        )

    query_vector = app_state.text_model.encode(request.query).tolist()
    search_result = app_state.qdrant_client.search(
        collection_name=COLLECTION_TEXT,
        query_vector=query_vector,
        limit=request.limit,
        score_threshold=0.3
    )

    results = [
        {
            "product_id": hit.payload.get("product_id"),
            "title": hit.payload.get("title"),
            "price": hit.payload.get("price"),
            "slug": hit.payload.get("slug"),
            "thumb": hit.payload.get("thumb"),
            "match_score": round(hit.score, 4),
        }
        for hit in search_result
    ]
    return {"query": request.query, "total_found": len(results), "results": results}


@app.post("/api/search/image")
async def perform_image_search(file: UploadFile = File(...), limit: int = 5):
    """Image Search using CLIP"""
    if not app_state.clip_model or not app_state.qdrant_client:
        raise HTTPException(
            status_code=503,
            detail="Search Agent chưa sẵn sàng. Models đang được tải, vui lòng thử lại sau."
        )

    try:
        # 1. Read uploaded image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # 2. Embed Image to Vector (512 dimensions for CLIP)
        image_vector = app_state.clip_model.encode(image).tolist()

        # 3. Search in Image Collection
        try:
            search_result = app_state.qdrant_client.search(
                collection_name=COLLECTION_IMAGE,
                query_vector=image_vector,
                limit=limit
            )
            results = [
                {
                    "product_id": hit.payload.get("product_id"),
                    "title": hit.payload.get("title"),
                    "thumb": hit.payload.get("thumb"),
                    "match_score": round(hit.score, 4),
                }
                for hit in search_result
            ]
        except Exception:
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