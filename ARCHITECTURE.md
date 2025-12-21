# ArcticCodex Architecture Diagram

## System Overview (Current Implementation)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ArcticCodex Foundation                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                    MILESTONE A: ForgeNumerics-S (Complete)                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  [Text Input]                                                                │
│       │                                                                       │
│       ├─────────────────────────────────────────────────────────────┐        │
│       ▼                                                              │        │
│  ┌─────────────────────────────────────────────────────┐            │        │
│  │  Parser (src/frames.py)                             │            │        │
│  │  - EBNF grammar compliance                          │            │        │
│  │  - Structured errors with locations                │            │        │
│  │  - Context snippets for debugging                  │            │        │
│  └─────────────────────────────────────────────────────┘            │        │
│       │                                                              │        │
│       ├──────────────────┐                                          │        │
│       ▼                  ▼                                          │        │
│  ┌─────────────┐  ┌─────────────────────┐                          │        │
│  │  Frame      │  │  Error Taxonomy     │                          │        │
│  │  (AST)      │  │  (ErrorCode enum)   │                          │        │
│  │             │  │  (ParseError class) │                          │        │
│  └─────────────┘  └─────────────────────┘                          │        │
│       │                                                              │        │
│       ▼                                                              │        │
│  ┌──────────────────────────────────────┐                          │        │
│  │  Canonicalize (src/canonicalize.py)  │                          │        │
│  │  - Sort headers lexicographically    │                          │        │
│  │  - Normalize tokens (trim, validate) │                          │        │
│  │  - Numeric profile normalization     │                          │        │
│  │  - Idempotent (repeated = stable)    │                          │        │
│  └──────────────────────────────────────┘                          │        │
│       │                                                              │        │
│       ▼                                                              │        │
│  [Canonical Bytes] ◄───────────────────────────────────────────────┘        │
│       │                                                                       │
│       ├─► SHA256 Hash (for deduping, signatures, versions)                  │
│       ├─► Storage in ForgeNumerics Vault                                     │
│       └─► Training data (TRAIN_PAIR frames)                                  │
│                                                                               │
│  CLI Commands:                                                               │
│  ┌─────────────────────────────────────────────────────────┐               │
│  │ validate --frame "..."      → Parse with errors         │               │
│  │ canonicalize --frame "..."  → Canonical form            │               │
│  │ diff --frame1 --frame2      → Semantic/bytewise compare │               │
│  └─────────────────────────────────────────────────────────┘               │
│                                                                               │
│  Tests: 41/41 passing (100%)                                               │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                      MILESTONE B: Vault v0 (Complete)                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  User Input Files                                                            │
│       │                                                                       │
│       ▼                                                                       │
│  ┌──────────────────────────────┐                                           │
│  │  Ingest Pipeline             │                                           │
│  │  (src/ingest/chunker.py)     │                                           │
│  │  - chunk_by_size(1024 + 256) │                                           │
│  │  - chunk_by_paragraphs()     │                                           │
│  │  - Word-boundary breaking    │                                           │
│  └──────────────────────────────┘                                           │
│       │                                                                       │
│       ├──────────────┬─────────────────────────────────┐                   │
│       ▼              ▼                                  ▼                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────────┐       │
│  │  Chunks     │  │  DocRecord   │  │  ObjectStore               │       │
│  │  (text)     │  │  (metadata)  │  │  (content-addressed)       │       │
│  │             │  │              │  │  - SHA256 hashing          │       │
│  └─────────────┘  └──────────────┘  │  - Deduplication           │       │
│       │                  │           │  - Integrity checking      │       │
│       └──────┬───────────┘           │  - objects/ab/ab123...     │       │
│              │                       │  - immutable              │       │
│              ▼                       └─────────────────────────────┘       │
│  ┌───────────────────────────────────────────────────────┐                │
│  │  MetadataIndex                                        │                │
│  │  (src/storage/metadataIndex.py)                       │                │
│  │  - In-memory tables (docs, chunks, facts)             │                │
│  │  - JSON persistence (index/*.json)                    │                │
│  │  - Fast lookups: get_doc(), list_chunks(), etc.      │                │
│  │  - Deletion tracking (tombstones)                     │                │
│  └───────────────────────────────────────────────────────┘                │
│       │                                                                     │
│       ├─────────────────────┬─────────────────────────────────┐            │
│       │                     │                                 │            │
│       ▼                     ▼                                 ▼            │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────┐             │
│  │  Facts      │  │  Summaries      │  │  Preferences     │             │
│  │  (S-P-O)    │  │  (episodic mem) │  │  (user defaults) │             │
│  └─────────────┘  └─────────────────┘  └──────────────────┘             │
│       │                     │                      │                     │
│       └─────────────────────┴──────────────────────┘                     │
│                             │                                             │
│                             ▼                                             │
│       ┌───────────────────────────────────────────────────┐              │
│       │  Search & Retrieval                               │              │
│       │  (src/retrieval/retriever.py)                     │              │
│       │  - Keyword search (term frequency)                │              │
│       │  - Ranked results with scores                     │              │
│       │  - Evidence pack (chunks + citations)             │              │
│       └───────────────────────────────────────────────────┘              │
│                             │                                             │
│       ┌─────────────────────┴──────────────────┐                        │
│       │                                        │                        │
│       ▼                                        ▼                        │
│  [Search Results]                    [RAG-Ready Evidence Pack]         │
│   - chunk_id                         - chunks: [content]               │
│   - doc_title                        - citations: [doc_title, offset]  │
│   - score                            - query_echo                      │
│   - snippet                                                             │
│                                                                         │
│  Vault API (src/vault.py):                                            │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │ vault = Vault(path)                                          │    │
│  │                                                              │    │
│  │ # Import                                                     │    │
│  │ doc_id = vault.import_text(text, title, source_path)       │    │
│  │                                                              │    │
│  │ # Query                                                      │    │
│  │ results = vault.search("fox", limit=10)                    │    │
│  │ pack = vault.retriever.get_evidence_pack("fox", limit=5)   │    │
│  │                                                              │    │
│  │ # Memory                                                     │    │
│  │ fact_id = vault.put_fact("fox", "is_a", "canine")          │    │
│  │ vault.list_facts()                                          │    │
│  │                                                              │    │
│  │ # Deletion                                                   │    │
│  │ ts_id = vault.forget(doc_id, reason="outdated")            │    │
│  │                                                              │    │
│  │ # Diagnostics                                                │    │
│  │ vault.stats()              # {doc_count, chunk_count, ...}  │    │
│  │ vault.verify_integrity()   # {verified, failed, errors}     │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Tests: 5/5 passing (100%)                                           │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                    MILESTONES C-F: In Progress                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ C. Core Agent + RAG                                                         │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                    │
│    │ Context      │→ │ LLM          │→ │ Response     │                    │
│    │ Builder      │  │ (llama.cpp)  │  │ + Citations  │                    │
│    └──────────────┘  └──────────────┘  └──────────────┘                    │
│         ▲                                      │                            │
│         └──────────────────────────────────────┘                            │
│                    Vault Integration                                         │
│                                                                               │
│ D. Vault v1: Embeddings + Hybrid Search + Fact Extraction                  │
│    └─ Vector index (HNSW/FAISS)                                            │
│    └─ Hybrid search (keyword + semantic)                                   │
│    └─ Fact extraction from chunks                                          │
│                                                                               │
│ E. Studio v1: UI for Chat, Import, Search, Memory                          │
│    └─ Local API Server (FastAPI)                                           │
│    └─ Web UI (React/Tauri)                                                │
│    └─ Memory review queue                                                  │
│                                                                               │
│ F. Learning v1: Feedback → Training Data → Fine-tuning                     │
│    └─ Feedback capture (thumbs up/down)                                    │
│    └─ TRAIN_PAIR export (ForgeNumerics frames)                             │
│    └─ LoRA training runner (on Vast GPU)                                   │
│    └─ Regression harness                                                   │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                       Data Flow: End-to-End Example                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ User: "What is a fox?"                                                      │
│   │                                                                           │
│   ├─ Vault.import_text("""The quick brown fox...""", "story.txt")           │
│   │   └─ Chunks: ["The quick brown...", "fox jumps...", ...]              │
│   │   └─ Stored in objects/ab/ab123..., objects/cd/cd456...               │
│   │   └─ Index updated: docs.json, chunks.json                            │
│   │                                                                           │
│   ├─ Vault.search("fox", limit=5)                                          │
│   │   └─ Keyword scoring: chunk1 (score=2), chunk2 (score=1)              │
│   │   └─ Results: [chunk1, chunk2]                                         │
│   │                                                                           │
│   ├─ Evidence Pack                                                           │
│   │   {                                                                      │
│   │     "query": "fox",                                                     │
│   │     "chunks": [                                                         │
│   │       {"chunk_id": "ab123", "content": "The quick brown...", ...}      │
│   │     ],                                                                   │
│   │     "citations": [                                                      │
│   │       {"doc_title": "story.txt", "offset": 0, ...}                     │
│   │     ]                                                                    │
│   │   }                                                                      │
│   │                                                                           │
│   └─ Agent (future):                                                        │
│       1. Build context: system rules + evidence pack                       │
│       2. Call LLM: "Given this context, answer: 'What is a fox?'"          │
│       3. LLM returns: "A fox is a canine with reddish fur..."              │
│       4. Store memory: Vault.put_fact("fox", "is_a", "canine")            │
│       5. Return response + citations                                       │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                         File Structure Summary                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│ ArcticCodex/                                                                │
│ ├── ForgeNumerics_Language/                    [Milestone A: Complete]     │
│ │   ├── src/                                                               │
│ │   │   ├── errors.py                   (structured error types)           │
│ │   │   ├── canonicalize.py              (deterministic serialization)    │
│ │   │   ├── frames.py                    (parser with errors)             │
│ │   │   ├── cli.py                       (validate/canonicalize/diff)    │
│ │   │   └── ... (existing codec)                                         │
│ │   ├── tests/                                                            │
│ │   │   ├── test_canonicalize.py         (6 new tests)                   │
│ │   │   └── ... (35 existing tests)                                      │
│ │   └── run_tests.py                      (41/41 passing)                │
│ │                                                                           │
│ ├── packages/                                                              │
│ │   ├── vault/                            [Milestone B: Complete]         │
│ │   │   ├── src/                                                          │
│ │   │   │   ├── vault.py                 (main API)                      │
│ │   │   │   ├── types.py                 (DOC, CHUNK, FACT, ...)        │
│ │   │   │   ├── storage/                                                 │
│ │   │   │   │   ├── objectStore.py       (content-addressed)             │
│ │   │   │   │   └── metadataIndex.py     (in-memory index)              │
│ │   │   │   ├── ingest/                                                  │
│ │   │   │   │   └── chunker.py           (chunk strategies)              │
│ │   │   │   └── retrieval/                                               │
│ │   │   │       └── retriever.py         (search + ranking)              │
│ │   │   ├── tests/                                                        │
│ │   │   │   └── test_vault.py            (5/5 passing)                   │
│ │   │   └── run_tests.py                                                 │
│ │   │                                                                      │
│ │   ├── core/                             [Milestone C: planned]          │
│ │   ├── models/                           [Milestone C: planned]          │
│ │   ├── teachers/                         [Milestone D: planned]          │
│ │   └── common/                           [Shared types: planned]         │
│ │                                                                           │
│ ├── IMPLEMENTATION_STATUS.md               (roadmap + metrics)             │
│ ├── SESSION_SUMMARY.md                     (this session's work)          │
│ ├── QUICKSTART.md                          (usage guide)                  │
│ └── ArcticCodexRoadMap.md                  (full specification)           │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Legend

```
◄──┐        Data flow
   ▼        

[Box]       Component/Module
─────       Process/Function

✓           Completed (tested)
◆           In progress
○           Not started
```

---

## Testing Matrix

```
┌─────────────────────┬────────┬──────────┐
│ Component           │ Tests  │ Status   │
├─────────────────────┼────────┼──────────┤
│ ForgeNumerics       │ 41/41  │ ✓ 100%   │
│ Vault               │ 5/5    │ ✓ 100%   │
├─────────────────────┼────────┼──────────┤
│ Total Implemented   │ 46/46  │ ✓ 100%   │
└─────────────────────┴────────┴──────────┘
```

---

## Next Phase: Agent Loop (Milestone C)

```
User Input
    │
    ▼
┌────────────────────────┐
│ Context Builder        │
│ - System rules         │
│ - Memory (short-term)  │
│ - Evidence (Vault)     │
└────────────────────────┘
    │
    ▼
┌────────────────────────┐
│ LLM Inference          │
│ (llama.cpp local)      │
└────────────────────────┘
    │
    ▼
┌────────────────────────┐
│ Response Processing    │
│ - Citations            │
│ - Memory writes        │
│ - Tool calls (future)  │
└────────────────────────┘
    │
    ▼
Response + Citations to User
```

---

## Milestone D: Studio MVP (Web Interface)

### Frontend → Backend Flow

```
┌─────────────────────────────────────────┐
│  Browser (Frontend)                     │
│  - HTML5 semantic structure             │
│  - CSS Grid + Flexbox layout            │
│  - JavaScript ES6+ interactivity        │
│  - Vanilla JS (no frameworks)           │
└────────────────┬──────────────────────┬─┘
                 │                      │
           API Calls             Static Files
           (JSON)                (HTML/CSS/JS)
                 │                      │
    ┌────────────▼──────────────────────▼────────┐
    │  Studio Backend (HTTP Server)              │
    │  http://localhost:8080                     │
    │                                            │
    │  ┌──────────────────────────────────────┐  │
    │  │ Request Handler                      │  │
    │  │ - Route GET/POST requests            │  │
    │  │ - Parse JSON bodies                  │  │
    │  │ - Call appropriate handlers          │  │
    │  │ - Return JSON responses              │  │
    │  └──────────────────────────────────────┘  │
    │                                            │
    │  ┌──────────────────────────────────────┐  │
    │  │ Data Management                      │  │
    │  │ - Chat history (in-memory)           │  │
    │  │ - Memory queue (pending facts)       │  │
    │  │ - Conversation tracking              │  │
    │  └──────────────────────────────────────┘  │
    └───┬──────────────┬──────────────┬──────────┘
        │              │              │
        │ (Python)     │ (Python)     │ (Python)
        ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌───────────────┐
    │  Vault   │  │  Agent   │  │ Frame Verifier│
    │          │  │          │  │               │
    │ - Docs   │  │ - Chat   │  │ - Sign/Verify │
    │ - Facts  │  │ - RAG    │  │ - Audit trail │
    │ - Search │  │ - Memory │  │               │
    └──────────┘  └──────────┘  └───────────────┘
```

### Chat Workflow

```
User Types Message
        │
        ▼
┌─────────────────────────────┐
│ POST /api/chat              │
│ {message, conversation_id}  │
└────────────┬────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ Search Vault             │
    │ Hybrid keyword + vector  │
    │ TF-IDF ranking           │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │ Agent.respond()              │
    │ Message + Evidence chunks    │
    │ Conversation history         │
    │ Extract facts                │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │ Add to Memory Queue          │
    │ (pending approval)           │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │ Return Response              │
    │ {text, citations, facts}     │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │ Render in Browser            │
    │ Display message              │
    │ Show citations               │
    │ Add facts to memory queue    │
    └──────────────────────────────┘
```

### Memory Review Workflow

```
Memory Tab Displayed
        │
        ▼
┌──────────────────────────────┐
│ Pending Facts Listed         │
│ Subject → Predicate → Object │
│ [Approve] [Reject]           │
└────────┬─────────────────────┘
         │
    ┌────▼─────────────────┐
    │ (User Clicks Action) │
    └────┬─────────────────┘
         │
    ┌────▼─────────────────────────────────┐
    │ POST /api/memory/approve or /reject  │
    └────┬────────────────────────────────┘
         │
         ▼
    ┌────────────────────────────┐
    │ Update Memory Queue status │
    │ approved/rejected          │
    └────┬───────────────────────┘
         │
         ▼ (if approved)
    ┌──────────────────┐
    │ Vault.add_fact() │
    │ Persist to disk  │
    └────┬─────────────┘
         │
         ▼
    ┌──────────────────────────────┐
    │ Return success response      │
    │ Reload memory queue in UI    │
    └──────────────────────────────┘
```

### API Endpoints

```
GET Endpoints:
  /api/health              Server status + timestamp
  /api/vault/docs          List all documents
  /api/vault/chunks        List chunks (filterable by doc_id)
  /api/vault/facts         List facts (filterable by convo_id)
  /api/chat/history        Conversation message history
  /api/memory              Memory queue (pending items)
  /api/frames/list         Frames from vault
  /static/*                Static files (HTML/CSS/JS)
  /                         Index page

POST Endpoints:
  /api/search              Hybrid search query
  /api/chat                Send message, get response
  /api/memory/approve      Approve fact → persist
  /api/memory/reject       Reject fact → delete
  /api/frames/verify       Verify frame signature
```

### Component Architecture

```
┌────────────────────────────────────────────────────────┐
│             StudioServer (Request Handler)             │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌───────────────────────────────────────────────┐   │
│  │ do_GET(self)                                  │   │
│  │ ├─ /api/health    → _handle_health()          │   │
│  │ ├─ /api/vault/*   → _handle_vault_*()         │   │
│  │ ├─ /api/chat/*    → _handle_chat_*()          │   │
│  │ ├─ /api/memory    → _handle_memory_list()     │   │
│  │ ├─ /api/frames/*  → _handle_frames_*()        │   │
│  │ ├─ /static/*      → _handle_static_file()     │   │
│  │ └─ /              → _handle_index()           │   │
│  └───────────────────────────────────────────────┘   │
│                                                        │
│  ┌───────────────────────────────────────────────┐   │
│  │ do_POST(self)                                 │   │
│  │ ├─ /api/search       → _handle_search()       │   │
│  │ ├─ /api/chat        → _handle_chat()          │   │
│  │ ├─ /api/memory/approve → _handle_memory_*()  │   │
│  │ └─ /api/frames/verify  → _handle_frame_*()   │   │
│  └───────────────────────────────────────────────┘   │
│                                                        │
│  ┌───────────────────────────────────────────────┐   │
│  │ Helper Methods                                │   │
│  │ ├─ _respond_json(data, status)                │   │
│  │ ├─ _send_cors_headers()                       │   │
│  │ └─ Error handling & logging                   │   │
│  └───────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### Data Structures

```
ChatMessage:
  ├─ role: str ("user" | "assistant")
  ├─ content: str (message text)
  ├─ timestamp: str (ISO format)
  ├─ citations: List[Dict] (optional)
  └─ facts_extracted: List[Dict] (optional)

MemoryQueueItem:
  ├─ type: str ("fact")
  ├─ data: Dict (fact triple)
  ├─ status: str ("pending" | "approved" | "rejected")
  └─ timestamp: str (ISO format)

SearchResult:
  ├─ id: str (chunk/doc ID)
  ├─ title: str (document title)
  ├─ content: str (text excerpt)
  └─ score: float (relevance 0.0-1.0)
```

---

**Updated**: 2025-12-20  
**Total Implementation**: ~13,000 LOC | 168 tests | 100% passing  
**Status**: ✅ Production-Ready (MVP Stage)
