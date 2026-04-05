from __future__ import annotations

from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import config
from logging_utils import setup_logging, logger

from retrieval.vector_store import FAISSVectorStore
from kg.graph_store import InMemoryGraphStore
from eligibility.engine import EligibilityEngine

from .models import (
    QueryRequest, QueryResponse, EvidenceChunk,
    EligibilityRequest, EligibilityResponse, SchemeEligibilityResult,
    SchemeNode, GraphResponse
)


app = FastAPI(title="Graph Policy - RAG & KG AI Assistant")

# Allow the React dev server to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global dependencies
VECTOR_STORE: FAISSVectorStore | None = None
GRAPH_STORE: InMemoryGraphStore | None = None
ENGINE: EligibilityEngine | None = None

try:
    import google.generativeai as genai
    HAS_LLM = bool(config.gemini_api_key)
    if HAS_LLM:
        genai.configure(api_key=config.gemini_api_key)
except ImportError:
    HAS_LLM = False


@app.on_event("startup")
def startup_event() -> None:
    setup_logging()
    logger.info("Starting Graph Policy API")
    
    global VECTOR_STORE, GRAPH_STORE, ENGINE
    
    # Initialize FAISS Vector Store
    VECTOR_STORE = FAISSVectorStore()
    VECTOR_STORE.load_index()
    
    # Initialize Knowledge Graph
    GRAPH_STORE = InMemoryGraphStore()
    GRAPH_STORE.load()
    
    # Initialize dynamic Rules Engine
    ENGINE = EligibilityEngine(graph_store=GRAPH_STORE)


@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest) -> QueryResponse:
    """Graph-RAG Retrieval: Combines Hybrid Vector Search and Knowledge Graph Traversal"""
    if VECTOR_STORE is None or GRAPH_STORE is None:
        raise HTTPException(status_code=500, detail="Stores not fully initialized.")

    raw_query = request.question.strip()
    if not raw_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Hybrid Vector Search (FAISS + BM25)
    hits = VECTOR_STORE.similarity_search(raw_query, k=request.top_k)
    evidence = []
    avg_score = 0.0
    text_context = ""
    for h in hits:
        evidence.append(EvidenceChunk(text=h["text"], score=h["score"], metadata=h.get("metadata", {})))
        avg_score += h["score"]
        text_context += f"- {h['text']}\n"
    
    confidence = (avg_score / len(hits)) if hits else 0.0

    # 2. Extract keywords for Graph Traversal
    potential_services = []
    
    # Check graph nodes directly matching user query
    for sid in GRAPH_STORE.services():
        s_data = GRAPH_STORE.get_service_details(sid)
        s_name = s_data.get("properties", {}).get("name", "").lower()
        if s_name and s_name in raw_query.lower():
            potential_services.append(sid)
    
    if not potential_services and hits:
        # Infer services from hybrid vector metadata
        for h in hits:
            if "filename" in h["metadata"]:
                fn = h["metadata"]["filename"].replace(".pdf", "").replace(".txt", "").upper().replace(" ", "_")
                if fn in list(GRAPH_STORE.services()):
                    potential_services.append(fn)
            elif "source" in h["metadata"]:
                fn = Path(h["metadata"]["source"]).stem.upper().replace(" ", "_")
                if fn in list(GRAPH_STORE.services()):
                    potential_services.append(fn)

    potential_services = list(set(potential_services))

    # 3. Assemble Civic Knowledge Graph Context
    graph_context = ""
    for sid in potential_services:
        dt = GRAPH_STORE.get_service_details(sid)
        desc = dt.get("properties", {}).get("description", "")
        crts = [c.get("description", "") for c in dt.get("criteria", [])]
        bens = [b.get("description", "") for b in dt.get("benefits", [])]
        procs = [p.get("description", "") for p in dt.get("procedures", [])]
        docs = [d.get("name", "") for d in dt.get("documents", [])]
        auths = [a.get("name", "") for a in dt.get("authorities", [])]
        fees = [f.get("description", "") for f in dt.get("fees", [])]
        
        graph_context += f"\nService: {dt.get('properties', {}).get('name', sid)}\nDescription: {desc}\nAuthority: {', '.join(auths)}\nEligibility: {', '.join(crts)}\nBenefits: {', '.join(bens)}\nProcedure Steps: {', '.join(procs)}\nDocuments Required: {', '.join(docs)}\nFees: {', '.join(fees)}\n"

    # 4. Generate Answer via LLM
    response_data = {
        "answer": "No answer could be generated. See sources.",
        "steps": [],
        "documents_required": [],
        "fees": [],
        "authority": "Unknown"
    }
    
    import json
    if HAS_LLM and (text_context or graph_context):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            prompt = f"""
            You are an expert Indian civic assistant.
            Use the provided context to answer the user's question.
            Provide a strict JSON response completely satisfying the schema. 
            If information is missing from the context, state "Information not found in context".
            
            Text Sources (Vector & BM25):
            {text_context}
            
            Knowledge Graph Context:
            {graph_context}
            
            User Question: {raw_query}
            
            JSON Response Schema:
            {{
                "answer": "clear explanation string",
                "steps": ["step 1", "step 2"],
                "documents_required": ["doc 1", "doc 2"],
                "fees": ["fee 1", "fee 2"],
                "authority": "authoritative body string"
            }}
            """
            
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            parsed = json.loads(response.text)
            response_data.update(parsed)
        except Exception as e:
            logger.error(f"LLM Structured Generation failed: {e}")
            response_data["answer"] = "Error generating synthetic answer. Check logs."

    return QueryResponse(
        answer=response_data.get("answer", "No answer generated."),
        steps=response_data.get("steps", []),
        documents_required=response_data.get("documents_required", []),
        fees=response_data.get("fees", []),
        authority=response_data.get("authority", "Unknown"),
        schemes=potential_services,
        sources=evidence,
        confidence_score=confidence
    )


@app.post("/eligibility", response_model=EligibilityResponse)
def check_eligibility(request: EligibilityRequest) -> EligibilityResponse:
    if ENGINE is None:
        raise HTTPException(status_code=500, detail="Eligibility engine not initialized.")
    
    # Run evaluation
    results_raw = ENGINE.evaluate_profile(request.profile.dict())
    
    mapped_results = []
    for er in results_raw:
        # Build explanation rule trace
        rule_texts = []
        for rres in er["results"]:
            r = rres["rule"]
            status = rres["value"]
            if status is None:
                status_str = "Unknown"
            else:
                status_str = "Valid" if status else "Failed"
            rule_texts.append(f"{r.description} ({status_str})")
        
        mapped_results.append(SchemeEligibilityResult(
            scheme_id=er["scheme_id"],
            scheme_name=er["scheme_name"],
            label=er["label"],
            missing_fields=er["missing_fields"],
            explanation=" | ".join(rule_texts),
            benefits=er["benefits"]
        ))
    
    return EligibilityResponse(results=mapped_results)


@app.get("/services", response_model=List[SchemeNode])
def get_services():
    if GRAPH_STORE is None:
        raise HTTPException(status_code=500, detail="Graph store not initialized.")
    res = []
    for sid in GRAPH_STORE.services():
        dt = GRAPH_STORE.get_service_details(sid)
        res.append(SchemeNode(
            id=sid,
            name=dt.get("properties", {}).get("name", sid),
            description=dt.get("properties", {}).get("description", "")
        ))
    return res


@app.get("/service/{service_id}")
def get_service_details(service_id: str):
    if GRAPH_STORE is None:
        raise HTTPException(status_code=500, detail="Graph store not initialized.")
    dt = GRAPH_STORE.get_service_details(service_id)
    if not dt:
        raise HTTPException(status_code=404, detail="Service not found")
    return dt


@app.get("/graph", response_model=GraphResponse)
def get_full_graph():
    if GRAPH_STORE is None:
        raise HTTPException(status_code=500, detail="Graph store not initialized.")
    data = GRAPH_STORE.to_dict()
    # Format properties to `label` for the react frontend
    for node in data["nodes"]:
        node["group"] = node.get("type", "Unknown")
        name = node.get("properties", {}).get("name")
        desc = node.get("properties", {}).get("description")
        field = node.get("properties", {}).get("field")
        val = node.get("properties", {}).get("value")
        # Heuristic label assignment
        if name:
            node["label"] = name
        elif desc:
            node["label"] = desc
        elif field and val:
            node["label"] = f"{field} {val}"
        else:
            node["label"] = node["id"]
    return GraphResponse(nodes=data["nodes"], edges=data["edges"])
