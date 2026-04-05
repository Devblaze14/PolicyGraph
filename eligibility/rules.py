from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from logging_utils import logger

class Comparison(str, Enum):
    LTE = "<="
    GTE = ">="
    EQ = "=="
    IN = "in"
    LT = "<"
    GT = ">"


@dataclass
class AtomicRule:
    """
    Dynamically loaded rule from the Knowledge Graph.
    Can be instantiated from properties of a Criterion node.
    """
    field: str
    op: Comparison
    value: Any
    description: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AtomicRule:
        return cls(
            field=str(data.get("field", "")),
            op=Comparison(data.get("operator", "==")),
            value=data.get("value"),
            description=str(data.get("description", ""))
        )

    def evaluate(self, profile: Dict[str, Any]) -> bool | None:
        if self.field not in profile or profile[self.field] is None:
            return None  # unknown / missing
        v = profile[self.field]
        val = self.value
        
        # Basic type coercion if comparing numbers to string rules
        try:
            if isinstance(v, (int, float)) and isinstance(val, str):
                val = float(val)
        except ValueError:
            pass

        if self.op == Comparison.LTE:
            return v <= val
        if self.op == Comparison.LT:
            return v < val
        if self.op == Comparison.GTE:
            return v >= val
        if self.op == Comparison.GT:
            return v > val
        if self.op == Comparison.EQ:
            return v == val
        if self.op == Comparison.IN:
            if isinstance(val, str):
                val = [x.strip() for x in val.split(",")]
            return v in val
        return None


@dataclass
class EligibilityRuleSet:
    scheme_id: str
    scheme_name: str
    rules: List[AtomicRule]
    benefits: str
    provenance: Dict[str, Any]

    def evaluate(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        results = []
        missing = []
        for r in self.rules:
            val = r.evaluate(profile)
            if val is None:
                missing.append(r.field)
            results.append({"rule": r, "value": val})

        if any(r["value"] is False for r in results):
            label = "NOT_ELIGIBLE"
        elif missing:
            label = "INSUFFICIENT_INFO"
        else:
            label = "ELIGIBLE"

        return {
            "scheme_id": self.scheme_id,
            "scheme_name": self.scheme_name,
            "label": label,
            "results": results,
            "missing_fields": sorted(set(missing)),
            "benefits": self.benefits,
            "provenance": self.provenance,
        }

__all__ = ["Comparison", "AtomicRule", "EligibilityRuleSet"]
