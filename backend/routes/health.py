from fastapi import APIRouter
import logging

logger = logging.getLogger("API_Gateway")
router = APIRouter()

@router.get("/health")
def health_check():
    logger.debug("Health check ping received.")
    return {"status": "alive"}
