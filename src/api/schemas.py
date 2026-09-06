"""Pydantic schemas for the public REST contract."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class FaceAnalysisResponse(BaseModel):
    face_detected: bool
    face_count: int
    detection_confidence: float | None = None
    embedding_dimension: int | None = None
    image_quality: dict[str, Any] | None = None


class CandidateResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    post_id: str
    similarity_score: float
    image_path: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    search_id: str
    timestamp: str
    provider: str
    query: dict[str, Any] = Field(default_factory=dict)
    embedding_dimension: int | None = None
    candidate_count: int
    results: list[CandidateResponse] = Field(default_factory=list)


class MatchResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    match: bool
    confidence: float
    face_similarity: float
    image_similarity: float | None = None
    metadata_consistency: float | None = None
    threshold: float | None = None
    candidate: CandidateResponse | None = None


class BlockchainResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    transaction_hash: str | None = None
    block_number: int | None = None
    timestamp: str | int | None = None
    contract_address: str | None = None
    verifier: str | None = None
    status: int | None = None


class VerificationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    verified: bool
    status: str
    local_hash: str
    blockchain_hash: str | None = None
    on_chain_exists: bool = False
    timestamp: int | str | None = None
    verifier: str | None = None
    contract_address: str | None = None
    reason: str | None = None
    message: str | None = None


class PipelineResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    pipeline_id: str
    status: str = "completed"
    search: SearchResponse | None = None
    candidate: CandidateResponse | None = None
    match: MatchResponse | None = None
    evidence: dict[str, Any] | None = None
    evidence_path: str | None = None
    evidence_hash: str | None = None
    blockchain: BlockchainResponse | None = None
    reverification: VerificationResponse | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    components: dict[str, str]

