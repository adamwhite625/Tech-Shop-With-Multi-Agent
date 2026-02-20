import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QDRANT_URL = "http://localhost:6333"
COLLECTION_IMAGE = "tech_products_images"
MODEL_CLIP_NAME = "clip-ViT-B-32"
IMAGE_FOLDER = "../data/images"

def ingest_images():
    logger.info("Loading CLIP model...")
    model = SentenceTransformer(MODEL_CLIP_NAME)
    client = QdrantClient(url=QDRANT_URL)
    
    # Recreate Collection for Images
    if client.collection_exists(collection_name=COLLECTION_IMAGE):
        client.delete_collection(collection_name=COLLECTION_IMAGE)
        
    client.create_collection(
        collection_name=COLLECTION_IMAGE,
        vectors_config=VectorParams(size=512, distance=Distance.COSINE) # CLIP produces 512-dim vectors
    )
    
    logger.info("Reading products.csv...")
    try:
        df_products = pd.read_csv("../data/products.csv")
    except FileNotFoundError:
        logger.error("File products.csv not found!")
        return

    points = []
    logger.info("Processing images. Missing files will be skipped...")
    
    for index, row in df_products.iterrows():
        try:
            product_id = int(row['product_id'])
            thumb_path = str(row['thumb'])
            # Lấy tên file từ đường dẫn (VD: /d/o/dong-ho-abc.png -> dong-ho-abc.png)
            filename = os.path.basename(thumb_path)
            full_img_path = os.path.join(IMAGE_FOLDER, filename)
            
            if os.path.exists(full_img_path):
                image = Image.open(full_img_path).convert("RGB")
                vector = model.encode(image).tolist()
                
                payload = {
                    "product_id": product_id,
                    "title": str(row['title']),
                    "thumb": thumb_path,
                    "price": float(row['price']) if not pd.isna(row['price']) else 0.0,
                }
                points.append(PointStruct(id=product_id, vector=vector, payload=payload))
        except Exception as e:
            continue

    if points:
        client.upsert(collection_name=COLLECTION_IMAGE, points=points)
        logger.info(f"Successfully ingested {len(points)} images into Qdrant!")
    else:
        logger.warning("No images found or ingested.")

if __name__ == "__main__":
    ingest_images()