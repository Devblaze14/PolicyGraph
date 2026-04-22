import os
from pathlib import Path
from typing import List, Dict, Any
import json
import re

from logging_utils import logger
from config import config

# Document Loading
from langchain_community.document_loaders import PyPDFLoader, TextLoader, BSHTMLLoader, WebBaseLoader
# Chunking
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Vector & Graph Stores
from retrieval.vector_store import FAISSVectorStore
from kg.graph_store import InMemoryGraphStore
from kg.schema import Node, Edge, NodeType, EdgeType

try:
    from pydantic import BaseModel, Field
    import google.generativeai as genai
except ImportError:
    pass

try:
    from groq import Groq
except ImportError:
    pass

class IngestionPipeline:
    def __init__(self, vector_store: FAISSVectorStore, graph_store: InMemoryGraphStore):
        self.vector_store = vector_store
        self.graph_store = graph_store
        # Civic service chunking (300 tokens, 50 overlap approx.)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200, # Approx 300 words/tokens
            chunk_overlap=200, # Approx 50 overlap
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )

    def process_file(self, file_path: Path):
        logger.info(f"Processing document: {file_path}")
        if file_path.suffix.lower() == ".json":
            self._process_json(file_path)
            return

        docs = []
        if file_path.suffix.lower() == ".pdf":
            loader = PyPDFLoader(str(file_path))
            docs = loader.load()
        elif file_path.suffix.lower() == ".html":
            loader = BSHTMLLoader(str(file_path))
            docs = loader.load()
        elif file_path.suffix.lower() == ".txt":
            loader = TextLoader(str(file_path))
            docs = loader.load()
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return

        full_text = " ".join([d.page_content for d in docs])
        logger.info("Extracting Knowledge Graph generalized Civic nodes and edges...")
        try:
            metadata_extracted = self._extract_kg_from_text(full_text, file_name=file_path.name)
        except Exception as e:
            logger.error(f"Failed to extract KG properties: {e}")
            metadata_extracted = {"service_type": "Unknown", "state": "All India", "category": "General"}

        # Vector Store Ingestion
        logger.info(f"Chunking {len(docs)} pages/sections...")
        
        # Inject metadata into chunks
        for doc in docs:
            doc.metadata.update(metadata_extracted)
            
        chunks = self.text_splitter.split_documents(docs)
        self.vector_store.add_documents(chunks)

    def _process_json(self, file_path: Path):
        """
        Processes structured JSON data, specifically the OpenNyAI schemes format.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                logger.info(f"Ingesting {len(data)} schemes from JSON...")
                for entry in data:
                    self._process_single_json_entry(entry)
            else:
                self._process_single_json_entry(data)
        except Exception as e:
            logger.error(f"Error processing JSON file {file_path}: {e}")

    def _process_single_json_entry(self, entry: Dict[str, Any]):
        """
        Maps a single JSON scheme entry to KG nodes and Vector Store documents.
        """
        scheme_name = entry.get("scheme_name", "Unknown Scheme")
        details = entry.get("details", "")
        benefits = entry.get("benefits", "")
        eligibility = entry.get("eligibility_criteria", "")
        process = entry.get("application_process", "")
        docs_req = entry.get("documents_required", "")
        
        # Combine into a descriptive text for the vector store
        combined_text = f"""
        Scheme Name: {scheme_name}
        Details: {details}
        Benefits: {benefits}
        Eligibility: {eligibility}
        Application Process: {process}
        Required Documents: {docs_req}
        Tags: {', '.join(entry.get('tags', []))}
        Category: {', '.join(entry.get('schemeCategory', []))}
        """
        
        # Create a document for the vector store
        from langchain_core.documents import Document
        metadata = {
            "service_name": scheme_name,
            "service_type": entry.get("schemeCategory", ["General"])[0] if entry.get("schemeCategory") else "General",
            "state": entry.get("beneficiaryState", ["All India"])[0] if entry.get("beneficiaryState") else "All India",
            "category": entry.get("schemeCategory", ["General"])[0] if entry.get("schemeCategory") else "General",
            "authority": "Government of India" # Default for this dataset
        }
        
        doc = Document(page_content=combined_text.strip(), metadata=metadata)
        chunks = self.text_splitter.split_documents([doc])
        self.vector_store.add_documents(chunks)

        # Build KG
        # Structured Criteria extraction
        criteria = []
        
        # 1. Age (Extract general range as baseline)
        age_data = entry.get("age", {}).get("general", {})
        if age_data.get("gte") is not None:
            criteria.append({"field": "age", "operator": ">=", "value": age_data["gte"], "description": f"Age >= {age_data['gte']}"})
        if age_data.get("lte") is not None:
            criteria.append({"field": "age", "operator": "<=", "value": age_data["lte"], "description": f"Age <= {age_data['lte']}"})
            
        # 2. Gender
        genders = entry.get("gender", [])
        if genders and "All" not in genders and "ALL" not in genders:
            criteria.append({"field": "gender", "operator": "in", "value": genders, "description": f"Gender in {genders}"})
            
        # 3. Caste / Category
        castes = entry.get("caste", [])
        if castes and "All" not in castes and "ALL" not in castes:
            criteria.append({"field": "category", "operator": "in", "value": castes, "description": f"Category in {castes}"})
            
        # 4. State
        states = entry.get("beneficiaryState", [])
        if states and "All" not in states and "ALL" not in states:
            criteria.append({"field": "state", "operator": "in", "value": states, "description": f"State in {states}"})
            
        # 5. Student status
        is_student = entry.get("isStudent")
        if is_student is not None:
            criteria.append({"field": "student", "operator": "==", "value": is_student, "description": f"Is Student: {is_student}"})

        # Base fallback
        if eligibility:
             criteria.append({"field": "eligibility", "operator": "contains", "value": eligibility, "description": "Full Eligibility Text Summary"})

        kg_data = {
            "service_name": scheme_name,
            "description": (entry.get("details") or entry.get("summary") or "").replace("\n", " ").strip(),
            "authority": "Government of India",
            "category": entry.get("schemeCategory", []),
            "state": entry.get("beneficiaryState", []),
            "procedures": [p.strip() for p in process.split("\n") if p.strip() and not p.lower().startswith("application process")],
            "required_documents": [d.strip() for d in docs_req.split("\n") if d.strip() and not d.lower().startswith("documents required")],
            "benefits": [{"description": b.strip()} for b in benefits.split("\n") if b.strip() and not b.lower().startswith("benefits")],
            "target_beneficiary": entry.get("tags", []),
            "criteria": criteria
        }
        
        self._build_kg_nodes(kg_data, file_name=scheme_name.replace(" ", "_"))

    def _extract_kg_from_text(self, text: str, file_name: str) -> Dict[str, Any]:
        """
        Dynamically extracts properties using a robust regex fallback 
        or LLM if configured.
        Returns base metadata to attach to chunks.
        """
        if config.llm_provider == "groq" and config.groq_api_key:
            return self._extract_with_groq(text, file_name)
        elif config.llm_provider == "google-genai" and config.gemini_api_key:
            return self._extract_with_gemini(text, file_name)
        else:
            return self._extract_with_heuristics(text, file_name)

    def _extract_with_groq(self, text: str, file_name: str) -> Dict[str, Any]:
        client = Groq(api_key=config.groq_api_key)
        prompt = f"""
        Extract generalized civic service and policy structured data from the following text into JSON format.
        Schema:
        - service_name: str
        - description: str
        - authority: str
        - procedures: [str] (Step by step procedure)
        - fees: [str]
        - required_documents: [str]
        - criteria: [{{field: str, operator: str, value: Any, description: str}}] (operators: ==, <=, >=, <, >, in)
        - benefits: [{{description: str}}]
        - state: [str]
        - target_beneficiary: [str]
        - category: [str]
        
        Text:
        {text[:10000]}
        
        Return ONLY RAW VALID JSON representing a dictionary with the above keys. No markdown.
        """
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
        self._build_kg_nodes(data, file_name)
        
        return {
            "service_type": data.get("category", ["General"])[0] if data.get("category") else "General",
            "state": data.get("state", ["All India"])[0] if data.get("state") else "All India",
            "category": data.get("category", ["General"])[0] if data.get("category") else "General",
            "authority": data.get("authority", "Unknown")
        }

    def _extract_with_gemini(self, text: str, file_name: str) -> Dict[str, Any]:
        genai.configure(api_key=config.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        prompt = f"""
        Extract generalized civic service and policy structured data from the following text into JSON format.
        Schema:
        - service_name: str
        - description: str
        - authority: str
        - procedures: [str] (Step by step procedure)
        - fees: [str]
        - required_documents: [str]
        - criteria: [{{field: str, operator: str, value: Any, description: str}}] (operators: ==, <=, >=, <, >, in)
        - benefits: [{{description: str}}]
        - state: [str]
        - target_beneficiary: [str]
        - category: [str]
        
        Text:
        {text[:10000]}
        
        Return ONLY RAW VALID JSON representing a dictionary with the above keys. No markdown.
        """
        response = model.generate_content(prompt)
        raw_json = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(raw_json)
        self._build_kg_nodes(data, file_name)
        
        return {
            "service_type": data.get("category", ["General"])[0] if data.get("category") else "General",
            "state": data.get("state", ["All India"])[0] if data.get("state") else "All India",
            "category": data.get("category", ["General"])[0] if data.get("category") else "General",
            "authority": data.get("authority", "Unknown")
        }

    def _extract_with_heuristics(self, text: str, file_name: str) -> Dict[str, Any]:
        # Quick fallback parsing for Civic entities using simple block detection
        blocks = text.split("\\n\\n")
        
        # Finding fields by labels
        def find_after(label: str) -> str:
            match = re.search(f"{label}:\\s*(.*)", text, re.IGNORECASE)
            return match.group(1).strip() if match else ""

        def find_list_after(label: str) -> List[str]:
            items = []
            capture = False
            for line in text.split("\\n"):
                if re.match(f"{label}:?", line, re.IGNORECASE):
                    capture = True
                    continue
                if capture:
                    if not line.strip(): 
                        break  
                    if line.strip().startswith("-") or line.strip()[0].isdigit():
                        items.append(line.strip().lstrip("-123456789. "))
                    else:
                        break
            return items

        name = find_after("Service Name") or find_after("Scheme Name") or file_name.replace(".txt", "").replace("_"," ")
        data = {
            "service_name": name,
            "description": find_after("Description") or text[:500],
            "authority": find_after("Authority") or "Govt of India",
            "category": [find_after("Category")] if find_after("Category") else ["General"],
            "state": [find_after("State")] if find_after("State") else ["All India"],
            "procedures": find_list_after("Procedure") or find_list_after("Application Process"),
            "required_documents": find_list_after("Required Documents"),
            "fees": find_list_after("Fees"),
            "benefits": [{"description": b} for b in find_list_after("Benefits")],
            "target_beneficiary": [find_after("Target Beneficiary")] if find_after("Target Beneficiary") else [],
            "criteria": [{"field": "general", "operator": "==", "value": "true", "description": c} for c in find_list_after("Eligibility Criteria")]
        }

        self._build_kg_nodes(data, file_name)
        return {
            "service_type": data["category"][0] if data["category"] else "General",
            "state": data["state"][0] if data["state"] else "All India",
            "category": data["category"][0] if data["category"] else "General",
            "authority": data["authority"]
        }

    def _build_kg_nodes(self, data: Dict[str, Any], file_name: str):
        service_id = data.get("service_name", file_name).upper().replace(" ", "_")
        
        # Service Node
        self.graph_store.add_node(Node(id=service_id, type=NodeType.SERVICE, properties={
            "name": data.get("service_name", file_name),
            "description": data.get("description", "")
        }))
        
        # Authority Node
        auth = data.get("authority", "")
        if auth:
            auth_id = f"AUTH_{auth.upper().replace(' ', '_')}"
            self.graph_store.add_node(Node(id=auth_id, type=NodeType.AUTHORITY, properties={"name": auth}))
            self.graph_store.add_edge(Edge(source=service_id, target=auth_id, type=EdgeType.PERFORMED_BY))

        # Documents Node
        for i, doc in enumerate(data.get("required_documents", [])):
            if not doc.strip(): continue
            doc_id = f"DOC_{hash(doc)}"
            self.graph_store.add_node(Node(id=doc_id, type=NodeType.DOCUMENT, properties={"name": doc}))
            self.graph_store.add_edge(Edge(source=service_id, target=doc_id, type=EdgeType.REQUIRES_DOCUMENT))
            
        # Procedure Nodes
        for i, proc in enumerate(data.get("procedures", [])):
            if not proc.strip(): continue
            proc_id = f"{service_id}_STEP_{i}"
            self.graph_store.add_node(Node(id=proc_id, type=NodeType.PROCEDURE, properties={"description": proc, "step": i+1}))
            self.graph_store.add_edge(Edge(source=service_id, target=proc_id, type=EdgeType.HAS_PROCEDURE))

        # Fees Node
        for i, fee in enumerate(data.get("fees", [])):
            if not fee.strip(): continue
            fee_id = f"{service_id}_FEE_{i}"
            self.graph_store.add_node(Node(id=fee_id, type=NodeType.FEE, properties={"description": fee}))
            self.graph_store.add_edge(Edge(source=service_id, target=fee_id, type=EdgeType.HAS_FEE))

        # Criteria
        for i, c in enumerate(data.get("criteria", [])):
            cid = f"{service_id}_CRIT_{i}"
            fmt_c = {"field": c.get("field"), "operator": c.get("operator"), "value": c.get("value"), "description": c.get("description")}
            self.graph_store.add_node(Node(id=cid, type=NodeType.CRITERION, properties=fmt_c))
            self.graph_store.add_edge(Edge(source=service_id, target=cid, type=EdgeType.HAS_ELIGIBILITY))

        # Benefits
        for i, b in enumerate(data.get("benefits", [])):
            bid = f"{service_id}_BEN_{i}"
            self.graph_store.add_node(Node(id=bid, type=NodeType.BENEFIT, properties={"description": b.get("description", b)}))
            self.graph_store.add_edge(Edge(source=service_id, target=bid, type=EdgeType.PROVIDES_BENEFIT))

        # States
        for s in data.get("state", []):
            if not s.strip(): continue
            sid = f"STATE_{s.upper().replace(' ', '_')}"
            self.graph_store.add_node(Node(id=sid, type=NodeType.STATE, properties={"name": s}))
            self.graph_store.add_edge(Edge(source=service_id, target=sid, type=EdgeType.AVAILABLE_IN))

        # Target Groups
        for t in data.get("target_beneficiary", []):
            if not t.strip(): continue
            tid = f"TARGET_{t.upper().replace(' ', '_')}"
            self.graph_store.add_node(Node(id=tid, type=NodeType.TARGET_GROUP, properties={"name": t}))
            self.graph_store.add_edge(Edge(source=service_id, target=tid, type=EdgeType.TARGETS))

        # Categories
        for cat in data.get("category", []):
            if not cat.strip(): continue
            catid = f"CAT_{cat.upper().replace(' ', '_')}"
            self.graph_store.add_node(Node(id=catid, type=NodeType.CATEGORY, properties={"name": cat}))
            self.graph_store.add_edge(Edge(source=service_id, target=catid, type=EdgeType.TARGETS))

    def ingest_directory(self, dir_path: Path):
        for file in dir_path.glob("**/*"):
            if file.is_file() and file.suffix.lower() in [".pdf", ".txt", ".html", ".json"]:
                self.process_file(file)
        
        self.vector_store.save_index()
        self.graph_store.save()

__all__ = ["IngestionPipeline"]
