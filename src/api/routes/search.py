"""Direct authorized-dataset search route."""

from fastapi import APIRouter
import numpy as np
from pydantic import BaseModel, Field

from src.api.schemas import SearchResponse
from src.search.orchestrator import search_detailed

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    embedding: list[float] = Field(..., min_length=512, max_length=512)
    top_k: int = Field(default=5, gt=0)


@router.post("/search", response_model=SearchResponse, summary="Search the authorized FAISS dataset")
def search(request: SearchRequest) -> SearchResponse:
    response = search_detailed(np.asarray(request.embedding, dtype=np.float32), top_k=request.top_k)
    return SearchResponse(**response.as_dict())
