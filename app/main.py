import os
import logging
from collections import defaultdict
from time import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.health import router as health_router
from api.ai import router as ai_router
from routers.config_admin import router as config_router
from routers import admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI(
    title="EnterPrise Ai",
    version="1.0.0"
)

# ── CORS ──────────────────────────────────────────────────────
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Security headers ──────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ── Rate limiting (60 requests / 60 seconds per IP) ───────────
_rate_limit_requests: dict = defaultdict(list)
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time()
    window = 60
    _rate_limit_requests[client_ip] = [
        t for t in _rate_limit_requests[client_ip] if now - t < window
    ]
    if len(_rate_limit_requests[client_ip]) >= RATE_LIMIT:
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    _rate_limit_requests[client_ip].append(now)
    return await call_next(request)

# ── Routers ───────────────────────────────────────────────────
app.include_router(admin.router)
app.include_router(health_router)
app.include_router(ai_router)
app.include_router(config_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)

