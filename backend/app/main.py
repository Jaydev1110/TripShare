"""
TripShare FastAPI Backend - Main Application Entry Point
"""
from fastapi import FastAPI
from app.routes import ping, auth, groups, photos

from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI application
app = FastAPI(
    title="TripShare",
    description="Backend API for TripShare application",
    version="1.0.0"
)

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "null"  # For local file access if opening html directly
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ping.router)
app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(photos.router)


@app.get("/")
async def root():
    """
    Root endpoint.
    Returns basic project information.
    """
    return {
        "project": "TripShare",
        "status": "active"
    }

