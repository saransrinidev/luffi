from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from services.llm_service import LLMService
from services.prompt_service import PromptService
from services.history_service import HistoryService

logger = logging.getLogger(__name__)
router = APIRouter()

llm_service = LLMService()
prompt_service = PromptService()
history_service = HistoryService()


class ExplainRequest(BaseModel):
    text: str
    model: str | None = None
    mode: str = "explain"


class ExplainResponse(BaseModel):
    explanation: str
    model_used: str
    mode: str
    from_cache: bool = False
    latency_ms: float = 0
    tokens_generated: int = 0
    tokens_per_sec: float = 0


@router.get("/health")
async def health():
    return {"status": "ok", "service": "nap-backend"}


@router.get("/modes")
async def get_modes():
    return prompt_service.get_modes()


@router.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    logger.info(f"[{request.mode}] Request: {request.text[:50]}...")

    try:
        result = await llm_service.explain(request.text, request.model, request.mode)
        # Save to history
        history_service.save(
            mode=result["mode"],
            input_text=request.text,
            response=result["explanation"],
            model=result["model_used"],
        )
        return result
    except Exception as e:
        logger.error(f"LLM service error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(limit: int = 20):
    return history_service.get_recent(limit)


@router.get("/history/search")
async def search_history(q: str, limit: int = 10):
    return history_service.search(q, limit)


@router.delete("/history")
async def clear_history():
    history_service.clear()
    return {"status": "cleared"}


@router.get("/cache/stats")
async def cache_stats():
    return llm_service.cache.stats


@router.delete("/cache")
async def clear_cache():
    llm_service.cache.clear()
    return {"status": "cache cleared"}
