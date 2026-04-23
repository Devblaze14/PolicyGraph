from __future__ import annotations

from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from config import config
from logging_utils import setup_logging, logger

from retrieval.vector_store import FAISSVectorStore
from kg.graph_store import InMemoryGraphStore
from eligibility.engine import EligibilityEngine

from .models import (
    QueryRequest, QueryResponse, EvidenceChunk,
    EligibilityRequest, EligibilityResponse, SchemeEligibilityResult,
    SchemeNode, GraphResponse, CombinedRequest
)


app = FastAPI(title="Graph Policy - RAG & KG AI Assistant")

# Allow the React dev server to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global dependencies
VECTOR_STORE: FAISSVectorStore | None = None
GRAPH_STORE: InMemoryGraphStore | None = None
ENGINE: EligibilityEngine | None = None
QUERIES_COUNT: int = 0

try:
    import google.generativeai as genai
    HAS_GEMINI = bool(config.gemini_api_key)
    if HAS_GEMINI:
        genai.configure(api_key=config.gemini_api_key)
except ImportError:
    HAS_GEMINI = False

try:
    from groq import Groq
    HAS_GROQ = bool(config.groq_api_key)
except ImportError:
    HAS_GROQ = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

HAS_LLM = HAS_GEMINI or HAS_GROQ or HAS_OPENAI


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
    global QUERIES_COUNT
    QUERIES_COUNT += 1
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
        "answer": "I found some relevant information but couldn't synthesize a complete answer. Please check the 'Source Evidence' section below for details from the government documents.",
        "steps": [],
        "documents_required": [],
        "fees": [],
        "authority": "Unknown"
    }

    # Out-of-scope detection: If confidence is extremely low and no graph context
    if (confidence < 0.012 and not potential_services) or (not hits and not potential_services):
        return QueryResponse(
            answer="The entered input is not matching with any schema. Please ask about Indian government schemes, policies, or civic services.",
            steps=[],
            documents_required=[],
            fees=[],
            authority="N/A",
            schemes=[],
            sources=[],
            confidence_score=confidence
        )
    
    import json
    if HAS_LLM:
        try:
            # Enhanced Prompt for Multi-Document Synthesis
            prompt = f"""
            You are an expert Indian civic assistant. Your goal is to provide a comprehensive, accurate, and helpful answer based on official government documents.
            
            Context from Government Documents (Vector Search):
            {text_context if text_context else "No direct text matches found."}
            
            Knowledge Graph Context (Relationships):
            {graph_context if graph_context else "No related schemes found in graph."}
            
            User Question: {raw_query}
            
            INSTRUCTIONS:
            1. If the context contains the answer, synthesize it clearly.
            2. If the context is incomplete, use your broad knowledge of Indian government procedures to fill in the gaps (e.g. standard document requirements like Aadhaar, PAN, etc.).
            3. If the question is general (e.g. "schemes for farmers"), summarize the most relevant schemes found in the context.
            4. If the question is completely unrelated to government schemes, policies, or civic services, state that the input does not match any known schemes.
            5. Be extremely detailed in the "steps" and "documents_required" sections.
            6. Provide a strict JSON response.
            
            JSON Response Schema:
            {{
                "answer": "A detailed explanation synthesizing all available information.",
                "steps": ["Step 1...", "Step 2..."],
                "documents_required": ["Document A...", "Document B..."],
                "fees": ["Mention any applicable fees or 'Free of cost'"],
                "authority": "The government department or nodal agency"
            }}
            """
            
            if config.llm_provider == "groq" and HAS_GROQ:
                from groq import Groq
                client = Groq(api_key=config.groq_api_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "You are a helpful Indian government policy expert. Return only JSON."},
                               {"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                raw_json = response.choices[0].message.content
                parsed = json.loads(raw_json)
                response_data.update(parsed)
            elif HAS_GEMINI and config.llm_provider == "google-genai":
                model = genai.GenerativeModel("gemini-1.5-flash-latest")
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json"
                    )
                )
                parsed = json.loads(response.text)
                response_data.update(parsed)
            elif config.llm_provider in ["grok", "huggingface"] and HAS_OPENAI:
                from openai import OpenAI
                if config.llm_provider == "grok":
                    client = OpenAI(api_key=config.grok_api_key, base_url="https://api.x.ai/v1")
                    model_name = "grok-beta"
                else:
                    client = OpenAI(api_key=config.hf_api_key, base_url="https://router.huggingface.co/v1/")
                    model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                raw_json = response.choices[0].message.content
                parsed = json.loads(raw_json)
                response_data.update(parsed)
            else:
                response_data["answer"] = "LLM provider not configured. Please check your .env file for GROQ_API_KEY or GEMINI_API_KEY."
        except Exception as e:
            logger.error(f"LLM Structured Generation failed: {e}")
            err_str = str(e)
            if "401" in err_str or "invalid_api_key" in err_str.lower() or "Invalid API Key" in err_str:
                response_data["answer"] = f"Authentication failed with Groq. Please verify GROQ_API_KEY in your .env file is correct and active."
            elif "404" in err_str or "model_not_found" in err_str.lower() or "decommissioned" in err_str.lower():
                response_data["answer"] = f"Groq model not found or deprecated. Error: {err_str[:150]}"
            else:
                response_data["answer"] = f"An error occurred while generating the answer: {err_str[:150]}... Please refer to the source evidence below."

    # Normalization to prevent Pydantic Validation Errors
    def to_list(val: Any) -> List[str]:
        if isinstance(val, list):
            return [str(x) for x in val]
        if isinstance(val, str):
            if not val.strip(): return []
            return [val]
        return []

    def to_str(val: Any) -> str:
        if isinstance(val, list):
            return ", ".join([str(x) for x in val])
        return str(val) if val is not None else "Unknown"

    return QueryResponse(
        answer=to_str(response_data.get("answer", "No answer generated.")),
        steps=to_list(response_data.get("steps", [])),
        documents_required=to_list(response_data.get("documents_required", [])),
        fees=to_list(response_data.get("fees", [])),
        authority=to_str(response_data.get("authority", "Unknown")),
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
@app.get("/metrics")
def get_metrics():
    if GRAPH_STORE is None:
        return {"error": "Graph store not initialized"}
    
    # 1. Count policies
    policies = len(list(GRAPH_STORE.services()))
    
    # 2. Count raw documents
    raw_files = list(config.paths.data_raw.glob("*"))
    doc_count = len([f for f in raw_files if f.is_file() and not f.name.startswith(".")])
    
    # 3. Graph stats
    graph_data = GRAPH_STORE.to_dict()
    node_count = len(graph_data["nodes"])
    edge_count = len(graph_data["edges"])
    
    return {
        "policies_indexed": policies,
        "documents_processed": doc_count,
        "queries_answered": QUERIES_COUNT,
        "graph_nodes": node_count,
        "graph_edges": edge_count,
        "status": "Healthy"
    }
@app.post("/query")
def combined_query(request: CombinedRequest):
    """
    Combined endpoint for the Streamlit UI.
    Performs eligibility check and then retrieves evidence for the schemes.
    """
    if ENGINE is None or VECTOR_STORE is None:
        raise HTTPException(status_code=500, detail="Services not fully initialized.")

    # 1. Run eligibility check
    eligibility_resp = check_eligibility(EligibilityRequest(profile=request.profile))
    results = eligibility_resp.results

    # 2. For each scheme, retrieve evidence if it's relevant
    # We use the question and scheme name to find evidence
    for res in results:
        scheme_query = f"{request.question} {res.scheme_name}"
        hits = VECTOR_STORE.similarity_search(scheme_query, k=3)
        evidence_chunks = []
        for h in hits:
            evidence_chunks.append(EvidenceChunk(
                text=h["text"], 
                score=h["score"], 
                metadata=h.get("metadata", {})
            ))
        res.evidence = evidence_chunks

    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
