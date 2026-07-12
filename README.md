---
title: Ask My Docs
emoji: 📄
colorFrom: indigo
colorTo: slate
sdk: docker
pinned: false
license: mit
---

# Ask My Docs — Production-Grade RAG System

A domain-specific document Q&A system with:

- **Hybrid retrieval**: BM25 (lexical) + dense vector search (semantic), fused with
  Reciprocal Rank Fusion (RRF).
- **Cross-encoder re-ranking**: a `sentence-transformers` cross-encoder re-scores the
  fused candidate list for precision before generation.
- **Citation enforcement**: every generated answer must cite `[chunk_id]` markers that
  are validated against the retrieved evidence set. Unsupported sentences are flagged
  or stripped, and the API refuses to answer if evidence is insufficient.
- **CI-gated evaluation**: a `ragas`-based evaluation suite (faithfulness, answer
  relevancy, context precision/recall) runs in GitHub Actions and **fails the build**
  if scores drop below configured thresholds.

## Architecture

```
                 ┌─────────────┐
   documents ──► │  Ingestion  │  loader → chunker → embed → index (BM25 + FAISS)
                 └─────┬───────┘
                       │
                       ▼
                 ┌─────────────┐        ┌──────────────┐
   query ──────► │   Hybrid    │──RRF──►│ Cross-Encoder │──► top-k evidence
                 │  Retriever  │        │   Re-ranker   │
                 └─────────────┘        └──────┬───────┘
                                               │
                                               ▼
                                       ┌───────────────┐
                                       │  Extractive   │
                                       │  Generator +  │──► grounded answer
                                       │   Citation    │      + citations
                                       │  Enforcement  │
                                       └───────────────┘
```

The generator is **extractive** — it constructs answers directly from retrieved evidence
snippets without calling an LLM. This means answers are always grounded, never
hallucinate, and run without any API keys.

## Sample corpus

`data/raw/` ships with a small, coherent doc set for a fictional SaaS product
("CloudNest") spanning every supported format, so the system is queryable
out of the box:

| File | Format | Content |
|---|---|---|
| `cloudnest_sla.pdf` | PDF | Uptime commitment, support response times, downtime credits, refund policy |
| `cloudnest_onboarding_guide.docx` | DOCX | Setup steps, team invite limits, integration setup times |
| `cloudnest_api_reference.html` | HTML | Auth, rate limits, endpoints, error codes |
| `cloudnest_pricing_tiers.csv` | CSV | Plan pricing, storage, user limits, support level |
| `cloudnest_faq.md` | Markdown | Password reset, cancellation, file limits, discounts |

`eval/testset/sample_qa.json` contains 15 question/ground-truth pairs written
against this exact content — replace both the corpus and the test set with your
own domain's documents when you're ready to move past the demo.

## Query logging (PostgreSQL)

Every `POST /query` request is optionally logged to Postgres: the question, every
retrieved chunk (id, doc, score, text), the final grounded answer, the citation-enforcement
verdict, and end-to-end latency in milliseconds.

```
src/db/
├── models.py       # QueryLog SQLAlchemy model
├── session.py       # engine/session management, init_db()
└── repository.py    # log_query() — never raises; DB outages don't break requests
```

Start Postgres via `docker compose up postgres` (or run the full stack with
`docker compose up`, which wires the API to the `postgres` service by container
name). Locally without Docker, point `DATABASE_URL` at any reachable Postgres
instance, or use `sqlite:///./local.db` for a zero-setup local run — the same
code path works against both since it's plain SQLAlchemy. On Hugging Face Spaces
(where no Postgres is available), leave `DATABASE_URL` empty to disable logging.

Logging is best-effort: if the database is unreachable, `log_query()` logs a
server-side warning and returns `None` rather than failing the request. Set
`LOG_QUERIES=false` to disable logging entirely.

```bash
# inspect logged queries
psql postgresql://raguser:ragpass@localhost:5432/askmydocs \
  -c "SELECT question, is_fully_grounded, latency_ms, created_at FROM query_logs ORDER BY created_at DESC LIMIT 10;"
```

`init_db()` uses `create_all()` for simplicity — fine for a demo/small
deployment. For anything beyond that, swap in Alembic migrations.

## Frontend (Next.js)

`frontend/` is a Next.js 15 App Router UI for the API — ask a question, get a
grounded answer with clickable citation tabs that scroll to and highlight the
matching evidence chunk in a side drawer.

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev          # http://localhost:3000
```

Or run the whole stack (Postgres + API + frontend) together:

```bash
cp .env.example .env   # if you haven't already
docker compose up --build
# App: http://localhost:7860  (FastAPI :8001 is internal, proxied via Next.js)
```

The frontend image uses Next's `output: "standalone"` build (`next.config.mjs`),
which traces only the files actually needed at runtime — the production image
ships a ~59MB `node_modules` instead of the full ~366MB dev tree. CI
(`.github/workflows/ci.yml`, `frontend` job) runs `npm ci` + `npm run build` on
every PR, so a TypeScript or build-breaking change in the frontend fails CI
the same way a failing pytest or Ragas threshold does on the backend.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 1. Put your source documents (pdf/docx/html/csv/md/txt) into data/raw/
# 2. Build the hybrid index
python scripts/ingest_docs.py --input data/raw --output storage

# 3. Ask a question
python scripts/run_query.py "What does the refund policy say about digital goods?"

# 4. Or run the API
uvicorn src.api.main:app --reload --port 8001

# 5. Run the CI-gated eval suite locally
python eval/run_ragas_eval.py
```

## Hugging Face Spaces

This project is designed for one-click deployment on Hugging Face Docker Spaces.

1. Create a new Space with the **Docker** SDK
2. Push this repository to the Space
3. The Space will build the Dockerfile automatically
4. Pre-built indexes are baked into the image — the app is queryable immediately
5. Optionally set `DATABASE_URL` in Space secrets to enable query logging

The container runs both FastAPI (port 8001) and Next.js (port 7860) via
supervisord. HF Spaces routes traffic to port 7860; Next.js proxies `/api/*`
requests to the FastAPI backend on port 8001.

## Why hybrid retrieval?

- **BM25** wins on exact terms: product codes, error codes, proper nouns, numbers.
- **Vector search** wins on paraphrase and semantic similarity ("cancel my plan" ↔
  "terminate subscription").
- Fusing both (RRF) and then re-ranking with a cross-encoder (which scores the
  *actual* query-passage pair jointly, unlike bi-encoders which embed independently)
  gives materially better top-k precision than either method alone.

## Citation enforcement, concretely

1. Each retrieved chunk gets a stable `chunk_id` (e.g. `s0001`).
2. The generator produces an answer that cites the `chunk_id` inline after every
   factual sentence, e.g. `Refunds are issued within 14 days [s0002].`
3. `CitationEnforcer` parses the answer, extracts citation tags, and verifies:
   - every cited `chunk_id` actually exists in the retrieved evidence set (no
     hallucinated citations),
   - every sentence that makes a factual claim carries at least one citation,
   - (optional, `strict` mode) an NLI/entailment check that the cited chunk actually
     supports the sentence.
4. Sentences that fail verification are either removed or the whole answer is
   downgraded to "insufficient evidence," depending on configured policy.

## CI gate

`.github/workflows/ci.yml` runs unit tests, then `eval/run_ragas_eval.py` against a
fixed regression test set (`eval/testset/sample_qa.json`). The job exits non-zero
(failing the PR check) if any of:

- `faithfulness < 0.85`
- `answer_relevancy < 0.80`
- `context_precision < 0.75`
- `context_recall < 0.75`

Thresholds live in `eval/run_ragas_eval.py` — tune them to your domain.
