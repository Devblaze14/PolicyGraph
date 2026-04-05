from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Iterable, Any

import networkx as nx

from .schema import Node, Edge, NodeType, EdgeType
from config import config
from logging_utils import logger


class InMemoryGraphStore:
    """
    In-memory KG using NetworkX. Completely dynamic and supports saving/loading.
    """

    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()
        self.path = config.paths.data_indices / "graph.json"

    def add_node(self, node: Node) -> None:
        self.g.add_node(node.id, type=node.type.value, **node.properties)

    def add_edge(self, edge: Edge) -> None:
        self.g.add_edge(edge.source, edge.target, key=edge.type.value, type=edge.type.value, **edge.properties)

    def save(self) -> None:
        data = nx.node_link_data(self.g)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Knowledge Graph saved to {self.path} ({self.g.number_of_nodes()} nodes, {self.g.number_of_edges()} edges)")

    def load(self) -> None:
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.g = nx.node_link_graph(data)
            logger.info(f"Knowledge Graph loaded from {self.path} ({self.g.number_of_nodes()} nodes)")
        else:
            logger.warning(f"No existing Knowledge Graph found at {self.path}. Starting fresh.")

    def get_service_details(self, service_id: str) -> Dict[str, Any]:
        """
        Retrieves all connected entities for a service (scheme, civic identity, etc).
        """
        if service_id not in self.g:
            return {}
        
        details = {
            "id": service_id,
            "properties": dict(self.g.nodes[service_id]),
            "criteria": [],
            "benefits": [],
            "procedures": [],
            "documents": [],
            "authorities": [],
            "fees": [],
            "states": [],
            "categories": [],
            "target_groups": []
        }
        for _, tgt, key, data in self.g.out_edges(service_id, keys=True, data=True):
            node_data = self.g.nodes[tgt]
            node_type = node_data.get("type")
            edge_type = data.get("type")
            
            if edge_type == EdgeType.HAS_ELIGIBILITY.value:
                details["criteria"].append({"id": tgt, **node_data})
            elif edge_type == EdgeType.PROVIDES_BENEFIT.value:
                details["benefits"].append({"id": tgt, **node_data})
            elif edge_type == EdgeType.HAS_PROCEDURE.value:
                details["procedures"].append({"id": tgt, **node_data})
            elif edge_type == EdgeType.REQUIRES_DOCUMENT.value:
                details["documents"].append({"id": tgt, **node_data})
            elif edge_type == EdgeType.PERFORMED_BY.value:
                details["authorities"].append({"id": tgt, **node_data})
            elif edge_type == EdgeType.HAS_FEE.value:
                details["fees"].append({"id": tgt, **node_data})
            elif edge_type == EdgeType.AVAILABLE_IN.value:
                details["states"].append({"id": tgt, **node_data})
            elif edge_type == EdgeType.TARGETS.value:
                details["target_groups"].append({"id": tgt, **node_data})
            elif node_type == NodeType.CATEGORY.value:
                details["categories"].append({"id": tgt, **node_data})
        
        return details

    def get_related_nodes(self, node_id: str, max_depth: int = 1) -> Dict[str, Any]:
        if node_id not in self.g:
            return {"nodes": [], "edges": []}
        
        edges = nx.bfs_edges(self.g, node_id, depth_limit=max_depth)
        nodes = {node_id}
        result_edges = []
        for u, v in edges:
            nodes.add(v)
            for k, dat in self.g[u][v].items():
                result_edges.append({"source": u, "target": v, "type": dat.get("type"), "properties": dat})
        
        result_nodes = [{"id": n, "type": self.g.nodes[n].get("type"), "properties": dict(self.g.nodes[n])} for n in nodes]
        return {"nodes": result_nodes, "edges": result_edges}

    def services(self) -> Iterable[str]:
        for nid, data in self.g.nodes(data=True):
            if data.get("type") in [NodeType.SERVICE.value, NodeType.SCHEME.value]:
                yield nid

    def schemes(self) -> Iterable[str]:  # Legacy support for EligibilityEngine
        return self.services()

    def get_scheme_details(self, scheme_id: str) -> Dict[str, Any]:
        return self.get_service_details(scheme_id)

    def to_dict(self) -> Dict[str, Any]:
        nodes = [{"id": n, "type": dat.get("type"), "properties": {k: v for k, v in dat.items() if k != "type"}} for n, dat in self.g.nodes(data=True)]
        edges = [{"source": u, "target": v, "type": dat.get("type"), "properties": {k: v for k, v in dat.items() if k != "type"}} for u, v, k, dat in self.g.edges(keys=True, data=True)]
        return {"nodes": nodes, "edges": edges}


__all__ = ["InMemoryGraphStore"]
