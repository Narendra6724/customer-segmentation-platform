"""
FastAPI Application — Customer Segmentation Platform Backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.db import engine, Base
from backend.routes.predict import router as predict_router
from backend.routes.auth import router as auth_router
from backend.services.user_service import seed_initial_users

# ---------------------------------------------------------------------------
# Create tables on import (idempotent)
# ---------------------------------------------------------------------------
# Import all models so Base.metadata knows about them
from backend.models import customer, user  # noqa: F401

Base.metadata.create_all(bind=engine)

# Seed default users
seed_initial_users()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Customer Segmentation API",
    description="K-Means powered customer segmentation with business insights.",
    version="2.0.0",
)

# CORS — allow Streamlit and any local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(predict_router)
app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
