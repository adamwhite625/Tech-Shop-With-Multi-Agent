import pandas as pd
import math
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "tech_products"
# Multilingual model supports Vietnamese very well
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2" 

def ingest_products_to_qdrant():
    logger.info(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    logger.info("Connecting to Qdrant Database...")
    client = QdrantClient(url=QDRANT_URL)
    
    # 1. Recreate Collection if exists (Clean state)
    if client.collection_exists(collection_name=COLLECTION_NAME):
        client.delete_collection(collection_name=COLLECTION_NAME)
        
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=model.get_sentence_embedding_dimension(), # 384 for this model
            distance=Distance.COSINE
        )
    )
    
    # 2. Read Data from CSV
    logger.info("Reading products.csv...")
    try:
        df_products = pd.read_csv("../data/products.csv")
    except FileNotFoundError:
        logger.error("File products.csv not found in data folder!")
        return

    # Filter out inactive products if status column exists (Assuming status=1 is active)
    if 'status' in df_products.columns:
        df_products = df_products[df_products['status'] == 1]

    points = []
    
    logger.info(f"Processing and embedding {len(df_products)} products. This might take a moment...")
    
    # 3. Process each product
    for index, row in df_products.iterrows():
        try:
            product_id = int(row['product_id'])
            title = str(row['title']) if not pd.isna(row['title']) else ""
            summary = str(row['summary']) if not pd.isna(row['summary']) else ""
            price = float(row['price']) if not pd.isna(row['price']) else 0.0
            thumb = str(row['thumb']) if not pd.isna(row['thumb']) else ""
            slug = str(row['slug']) if not pd.isna(row['slug']) else ""
            
            # Create a rich text representation for semantic search
            text_to_embed = f"Tên sản phẩm: {title}. Cấu hình/Mô tả: {summary}"
            
            # Generate Vector
            vector = model.encode(text_to_embed).tolist()
            
            # Prepare Payload (Data returned when searched)
            payload = {
                "product_id": product_id,
                "title": title,
                "price": price,
                "thumb": thumb,
                "slug": slug,
                "summary": summary
            }
            
            # Create Qdrant Point
            point = PointStruct(
                id=product_id, # Qdrant supports integer IDs
                vector=vector,
                payload=payload
            )
            points.append(point)
            
        except Exception as e:
            logger.warning(f"Error processing row {index}: {e}")
            continue

    # 4. Upload to Qdrant in batches
    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        logger.info(f"Successfully ingested {len(points)} products into Qdrant collection '{COLLECTION_NAME}'.")
    else:
        logger.warning("No data points were created.")

if __name__ == "__main__":
    ingest_products_to_qdrant()