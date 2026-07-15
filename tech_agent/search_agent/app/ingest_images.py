import os
import io
import time
import requests
import pandas as pd
from PIL import Image
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# Configuration
CSV_PATH = "../data/products_valid.csv"
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "tech_products_images"


BASE_IMAGE_URL = "https://cdn2.cellphones.com.vn/insecure/rs:fill:300:300/q:90/plain/https://cellphones.com.vn/media/catalog/product" 

def main():
    # Process product images, generate CLIP embeddings, and ingest them into Qdrant.
    print("1. Đang khởi tạo Qdrant Client và load model CLIP (có thể mất chút thời gian)...")
    qdrant = QdrantClient(url=QDRANT_URL)
    clip_model = SentenceTransformer('clip-ViT-B-32')

    # Tạo collection nếu chưa có
    try:
        qdrant.get_collection(COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' đã tồn tại.")
    except Exception:
        print(f"Tạo mới collection '{COLLECTION_NAME}'...")
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=512, distance=models.Distance.COSINE),
        )

    print(f"2. Đang đọc dữ liệu từ {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    # Giới hạn số lượng nạp thử nghiệm (thay đổi tuỳ ý)
    # df = df.head(100) 

    points = []
    success_count = 0
    fail_count = 0

    print("3. Bắt đầu xử lý và nạp vector ảnh vào Qdrant...")
    for index, row in df.iterrows():
        try:
            product_id = str(row['product_id'])
            title = str(row['title'])
            thumb_path = str(row.get('thumb', ''))
            
            if not thumb_path or thumb_path == 'nan':
                fail_count += 1
                continue

            # Thay đổi logic này nếu bạn lưu ảnh ở local folder
            image_url = BASE_IMAGE_URL + thumb_path

            # Tải ảnh về
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                print(f"Lỗi tải ảnh {image_url}")
                fail_count += 1
                continue
                
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
            
            # Chạy qua model CLIP để biến ảnh thành dãy số (vector 512 chiều)
            vector = clip_model.encode(image).tolist()
            
            # Gom dữ liệu để đẩy lên Qdrant
            points.append(
                models.PointStruct(
                    id=index, # Dùng index của dòng làm ID trong Qdrant
                    vector=vector,
                    payload={
                        "product_id": product_id,
                        "title": title,
                        "thumb": thumb_path
                    }
                )
            )
            success_count += 1
            
            # Cứ mỗi 50 ảnh thì lưu vào Qdrant 1 lần cho lẹ
            if len(points) >= 50:
                qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
                points = []
                print(f"  Đã nạp {success_count} ảnh...")
                
            # Tránh bị server block vì spam request tải ảnh
            time.sleep(0.1) 
            
        except Exception as e:
            print(f"Lỗi xử lý dòng {index}: {e}")
            fail_count += 1

    # Nạp nốt những ảnh còn dư chưa đủ 50 cái
    if points:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

    print("====================================")
    print("HOÀN TẤT NẠP DỮ LIỆU ẢNH TRUY VẤN!")
    print(f"- Thành công: {success_count} ảnh")
    print(f"- Thất bại (Lỗi hoặc không có link): {fail_count} ảnh")
    print("====================================")

if __name__ == "__main__":
    main()
