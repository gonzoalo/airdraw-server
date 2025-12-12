from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.core.operators import load_operators
from app.api.routes import operators, files, health

# Setup logging
logging.basicConfig(level=settings.log_level)

app = FastAPI(title=settings.app_name, debug=settings.debug)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(operators.router)
app.include_router(files.router)
app.include_router(health.router)

@app.on_event("startup")
async def startup_event():
    """Load operators at startup"""
    ops, errs = load_operators()
    logging.getLogger(__name__).info(f"Loaded {len(ops)} operator modules")