"""
FastAPI REST Server Entry Point.
Monday.com AI Business Intelligence Agent API.

Provides API endpoints for health monitoring, Monday workspace boards,
cleaned datasets, BI pipeline & revenue summaries, and an interactive AI chat interface.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.bi_agent import BIAgent, ask
from services import business_intelligence_service as bi_service
from services import data_cleaning_service as cleaning_service
from services import monday_service
from utils.logger import get_logger

# Initialize logger for FastAPI server
logger = get_logger("main_api")

# Create FastAPI application instance with OpenAPI metadata
app = FastAPI(
    title="Monday.com AI Business Intelligence Agent API",
    description="Backend API service exposing Monday.com GraphQL integrations, data cleaning pipelines, business metrics analytics, and AI agent chat.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Schemas for Request and Response payloads
class ChatRequest(BaseModel):
    question: str = Field(..., description="Natural language business query", example="What is our total pipeline value?")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Plain text response from AI BI Agent")


@app.get("/", tags=["General"])
async def root() -> Dict[str, str]:
    """
    Root endpoint returning server greeting message.
    """
    logger.info("GET / endpoint called.")
    return {"message": "Monday BI Agent API Running"}


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint reporting API status, Monday API connection status, and Groq initialization state.
    """
    logger.info("GET /health endpoint called.")
    
    # Check Monday.com API connection
    try:
        monday_res = monday_service.test_connection()
        monday_status = "connected" if monday_res.get("success") else "failed"
    except Exception as e:
        logger.error(f"Monday connection check failed: {str(e)}")
        monday_status = f"failed ({str(e)})"

    # Check Groq Agent status
    try:
        agent_instance = BIAgent()
        groq_status = "Initialized" if agent_instance.agent is not None else "Not Initialized"
    except Exception as e:
        logger.error(f"Groq status check failed: {str(e)}")
        groq_status = "Not Initialized"

    return {
        "status": "healthy",
        "monday_connection": monday_status,
        "groq_status": groq_status,
        "openai_status": groq_status,  # Retained for backwards compatibility
        "gemini_status": groq_status,  # Retained for backwards compatibility
    }



@app.get("/boards", tags=["Monday Data"])
async def get_boards() -> Dict[str, Any]:
    """
    Retrieves all available Monday.com workspace boards.
    """
    logger.info("GET /boards endpoint called.")
    try:
        res = monday_service.get_boards()
        if not res.get("success"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=res.get("error", "Failed to retrieve Monday boards."),
            )
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET /boards: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/pipeline-summary", tags=["Analytics"])
async def get_pipeline_summary() -> Dict[str, Any]:
    """
    Returns sales pipeline summary metrics (total deals, total value, average deal value).
    """
    logger.info("GET /pipeline-summary endpoint called.")
    try:
        res = bi_service.get_pipeline_summary()
        if not res.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=res.get("error", "Failed to compute pipeline summary."),
            )
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET /pipeline-summary: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/revenue-summary", tags=["Analytics"])
async def get_revenue_summary() -> Dict[str, Any]:
    """
    Returns overall revenue summary (invoiced amount, collected amount, pending collection).
    """
    logger.info("GET /revenue-summary endpoint called.")
    try:
        res = bi_service.get_revenue_summary()
        if not res.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=res.get("error", "Failed to compute revenue summary."),
            )
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET /revenue-summary: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/deals", tags=["Cleaned Datasets"])
async def get_deals() -> Dict[str, Any]:
    """
    Returns cleaned sales deals dataset from Monday.com.
    """
    logger.info("GET /deals endpoint called.")
    try:
        raw_deals = monday_service.get_deals()
        cleaned_res = cleaning_service.clean_deals(raw_deals)
        if not cleaned_res.get("success"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=cleaned_res.get("error", "Failed to retrieve deals."),
            )
        return cleaned_res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET /deals: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/work-orders", tags=["Cleaned Datasets"])
async def get_work_orders() -> Dict[str, Any]:
    """
    Returns cleaned work orders dataset from Monday.com.
    """
    logger.info("GET /work-orders endpoint called.")
    try:
        raw_work_orders = monday_service.get_work_orders()
        cleaned_res = cleaning_service.clean_work_orders(raw_work_orders)
        if not cleaned_res.get("success"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=cleaned_res.get("error", "Failed to retrieve work orders."),
            )
        return cleaned_res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET /work-orders: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/chat", tags=["AI BI Agent"], response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Processes a natural language business question using the Monday.com AI BI Agent.
    """
    logger.info(f"POST /chat endpoint called with question: '{request.question}'")
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )

    try:
        answer_text = ask(request.question)
        return ChatResponse(answer=answer_text)
    except Exception as e:
        logger.error(f"Error in POST /chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while answering your question: {str(e)}",
        )
