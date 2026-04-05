# Graph Policy - AI Powered Policy Assistant

Graph Policy is an enterprise-grade AI assistant capable of processing complex government schemes, modeling them dynamically using **Knowledge Graphs**, and conducting natural language **Retrieval Augmented Generation (RAG)** search combined with deterministic Eligibility Evaluation.

## Complete Architecture Overview
This is a production-ready rewrite supporting completely dynamic, data-driven reasoning.

1. **Ingestion Pipeline (`ingestion/pipeline.py`)** 
   - Downloads, parses, and chunks raw PDF, HTML, and TXT data natively using `LangChain` loaders.
   - Leverages Heuristics or Google Gemini (if configured in `.env`) to parse explicit Scheme Nodes, Benefits, Criterions, and State structures into our Knowledge Graph without hardcoding anything.
2. **Retrieval Engine (`retrieval/vector_store.py`)**
   - Implements native **FAISS Vector indexing** using HuggingFaceEmbeddings (`all-MiniLM-L6-v2`) to capture context semantics and exact document sources.
3. **Dynamic Knowledge Graph (`kg/graph_store.py`)**
   - Maintains an `InMemoryGraphStore` via NetworkX mapping relationships like `HAS_ELIGIBILITY` and `PROVIDES_BENEFIT`.
   - Serializes directly to `data/indices/graph.json` so memory states persist.
4. **Data-Driven Eligibility (`eligibility/engine.py`)**
   - Completely removes hardcoded evaluations.
   - Evaluates a User Profile dynamically by fetching raw `Criterion` Nodes directly from the Knowledge Graph on a per-scheme basis and parsing relational operators (e.g. `<=`, `in`).
5. **Modern API Backend (`api/server.py`)**
   - Offers robust endpoints like `/query` (runs combined graph traversal + FAISS retrieval + LLM synthesis) and `/eligibility` (dynamic rule checking).
6. **Next-Generation React UI**
   - Built with Vite, Tailwind CSS v4, Framer Motion, and Recharts.
   - Includes real dashboard analytics, knowledge graph visualizations via `react-force-graph`, full Perplexity-like Search, and multi-colored Eligibility trace outputs.

---

## 🚀 Getting Started

### 1. Backend Setup & Ingestion
```bash
# Install dependencies
pip install -r requirements.txt pydantic-settings

# Start the Ingestion Pipeline. If no data exists, this will auto-seed
# the data/raw/ directory with PM-KISAN, Ayushman Bharat, PMAY, Startup India etc.,
# completely process them, build FAISS embeddings, and construct the KG.
python ingestion/run_ingest.py

# Optional: Ensure Gemini API is available for superior extractions and synthesize
# Add variable back into .env file if necessary.
echo "GEMINI_API_KEY=your_key" > .env

# Run the FastAPI server
uvicorn api.server:app --reload
```
*API will run on [http://localhost:8000](http://localhost:8000)*

### 2. Frontend Setup
```bash
cd ui/frontend
npm run dev
```
*Vite Server will run cleanly on [http://localhost:5173](http://localhost:5173)*

### 3. Evaluation
```bash
# Measure precision, recall, and F1 on document retrieval 
python evaluation/eval.py
```

### 4. Deployment Checklists

#### Option A: Docker Compose (All-in-one)
The repo contains a `Dockerfile`.
1. `docker build -t graph-policy-backend .`
2. `docker run -p 8000:8000 graph-policy-backend`

#### Option B: Render / Railway / AWS (Backend)
- Standard Uvicorn initialization. 
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn api.server:app --host 0.0.0.0 --port $PORT`

#### Option C: Vercel / Netlify (Frontend)
- Build Command: `cd ui/frontend && npm install && npm run build`
- Output Directory: `dist`
