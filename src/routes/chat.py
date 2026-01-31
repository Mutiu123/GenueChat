"""Chat and document Q&A endpoints."""

import logging
import time
import tempfile
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.config import get_settings
from src.exceptions import DocumentProcessingError, LLMError
from src.monitoring import (
    DOCUMENT_UPLOADS,
    METRICS_AVAILABLE,
    log_prediction_audit,
)
from src.schemas import ChatRequest, ChatResponse, DocumentChatResponse
from src.security import check_rate_limit, get_current_user, sanitize_input
from src.llm import handle_chat_async, rag_chain_async

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Send a chat message",
    dependencies=[Depends(check_rate_limit)],
)
async def chat(
    body: ChatRequest,
    user: dict = Depends(get_current_user),
) -> ChatResponse:
    """Process a general chat message through the LLM."""
    request_id: Optional[str] = None
    question = sanitize_input(body.question)
    start = time.perf_counter()
    try:
        answer = await handle_chat_async(question)
    except Exception as exc:
        logger.exception("LLM error: %s", exc)
        raise LLMError("Failed to generate response") from exc
    elapsed_ms = (time.perf_counter() - start) * 1000

    log_prediction_audit(
        request_id=request_id,
        question=question,
        answer=answer,
        model=settings.LLM_MODEL_NAME,
        processing_time_ms=elapsed_ms,
        source="chat",
    )
    return ChatResponse(
        answer=answer,
        session_id=body.session_id,
        model=settings.LLM_MODEL_NAME,
        processing_time_ms=round(elapsed_ms, 2),
    )


@router.post(
    "/document",
    response_model=DocumentChatResponse,
    summary="Ask a question about an uploaded PDF",
    dependencies=[Depends(check_rate_limit)],
)
async def document_chat(
    file: UploadFile = File(...),
    question: str = Form(...),
    session_id: Optional[str] = Form(None),
    user: dict = Depends(get_current_user),
) -> DocumentChatResponse:
    """Upload a PDF and ask a question about its contents."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise DocumentProcessingError("Only PDF files are supported")

    if METRICS_AVAILABLE:
        DOCUMENT_UPLOADS.inc()

    question = sanitize_input(question)
    start = time.perf_counter()

    # Write upload to a temporary file for PyPDFLoader
    tmp_path = ""
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        answer = await rag_chain_async(tmp_path, question)
    except DocumentProcessingError:
        raise
    except Exception as exc:
        logger.exception("Document processing error: %s", exc)
        raise DocumentProcessingError(
            "Failed to process document"
        ) from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    elapsed_ms = (time.perf_counter() - start) * 1000
    log_prediction_audit(
        question=question,
        answer=answer,
        model=settings.LLM_MODEL_NAME,
        processing_time_ms=elapsed_ms,
        source="document",
    )
    return DocumentChatResponse(
        answer=answer,
        session_id=session_id,
        processing_time_ms=round(elapsed_ms, 2),
    )
