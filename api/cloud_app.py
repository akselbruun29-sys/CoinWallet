"""Minimal cloud deployment — leaderboard + future AI only (no wallet routes)."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.leaderboard import router as leaderboard_router
from api.middleware import SecurityHeadersMiddleware
from api.remote_leaderboard import router as remote_leaderboard_router

load_dotenv()

# Cloud services must not expose wallet data; this app only mounts public leaderboard routes.
os.environ.setdefault("LEADERBOARD_CLOUD_MODE", "true")

_DEFAULT_CORS = [
    "https://coinwallet.pages.dev",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

_cors_raw = os.getenv("CORS_ORIGINS", "").strip()
_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()] if _cors_raw else _DEFAULT_CORS

app = FastAPI(title="CoinWallet Cloud Services", version="0.1.0")
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(leaderboard_router)
app.include_router(remote_leaderboard_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "coinwallet-cloud"}
