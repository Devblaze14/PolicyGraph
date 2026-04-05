# PROJECT INFO — Beginner-Friendly Guide

## What is this project about?

Imagine a farmer in a rural village, a single mother in a small town, or a college
student from a low-income family. The Indian government runs **hundreds of welfare
schemes** (scholarships, subsidies, pensions, health cover, housing aid, etc.) for
people like them — but the information is scattered across dozens of websites, buried
inside long PDF documents, written in legal/bureaucratic language, and often
contradictory or outdated.

**Our project builds a smart assistant** that:

1. Reads and understands all those government scheme documents automatically.
2. Knows the eligibility rules for each scheme (age limits, income caps, category
   requirements, location restrictions, etc.).
3. Takes a citizen's basic profile (age, income, state, category, …) and **tells them
   exactly which schemes they qualify for**, with clear explanations and links back to
   the original documents as proof.

In short: **"Tell me about yourself and I'll tell you what the government can do for
you — with receipts."**

---

## What does "RAG" mean and why do we use it?

### The problem with a plain chatbot (LLM alone)

Large Language Models (like ChatGPT, Claude, Llama) are great at generating fluent
text, but they have two big problems for our use case:

- **They hallucinate.** They can confidently make up scheme names, wrong income limits,
  or fake eligibility rules that don't exist.
- **Their knowledge is frozen.** They were trained months ago; government schemes change
  every budget season.

### RAG = Retrieval-Augmented Generation

RAG is a technique that **fixes both problems** by adding a "look-it-up-first" step
before the AI answers:

```
   User Question
        │
        ▼
  ┌────────────┐      ┌──────────────────┐
  │  RETRIEVER  │─────▶│  RELEVANT CHUNKS  │  (actual text from govt docs)
  └────────────┘      └──────────────────┘
        │                       │
        │                       ▼
        │              ┌────────────────┐
        └─────────────▶│   LLM / Engine  │──▶  Answer + Citations
                       └────────────────┘
```

**Step-by-step in plain English:**

1. The user asks: *"Am I eligible for the PM-KISAN scheme?"*
2. The **Retriever** searches our database of pre-processed government documents and
   finds the 5 most relevant text passages (chunks) about PM-KISAN eligibility.
3. Those passages are handed to the **answer engine** along with the user's question.
4. The engine generates an answer **grounded in those real passages** — so it can say
   *"Yes, because [exact quote from the document]"* instead of guessing.

**Why this matters:**

| Without RAG | With RAG |
|---|---|
| AI might invent a fake rule | AI quotes the actual PDF |
| No way to verify the answer | Every claim has a citation |
| Outdated info | We re-ingest new docs anytime |
| One-size-fits-all | We retrieve passages specific to this user's state/category |

---

## What is a Knowledge Graph and why do we add one?

RAG alone treats documents as flat bags of text. But government schemes have
**structure**: a scheme *has* eligibility criteria, each criterion *checks* a field
(age, income, location), and a scheme *provides* certain benefits.

A **Knowledge Graph (KG)** stores this structure as a network of nodes and edges:

```
    [Scheme: PM-KISAN]
        │
        ├──HAS_CRITERION──▶ [Criterion: age >= 18]
        │                        └── provenance: "Guidelines.pdf, §2.1"
        │
        ├──HAS_CRITERION──▶ [Criterion: occupation == "farmer"]
        │
        └──PROVIDES────────▶ [Benefit: ₹6000/year in 3 installments]
```

**Why we need both KG + vector search (not just one):**

| Vector search alone | KG alone | KG + Vector (our approach) |
|---|---|---|
| Finds relevant text passages | Knows scheme structure & rules | Knows structure AND can find supporting evidence |
| Can't reason about rules | Can check eligibility precisely | Can check eligibility AND cite the source |
| Might miss a criterion buried on page 47 | Has no free-text search | Graph narrows candidates, vectors find proof |

So our system does **hybrid retrieval**:

1. The KG quickly shortlists schemes whose criteria *could* match the user's profile.
2. The vector store finds the exact text passages that support or explain each
   criterion.
3. The eligibility engine runs the actual rule checks and labels each scheme.

---

## How does our system work end-to-end?

Here is the full flow, step by step:

### Phase A — Offline (done once, or when documents update)

```
  Government PDFs/HTMLs
        │
        ▼
  ┌──────────────┐
  │  1. INGESTOR  │   Collects raw files, records metadata (state, dept, date)
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  2. PARSER    │   Extracts text from PDFs (PyMuPDF), tables, headings
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  3. CHUNKER   │   Splits text into ~800-char chunks with metadata tags
  └──────┬───────┘
         │
         ├───────────────────────────┐
         ▼                           ▼
  ┌──────────────┐          ┌────────────────────┐
  │ 4. VECTOR DB  │          │ 5. ENTITY EXTRACTOR │
  │  (embeddings) │          │  (rules, criteria)  │
  └──────────────┘          └────────┬───────────┘
                                     ▼
                            ┌────────────────┐
                            │ 6. KNOWLEDGE    │
                            │    GRAPH (KG)   │
                            └────────────────┘
```

### Phase B — Online (every time a user asks a question)

```
  User fills profile (age, income, state, category, ...)
  User types a question
        │
        ▼
  ┌─────────────────────┐
  │ 7. QUERY CLASSIFIER  │  "Is this an eligibility check, a how-to, or general?"
  └──────────┬──────────┘
             ▼
  ┌─────────────────────────────────────────────┐
  │ 8. HYBRID RETRIEVAL                          │
  │   a. KG traversal → candidate schemes        │
  │   b. Vector search → supporting text chunks   │
  └──────────┬──────────────────────────────────┘
             ▼
  ┌─────────────────────────┐
  │ 9. ELIGIBILITY ENGINE    │   Runs rules against profile
  │   Eligible / Not / ???   │   Generates rule-by-rule trace
  └──────────┬──────────────┘
             ▼
  ┌─────────────────────────┐
  │ 10. ANSWER + CITATIONS   │   Natural-language response with
  │     + CONFIDENCE LABEL   │   inline citations and next steps
  └─────────────────────────┘
```

---

## What technologies/libraries do we use (and why)?

Here's every tool in our stack, explained simply:

### Python (language)

The standard language for AI/ML projects. All our code is Python.

### PyMuPDF (`fitz`)

A fast Python library to read PDF files and extract their text, page by page. We use
it in `parsers.py` to turn government PDFs into plain text sections.

### sentence-transformers

A library that converts text into **embeddings** — lists of numbers (vectors) that
capture the *meaning* of a sentence. Two sentences with similar meaning will have
similar vectors. We use the model `all-MiniLM-L6-v2` (small, fast, good enough for a
student project). This powers our semantic search: when a user asks a question, we
convert it into a vector and find the document chunks with the closest vectors.

### NumPy

The fundamental Python library for fast math on arrays. We use it to store our
embedding vectors and compute similarity scores (dot products) during search.

### NetworkX

A Python library for creating and querying graphs (nodes + edges). We use it as our
in-memory Knowledge Graph store. Each scheme is a node, each criterion is a node, and
edges connect them. Later you could swap this out for Neo4j (a real graph database) for
bigger datasets.

### FastAPI

A modern Python web framework for building APIs. Our backend server (`server.py`) uses
FastAPI to expose a `/query` endpoint: the Streamlit UI sends a JSON request with the
user's profile and question, and gets back eligibility results + evidence.

### Pydantic

A data validation library (comes built into FastAPI). We define the shape of requests
and responses as Pydantic models (`UserProfile`, `QueryRequest`, `QueryResponse`, etc.)
so that bad data is caught automatically.

### Streamlit

A dead-simple Python library for building web UIs. You write normal Python and Streamlit
turns it into an interactive web page with sliders, text inputs, buttons, etc. Our
`ui/app.py` is a single-file Streamlit app that collects the user profile, calls the
API, and displays results.

### Loguru

A nicer alternative to Python's built-in `logging` module. We use it for clean,
colored log messages during ingestion and serving.

### (Optional) Tesseract / ocrmypdf

For scanned PDFs that are just images (no selectable text), Tesseract does OCR (Optical
Character Recognition) — it "reads" the image and converts it to text. We haven't wired
this in yet, but it's the recommended tool when you encounter image-only PDFs.

### (Optional) OpenAI / Claude API or Llama

For the final answer generation step (turning retrieved evidence into a natural-language
response), you'd call an LLM. Right now our MVP does rule-based eligibility without an
LLM, but the next step is to add one for fluent, explained answers.

---

## What does each file/module in our code do?

Here's a tour of the project, file by file:

```
RAG_GOV/
├── pyproject.toml              ← Project metadata + list of dependencies
├── README.md                   ← Quick-start instructions
├── PROJECT_INFO.md             ← You are reading this file!
│
├── data/
│   ├── raw/                    ← Put government PDFs and HTML files here
│   └── processed/
│       └── chunks.jsonl        ← Auto-generated: one JSON line per text chunk
│
└── src/rag_gov/                ← All source code lives here
    │
    ├── config.py               ← Central settings: file paths, embedding model name
    ├── logging_utils.py        ← Sets up pretty logging with Loguru
    │
    ├── ingestion/              ← PHASE A: turning raw docs into searchable chunks
    │   ├── loaders.py          ←   Lists files in data/raw, assigns metadata
    │   ├── parsers.py          ←   Reads PDFs with PyMuPDF, outputs Section objects
    │   ├── chunking.py         ←   Splits sections into ~800-char Chunk objects
    │   └── run_ingest.py       ←   Script: runs the full pipeline, writes chunks.jsonl
    │
    ├── retrieval/              ← Semantic search over chunks
    │   └── vector_store.py     ←   Embeds chunks, builds numpy index, cosine search
    │
    ├── kg/                     ← Knowledge Graph layer
    │   ├── schema.py           ←   Defines node types (Scheme, Criterion, Benefit, ...)
    │   │                           and edge types (HAS_CRITERION, PROVIDES, CITES)
    │   └── graph_store.py      ←   In-memory graph (NetworkX), add nodes/edges, query
    │
    ├── eligibility/            ← Rule-based eligibility checking
    │   ├── rules.py            ←   AtomicRule (e.g. age>=18), EligibilityRuleSet per scheme
    │   └── engine.py           ←   Runs all rulesets against a user profile
    │
    ├── api/                    ← Backend HTTP server
    │   ├── models.py           ←   Pydantic shapes for request/response JSON
    │   └── server.py           ←   FastAPI app: /query endpoint, startup loading
    │
    ├── ui/                     ← Frontend
    │   └── app.py              ←   Streamlit web UI: profile form, results display
    │
    └── evaluation/             ← Testing & metrics
        ├── datasets.py         ←   Sample citizen profiles for testing
        └── metrics.py          ←   Accuracy metric: compare predicted vs gold labels
```

---

## Key concepts explained simply

### Embeddings

Think of an embedding as a "meaning fingerprint" for a sentence. The sentence
*"Annual income must not exceed 2.5 lakh"* gets converted into a list of 384 numbers.
A different sentence with similar meaning, like *"Family income should be below
₹250,000"*, will have a very similar list of numbers. This lets us do **meaning-based
search** instead of keyword matching.

### Cosine similarity

The way we measure how similar two embeddings are. It's the dot product of the two
vectors after normalizing them to length 1. A score of 1.0 = identical meaning, 0.0 =
completely unrelated.

### Chunks

We don't embed entire 50-page PDFs as one vector — that would lose detail. Instead, we
split each document into small pieces (~800 characters each), called **chunks**. Each
chunk gets its own embedding. When searching, we find the most relevant *chunks*, not
the most relevant *documents*.

### Knowledge Graph triples

A Knowledge Graph stores facts as (subject, relation, object) triples:
- (PM-KISAN, HAS_CRITERION, age >= 18)
- (PM-KISAN, PROVIDES, ₹6000/year)
- (Criterion: age >= 18, CITES, "Guidelines.pdf, page 3")

This structured format lets us do precise reasoning (check if a rule is satisfied)
instead of relying purely on text similarity.

### Eligibility labels

When we check a user against a scheme, we output one of:
- **ELIGIBLE** — all criteria are satisfied.
- **NOT_ELIGIBLE** — at least one criterion clearly fails.
- **INSUFFICIENT_INFO** — some criteria can't be checked because the user didn't
  provide that field (e.g., they left "occupation" blank).

This three-way labeling is important because it's **honest** — we don't guess when we
don't have enough data.

### Citations / Provenance

Every claim our system makes should point back to the exact document, page, and
sentence it came from. This is called **provenance**. It's crucial for government
information because users need to trust the answer and officials need to verify it.

---

## How is this different from just using ChatGPT?

| ChatGPT / plain LLM | Our system (RAG + KG) |
|---|---|
| Might hallucinate scheme names or rules | Every fact is retrieved from real documents |
| Can't check your specific eligibility | Has an engine that evaluates rules against your profile |
| No citations | Every claim cites the source PDF, page, and section |
| Doesn't know about policy updates | We re-ingest documents when policies change |
| Treats all users the same | Personalizes based on your age, income, state, category |
| Black box — no explanation | Shows rule-by-rule trace: "age ≥ 18 ✓, income ≤ 2.5L ✗" |

---

## A concrete example walkthrough

**User inputs:**
- Age: 22
- Income: ₹1,40,000
- Category: SC
- State: Rajasthan
- Student: Yes

**User asks:** *"What scholarships am I eligible for?"*

**What happens inside the system:**

1. The **query classifier** detects this is an eligibility-check question.
2. The **KG** is traversed: find all Scheme nodes where type = "scholarship" and
   applies_in includes "Rajasthan" or "All India".
3. Say it finds 3 candidate schemes: Post-Matric Scholarship, Merit-cum-Means, and
   National Fellowship.
4. The **eligibility engine** checks each scheme's rules against the profile:
   - Post-Matric Scholarship: age ✓, income ≤ 2.5L ✓, category in [SC,ST] ✓ →
     **ELIGIBLE**
   - Merit-cum-Means: age ✓, income ≤ 2.5L ✓, category in [OBC] ✗ →
     **NOT_ELIGIBLE** (requires OBC)
   - National Fellowship: age ✓, income ✓, category ✓, but needs "enrolled in PhD" →
     **INSUFFICIENT_INFO** (we don't know their degree level)
5. The **vector store** retrieves the top passages about Post-Matric Scholarship
   eligibility from the actual PDF.
6. The system returns:

   > **Post-Matric Scholarship — ELIGIBLE**
   > You meet all criteria: age ≥ 18 ✓, income ≤ ₹2.5L ✓, category SC ✓.
   > *"Students belonging to SC/ST communities with family income not exceeding
   > ₹2,50,000 are eligible."* — [Post-Matric Guidelines.pdf, §2.1]
   >
   > **National Fellowship — INSUFFICIENT INFO**
   > We need to know your current degree level (enrolled in PhD?).

---

## What makes this project research-worthy?

Most RAG tutorials just do: "embed documents → retrieve → ask an LLM." Our project
goes further in three specific ways:

1. **Structured eligibility reasoning** — We don't just retrieve text; we extract
   actual rules (age ≥ X, income ≤ Y) and execute them against user profiles. This
   gives precise, verifiable, explainable results.

2. **Provenance-first knowledge graph** — Every edge in our graph links back to the
   exact sentence in the source document. This makes the system auditable and
   trustworthy for government use.

3. **Honest uncertainty handling** — The system explicitly says "I don't know" when
   data is missing or sources conflict, instead of guessing. This is rare in current
   RAG systems and important for public policy applications.

---

## Glossary of terms

| Term | Plain English |
|---|---|
| **RAG** | Retrieval-Augmented Generation — look up relevant info first, then answer |
| **LLM** | Large Language Model — AI that generates text (GPT, Claude, Llama) |
| **Embedding** | A list of numbers representing the meaning of a text |
| **Vector store** | A database of embeddings that supports similarity search |
| **Knowledge Graph (KG)** | A network of facts stored as (entity, relation, entity) |
| **Chunk** | A small piece of a document (~800 chars) used for embedding |
| **Cosine similarity** | A number (0 to 1) measuring how similar two vectors are |
| **Provenance** | The source reference (doc, page, sentence) for a claim |
| **Eligibility engine** | Code that checks scheme rules against a user's profile |
| **FastAPI** | Python web framework for building our backend API |
| **Streamlit** | Python library for building our frontend web UI |
| **NetworkX** | Python library for in-memory graphs |
| **PyMuPDF** | Python library for reading PDFs |
| **OCR** | Optical Character Recognition — reading text from images |
| **Pydantic** | Data validation library used for API request/response shapes |

---

## FAQ for team members

**Q: Do I need a GPU?**
A: No. The embedding model (`all-MiniLM-L6-v2`) runs fine on CPU. If you later add a
local LLM (Llama), you'll want a GPU, but for the MVP everything runs on a normal
laptop.

**Q: Do I need an OpenAI API key?**
A: Not for the current MVP. The eligibility engine is rule-based and the retrieval uses
local embeddings. You'll need an API key only when you add LLM-based answer generation
(Phase 2).

**Q: How many documents do we need?**
A: Start with 5–10 scheme PDFs from 1–2 states. That's enough to demonstrate the full
pipeline. You can scale up later.

**Q: Can I use this for a real government deployment?**
A: Not yet — this is a research prototype. For real deployment you'd need thorough
testing, legal review, accessibility compliance, and ongoing maintenance. But this
project proves the concept and architecture.

**Q: What if a PDF is a scanned image?**
A: Use Tesseract OCR (via `ocrmypdf`) to convert it to searchable text first, then
feed it into our parser. We haven't wired this in automatically yet, but it's a
straightforward addition.

---

*This file is meant to help every team member — even someone who has never worked with
NLP or RAG before — understand what we're building and why each piece exists.*
