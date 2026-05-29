from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from services.llm_service import LLMService

logger = logging.getLogger(__name__)
router = APIRouter()

llm_service = LLMService()


class ExplainRequest(BaseModel):
    text: str
    model: str | None = None


class ExplainResponse(BaseModel):
    explanation: str
    model_used: str


@router.get("/health")
async def health():
    return {"status": "ok", "service": "nap-backend"}


@router.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    logger.info(f"Explain request received: {request.text[:50]}...")

    try:
        result = await llm_service.explain(request.text, request.model)
        return result
    except Exception as e:
        logger.error(f"LLM service error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
