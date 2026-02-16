from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth

app = FastAPI(title="PinkCapy Tech E-commerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Website Backend Core is running!"}

# Nhúng Auth Router vào hệ thống
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])