from __future__ import annotations

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    income: Optional[float] = None
    category: Optional[str] = Field(None, description="e.g. SC, ST, OBC, General")
    state: Optional[str] = None
    district: Optional[str] = None
    occupation: Optional[str] = None
    disability: Optional[bool] = None
    student: Optional[bool] = None


class QueryRequest(BaseModel):
    question: str
    top_k: int = 10


class EvidenceChunk(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    answer: str
    steps: List[str]
    documents_required: List[str]
    fees: List[str]
    authority: str
    schemes: List[str]
    sources: List[EvidenceChunk]
    confidence_score: float


class EligibilityRequest(BaseModel):
    profile: UserProfile


class SchemeEligibilityResult(BaseModel):
    scheme_id: str
    scheme_name: str
    label: str
    missing_fields: List[str]
    explanation: str
    benefits: str
    evidence: Optional[List[EvidenceChunk]] = Field(default_factory=list)


class EligibilityResponse(BaseModel):
    results: List[SchemeEligibilityResult]


class SchemeNode(BaseModel):
    id: str
    name: str
    description: str


class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class CombinedRequest(BaseModel):
    profile: UserProfile
    question: str
    top_k: int = 10


__all__ = [
    "UserProfile", "QueryRequest", "QueryResponse", 
    "SchemeEligibilityResult", "EvidenceChunk", 
    "EligibilityRequest", "EligibilityResponse",
    "SchemeNode", "GraphResponse", "CombinedRequest"
]
