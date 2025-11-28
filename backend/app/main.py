from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, messages, websocket, pq, documents
from app.middleware import setup_rate_limiting
from app.pq_transport import generate_server_keypair

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
app.include_router(websocket.router)
app.include_router(pq.router)  # Post-quantum transport security
app.include_router(documents.router)  # Document serving


@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    
    # Generate server's post-quantum Kyber keypair on startup
    # This keypair is used for establishing secure session keys with clients
    try:
        public_key, secret_key = generate_server_keypair()
        print(f"[STARTUP] Post-quantum server keypair generated successfully")
        print(f"[STARTUP] Public key size: {len(public_key)} bytes")
    except Exception as e:
        print(f"[STARTUP] WARNING: Failed to generate PQ keypair: {e}")
        print(f"[STARTUP] PQ transport security will not work properly!")

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

@app.get("/")
async def root():
    return {"message": "Messaging App API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
