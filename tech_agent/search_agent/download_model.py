import os
from huggingface_hub import snapshot_download

# Tăng mạnh thời gian chờ mạng timeout từ 10s lên 300s
os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "300"

print("Downloading Text Model (paraphrase-multilingual-MiniLM-L12-v2)...", flush=True)
snapshot_download("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

print("Downloading Image Model (clip-ViT-B-32)...", flush=True)
snapshot_download("sentence-transformers/clip-ViT-B-32")

print("All models downloaded successfully!", flush=True)
