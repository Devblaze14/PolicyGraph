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
    CONTAINS = "contains"


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
        
        # Basic normalization for booleans
        def normalize_bool(x: Any) -> Any:
            if isinstance(x, bool):
                return x
            if str(x).lower() in ["true", "yes", "y"]:
                return True
            if str(x).lower() in ["false", "no", "n"]:
                return False
            return x

        # Coerce both to bool if either looks like a bool
        v_norm = normalize_bool(v)
        val_norm = normalize_bool(val)
        if isinstance(v_norm, bool) or isinstance(val_norm, bool):
            v = v_norm
            val = val_norm

        # Basic type coercion if comparing numbers to string rules
        try:
            # If both are numbers or strings that look like numbers
            if not isinstance(v, bool) and not isinstance(val, bool):
                v_f = float(v)
                val_f = float(val)
                v = v_f
                val = val_f
        except (ValueError, TypeError):
            pass

        if self.op == Comparison.LTE:
            try: return v <= val
            except: return False
        if self.op == Comparison.LT:
            try: return v < val
            except: return False
        if self.op == Comparison.GTE:
            try: return v >= val
            except: return False
        if self.op == Comparison.GT:
            try: return v > val
            except: return False
        if self.op == Comparison.EQ:
            # Case-insensitive string comparison
            if isinstance(v, str) and isinstance(val, str):
                return v.lower() == val.lower()
            return v == val
        if self.op == Comparison.IN:
            if isinstance(val, str):
                val = [x.strip() for x in val.split(",")]
            # Ensure val is a list/set for membership test
            if not isinstance(val, (list, set, tuple)):
                val = [val]
            
            # Handle "All" / "All India" as wildcards
            wildcards = ["all", "all india", "all states", "any"]
            if any(str(x).lower() in wildcards for x in val):
                return True
            
            # Case-insensitive check for strings
            if isinstance(v, str):
                return any(str(x).lower() == v.lower() for x in val)
            
            return v in val
        if self.op == Comparison.CONTAINS:
            return str(val).lower() in str(v).lower()
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
