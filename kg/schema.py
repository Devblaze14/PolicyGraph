from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any

class NodeType(str, Enum):
    SERVICE = "Service"
    SCHEME = "Scheme"
    DOCUMENT = "Document"
    PROCEDURE = "Procedure"
    AUTHORITY = "Authority"
    FEE = "Fee"
    CRITERION = "EligibilityCriterion"
    BENEFIT = "Benefit"
    STATE = "State"
    CATEGORY = "Category"
    TARGET_GROUP = "TargetGroup"

class EdgeType(str, Enum):
    REQUIRES_DOCUMENT = "SERVICE_REQUIRES_DOCUMENT"
    PERFORMED_BY = "SERVICE_PERFORMED_BY"
    HAS_PROCEDURE = "SERVICE_HAS_PROCEDURE"
    HAS_FEE = "SERVICE_HAS_FEE"
    AVAILABLE_IN = "SERVICE_AVAILABLE_IN_STATE"
    HAS_ELIGIBILITY = "SCHEME_HAS_ELIGIBILITY"
    PROVIDES_BENEFIT = "SCHEME_PROVIDES_BENEFIT"
    TARGETS = "SCHEME_TARGETS_GROUP"
    CITES = "CITES"

class Node(BaseModel):
    id: str
    type: NodeType
    properties: Dict[str, Any] = Field(default_factory=dict)

class Edge(BaseModel):
    source: str
    target: str
    type: EdgeType
    properties: Dict[str, Any] = Field(default_factory=dict)

__all__ = ["NodeType", "EdgeType", "Node", "Edge"]
