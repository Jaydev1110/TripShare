"""
TripShare FastAPI Backend - Main Application Entry Point
"""
from fastapi import FastAPI
from app.routes import ping, auth

# Initialize FastAPI application
app = FastAPI(
    title="TripShare",
    description="Backend API for TripShare application",
    version="1.0.0"
)

# Include routers
app.include_router(ping.router)
app.include_router(auth.router)


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

