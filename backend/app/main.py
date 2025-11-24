from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, messages
from app.middleware import setup_rate_limiting

app = FastAPI(
    title="Messaging App API",
    description="A simple messaging app with encrypted messages",
    version="1.0.0"
)

# Setup rate limiting
limiter = setup_rate_limiting(app)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://localhost:5178",
    "http://localhost:5179",
    "http://localhost:5180",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
    "http://127.0.0.1:5177",
    "http://127.0.0.1:5178",
    "http://127.0.0.1:5179",
    "http://127.0.0.1:5180",
]

# CORS middleware (keep this ABOVE routers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # or ["*"] for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ⛔️ DELETE this whole block from your code:
# @app.options("/{full_path:path}")
# async def options_handler(...):
#     ...

# Routers
app.include_router(auth.router)
app.include_router(messages.router)


@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Messaging App API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
