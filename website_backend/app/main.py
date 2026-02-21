from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import các router
from app.routers import auth, category, product, cart, checkout

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

# Nhúng các Router vào hệ thống
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

app.include_router(category.router, prefix="/api/categories", tags=["Categories"])
app.include_router(product.router, prefix="/api/products", tags=["Products"])
app.include_router(cart.router, prefix="/api/cart", tags=["Cart"])
app.include_router(checkout.router, prefix="/api/checkout", tags=["Checkout"])