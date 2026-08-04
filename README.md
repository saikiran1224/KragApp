# KragApp — RAG Application (Learning Journal)

A production-grade RAG (Retrieval-Augmented Generation) application built step by step as a hands-on learning project. This README serves as both documentation and a track sheet of everything built and learned.

---

## Goal

Build a complete RAG application from scratch — understanding every line of code — progressing through:

- **Phase 1** — Simple RAG (current) ← we are here
- **Phase 2** — Advanced RAG (query rewriting, re-ranking, hybrid search)
- **Phase 3** — Agentic RAG (tool-using agents, LangGraph)
- **Phase 4** — LLMOps (observability, evaluation, CI/CD)

All deployments target **AWS Serverless** — Docker container images on Lambda via ECR.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.13 | Standard for ML/AI work |
| LLM | Groq (`llama-3.1-8b-instant`) | Free tier, fast inference |
| Embeddings | Voyage AI (`voyage-3-lite`) | Free 200M tokens/month, API-based (no model weights in Docker image) |
| Vector Store | PostgreSQL + pgvector | Already provisioned on AWS RDS |
| Framework | LangChain + LangGraph | Best for the full journey: RAG → Agents |
| Deployment | Docker → ECR → Lambda | AWS Serverless |
| Observability | LangSmith (Phase 4) | Native LangChain integration |

---

## Project Structure

```
KragApp/
├── ingestion/
│   ├── __init__.py
│   ├── handler.py       # Lambda entrypoint — orchestrates the pipeline
│   ├── loader.py        # File type detection + text extraction
│   ├── chunker.py       # Text splitting into overlapping chunks
│   ├── embedder.py      # Voyage AI batch embedding
│   └── store.py         # pgvector write operations
│
├── retrieval/
│   ├── __init__.py
│   ├── handler.py       # Lambda entrypoint — orchestrates the pipeline
│   ├── embedder.py      # Voyage AI query embedding
│   ├── retriever.py     # pgvector cosine similarity search
│   └── generator.py     # Groq LLM answer generation
│
├── shared/
│   ├── __init__.py
│   └── config.py        # Centralised env vars and constants
│
├── db/
│   └── schema.sql       # pgvector table definitions and indexes
│
├── tests/
│   ├── test_ingestion.py
│   └── test_retrieval.py
│
├── docker-compose.yml   # Local Postgres + pgvector for development
├── Dockerfile.ingestion
├── Dockerfile.retrieval
├── requirements.txt
└── .env                 # Never commit this
```

---

## Phase 1 — Simple RAG

### Architecture

```
INGESTION PIPELINE                      QUERY PIPELINE
──────────────────                      ──────────────
Upload document                         User sends question
      ↓                                       ↓
loader.py                               embedder.py
Detect file type                        Embed the question
Extract raw text                        (embed_query)
      ↓                                       ↓
chunker.py                              retriever.py
Split into overlapping chunks           Cosine similarity search
(RecursiveCharacterTextSplitter)        Return top-k chunks
      ↓                                       ↓
embedder.py                             generator.py
Batch embed all chunks                  Build prompt with context
(embed_documents)                       Call Groq LLM
      ↓                                       ↓
store.py                                Return answer to user
Write to pgvector
```

### Supported File Types

| Extension | Library |
|---|---|
| `.pdf` | `pypdf` |
| `.docx` | `python-docx` |
| `.txt` | Python built-in |
| `.xlsx` | `openpyxl` |

---

## Database Schema

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    document_id bigserial PRIMARY KEY,
    file_name   text NOT NULL,
    file_type   text NOT NULL,
    uploaded_at timestamp DEFAULT now() NOT NULL,
    metadata    jsonb
);

CREATE TABLE chunks (
    id           bigserial PRIMARY KEY,
    document_id  bigint REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_text   text NOT NULL,
    embedding    vector(512) NOT NULL,
    chunk_index  int NOT NULL,
    metadata     jsonb
);

CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
```

**Why two tables?** Documents tracks the file. Chunks tracks every piece of it. One document → many chunks. The foreign key with `ON DELETE CASCADE` means deleting a document automatically deletes all its chunks.

**Why `jsonb` for metadata?** Unlike plain `text`, `jsonb` lets you query inside it — useful for filtering by page number, author, sheet name etc. in Advanced RAG.

---

## Key Concepts Learned

### Docker Compose
- `version` field is deprecated in Compose v2 but still common in tutorials
- Container names are auto-generated as `{project_name}-{service_name}-{replica_number}`
- Project name defaults to the folder name (lowercased)
- Named volumes persist data outside the container — survives container restarts
- Two-level volume declaration: `services.volumes` mounts it, top-level `volumes` registers it
- Always use `docker compose down -v` when you need a clean slate — `-v` removes the volume too

### pgvector
- `vector(512)` is a new Postgres column type from the pgvector extension — stores 512 floats
- Three distance operators: `<->` (L2), `<=>` (cosine), `<#>` (inner product)
- For text embeddings, always use cosine similarity (`<=>`)
- **ivfflat index** — clusters vectors into lists, requires ~1000 rows minimum to work. Returns empty results with few rows
- **hnsw index** — works correctly from row 1, faster queries, better accuracy. Preferred choice unless at very large scale
- When passing vectors from Python, use `pgvector.psycopg2.register_vector(conn)` + `numpy` arrays — plain strings don't work

### Python Concepts

**Dispatch table pattern** — store functions as dict values, look them up by key. Cleaner than long if/elif chains and easy to extend:
```python
LOADERS = {".pdf": _load_pdf, ".docx": _load_docx}
loader = LOADERS.get(extension)
loader(file_path)
```

**Private functions** — underscore prefix (`_function`) signals "internal use only" even outside classes. Convention, not enforcement.

**`__init__.py`** — empty file that tells Python to treat a folder as an importable package. Required for `from ingestion.loader import load_document` to work.

**`enumerate()`** — always yields `(index, value)`, index first:
```python
for index, value in enumerate(my_list):  # correct
for value, index in enumerate(my_list):  # wrong — swapped
```

**Parameterised queries** — never use f-strings for SQL. Always use `%s` placeholders:
```python
cursor.execute("INSERT INTO t (col) VALUES (%s)", (value,))
```

**`execute_values`** — bulk insert in psycopg2. One SQL round trip for all rows instead of one per row. Uses `VALUES %s` (no parentheses around `%s`).

**`RETURNING` clause** — get the auto-generated ID back immediately after insert:
```python
cursor.execute("INSERT INTO documents ... RETURNING document_id")
document_id = cursor.fetchone()[0]
```

**`try/except/finally` pattern** — always initialise `conn = None` before the try block so the `finally` clause can safely check `if conn:` even if the connection itself failed:
```python
conn = None
try:
    conn = psycopg2.connect(...)
except Exception as e:
    if conn: conn.rollback()
    raise
finally:
    if conn:
        cursor.close()
        conn.close()
```

### Chunking Strategy
- **Fixed size** — splits every N characters. Simple, cuts sentences mid-way
- **Recursive character splitting** — tries natural boundaries in order: `\n\n` → `\n` → `. ` → ` ` → character. LangChain's `RecursiveCharacterTextSplitter`
- **Semantic chunking** — splits where meaning changes (Phase 2)
- `CHUNK_SIZE = 512` characters, `CHUNK_OVERLAP = 50` characters
- Overlap ensures sentences spanning chunk boundaries aren't lost

### Embedding
- `embed_documents([...])` — batch embed multiple texts (ingestion)
- `embed_query("...")` — embed a single query string (retrieval)
- These are different methods because Voyage AI uses slightly different internal processing for each
- Voyage AI `voyage-3-lite` outputs 512-dimensional vectors
- API-based embedding keeps Docker images lean — no model weights bundled

### LangChain Package Structure (v1.x)
LangChain split into separate installable packages. Key imports:
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter  # NOT langchain.text_splitter
from langchain_core.messages import SystemMessage, HumanMessage       # NOT langchain.messages
from langchain_groq import ChatGroq
from langchain_voyageai import VoyageAIEmbeddings
```

### Prompt Engineering — Grounded Generation
Force the LLM to answer only from retrieved context to prevent hallucination:
```
System: Answer ONLY from the context below. If not in context, say you don't know.
Human:  Context: {chunks joined by ---}
        Question: {user query}
        Answer:
```

### Framework Decision — LangChain over LlamaIndex
Chosen because the learning journey goes Simple RAG → Advanced RAG → **Agentic RAG**. LangChain + LangGraph is the dominant stack for agents. LlamaIndex is stronger for pure document ingestion but weaker on the agent story.

---

## Local Development Setup

### Prerequisites
- Python 3.13
- Docker Desktop
- API keys: Groq, Voyage AI

### Environment Variables (`.env`)
```
GROQ_API_KEY=your_key_here
VOYAGE_API_KEY=your_key_here
POSTGRESQL_DB_PASSWORD=kragapplocal
```

### Start Local Database
```bash
docker compose up -d
```

### Apply Schema
```bash
docker exec -i kragapp-postgres-1 psql -U kragapp_admin -d kragapp_db < db/schema.sql
```

### Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate      # Mac/Linux
# source /venv/... won't work — leading slash makes it absolute path from root
pip install -r requirements.txt
```

### Run Tests
```bash
# Ingestion
python tests/test_ingestion.py

# Retrieval
python tests/test_retrieval.py
```

### Verify Data in Database
```bash
# Check documents
docker exec -it kragapp-postgres-1 psql -U kragapp_admin -d kragapp_db \
  -c "SELECT document_id, file_name, file_type, uploaded_at FROM documents;"

# Check chunks
docker exec -it kragapp-postgres-1 psql -U kragapp_admin -d kragapp_db \
  -c "SELECT id, document_id, chunk_index, left(chunk_text, 80) as preview FROM chunks;"
```

---

## Configuration Constants (`shared/config.py`)

| Constant | Value | Purpose |
|---|---|---|
| `GROQ_MODEL` | `llama-3.1-8b-instant` | Fast, stable, free tier |
| `CHUNK_SIZE` | `512` | Max characters per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `EMBEDDING_DIM` | `512` | Voyage-3-lite output dimensions |

---

## Bugs Fixed and Lessons

| Bug | Root Cause | Fix |
|---|---|---|
| `role "kgragapp_admin" does not exist` | Typo in compose file, baked into volume | `docker compose down -v` to wipe volume, fix typo, restart |
| `ModuleNotFoundError: langchain.text_splitter` | LangChain v1 split into sub-packages | Use `langchain_text_splitters` package |
| `ivfflat` index returning empty results | ivfflat needs ~1000 rows minimum | Switched to `hnsw` index |
| Vector search returning empty with `str(query_vector)` | psycopg2 doesn't know how to cast Python list to pgvector type | Use `pgvector.psycopg2.register_vector(conn)` + `np.array()` |
| `HumanMessage` receiving a tuple | Used `%s` string format instead of f-string for content | Use f-string: `f"Context: {text}"` |
| `from langchain.messages import ...` | Wrong package path in LangChain v1 | Use `langchain_core.messages` |

---

## Roadmap

### Phase 2 — Advanced RAG
- [ ] Query rewriting / HyDE (Hypothetical Document Embeddings)
- [ ] Re-ranking with cross-encoders
- [ ] Hybrid search (dense vectors + BM25 keyword search)
- [ ] Metadata filtering
- [ ] Multi-query retrieval
- [ ] Semantic chunking

### Phase 3 — Agentic RAG
- [ ] Retrieval as a tool
- [ ] ReAct agent pattern
- [ ] Multi-step reasoning
- [ ] LangGraph orchestration
- [ ] Memory (short-term + long-term)

### Phase 4 — LLMOps
- [ ] Dockerize both Lambda functions
- [ ] Push images to ECR
- [ ] Deploy to AWS Lambda
- [ ] Add API Gateway
- [ ] Tracing with LangSmith
- [ ] Evaluation with RAGAS
- [ ] CI/CD pipeline
- [ ] Cost and latency monitoring

---

## Next Steps (Immediate)

1. Dockerize `ingestion` and `retrieval` as Lambda container images
2. Push to ECR
3. Deploy and test via AWS Lambda console
4. Add VPC configuration for RDS access from Lambda
