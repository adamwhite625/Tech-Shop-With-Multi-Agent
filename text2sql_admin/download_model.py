from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="adamwhite625/gemma-2-2b-text2sql-12k-gguf",
    local_dir="model-12k",
    allow_patterns=["*.gguf"]
)

print("Download done!")