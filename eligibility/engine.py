from __future__ import annotations

from typing import Dict, List, Any

from kg.graph_store import InMemoryGraphStore
from logging_utils import logger
from .rules import EligibilityRuleSet, AtomicRule


class EligibilityEngine:
    """
    Evaluates dynamically constructed eligibility rule sets derived directly from the Knowledge Graph.
    """

    def __init__(self, graph_store: InMemoryGraphStore):
        logger.info("Initializing Rules Engine linked to Graph Store")
        self.graph_store = graph_store
        self.rulesets = self._build_rulesets_from_graph()

    def _build_rulesets_from_graph(self) -> List[EligibilityRuleSet]:
        rulesets = []
        for scheme_id in self.graph_store.schemes():
            details = self.graph_store.get_scheme_details(scheme_id)
            scheme_name = details.get("properties", {}).get("name", scheme_id)
            
            # Extract criteria rules dynamically
            atomic_rules = []
            for c in details.get("criteria", []):
                try:
                    op = c.get("operator", "==")
                    field = c.get("field")
                    value = c.get("value")
                    desc = c.get("description", f"{field} {op} {value}")
                    if field and value is not None:
                        atomic_rules.append(AtomicRule(
                            field=field,
                            op=op,
                            value=value,
                            description=desc
                        ))
                except Exception as e:
                    logger.warning(f"Failed to parse rule from criterion node {c.get('id')}: {e}")
            
            # Format benefits
            bens = [b.get("description", b.get("id")) for b in details.get("benefits", [])]
            benefits_text = " • ".join(bens) if bens else "No specific benefits listed."

            if atomic_rules:
                rulesets.append(EligibilityRuleSet(
                    scheme_id=scheme_id,
                    scheme_name=scheme_name,
                    rules=atomic_rules,
                    benefits=benefits_text,
                    provenance={"source": "Dynamic Knowledge Graph Graph-RAG"}
                ))
        
        logger.info(f"Loaded {len(rulesets)} eligibility rulesets dynamically.")
        return rulesets

    def evaluate_profile(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Ensure rulesets are fresh if graph dynamically changed
        self.rulesets = self._build_rulesets_from_graph()
        return [rs.evaluate(profile) for rs in self.rulesets]

__all__ = ["EligibilityEngine"]
