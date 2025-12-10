"""
Test endpoint to verify backend is running.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def ping():
    """
    Health check endpoint.
    Returns a simple status message to verify the backend is running.
    """
    return {
        "status": "ok",
        "message": "TripShare backend running"
    }

