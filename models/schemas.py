"""
Pydantic schemas for API requests, responses, and agent state objects.
Placeholder file - schemas to be defined.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    board_id: Optional[str] = None


class QueryResponse(BaseModel):
    query: str
    result: str
    data: Optional[Dict[str, Any]] = None
