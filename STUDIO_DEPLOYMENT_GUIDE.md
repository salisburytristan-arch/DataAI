# ArcticCodex Studio - Full Conversational Deployment

Complete setup for running a conversational chat system with 230k+ document chunks, real-time streaming, and citations.

## Architecture

- **Frontend**: Chat UI (browser-based) at `/`
- **Backend**: Python Studio Server handling vault + LLM inference
- **Vault**: 230k+ chunked documents with semantic search
- **Streaming**: SSE (Server-Sent Events) for token-by-token responses
- **Citations**: Automatic source attribution from vault

## Quick Start (Local)

### Windows (PowerShell)
```powershell
# Run the startup script
.\start_studio.ps1

# Or manually:
python run_studio.py seed      # Optional: seed vault first
python run_studio.py local --port 8000
```

### Linux/Mac (Bash)
```bash
# Make startup script executable
chmod +x start_studio.sh

# Run it
./start_studio.sh

# Or manually:
python run_studio.py seed      # Optional: seed vault first
python run_studio.py local --port 8000
```

### Access
Open browser to **http://localhost:8000**

## Vault Seeding

To populate the vault with your documents:

```bash
python run_studio.py seed --vault ./vault
```

This searches:
- `./docs` - Documentation
- `./KnowledgeTXT` - Knowledge base
- `./training_data` - Training materials

Supported formats: `.md`, `.txt`, `.jsonl`

## API Endpoints

### Health Check
```
GET /api/health
```
Response: `{"status": "healthy", "timestamp": "2026-01-01T..."}`

### Search
```
POST /api/chat
{
  "message": "What is ArcticCodex?",
  "convo_id": "session-1"
}
```

### Streaming Chat
```
GET /api/chat/stream?message=...&convo_id=...
```
Response: Server-Sent Events stream with tokens

## Deployment to Fly.io

### Prerequisites
1. Install Fly.io CLI: https://fly.io/docs/hands-on/install-flyctl/
2. Create Fly account and login: `fly auth login`

### Deploy
```bash
# Deploy with Dockerfile.fly-prod
python run_studio.py fly

# Or manually:
fly deploy --dockerfile Dockerfile.fly-prod

# Monitor deployment
fly logs

# Open in browser
fly open
```

### Fly Configuration

The `fly.toml` includes:
- **16GB RAM, 4 CPU cores** - Handles 7B Mistral model + 230k embeddings
- **Persistent volumes**:
  - `/app/vault` - Document storage
  - `/app/models` - LLM models
- **Health checks** - Auto-restarts on failure
- **SSE support** - Streaming responses

### Seed Vault on Fly
```bash
fly ssh console
cd /app
python run_studio.py seed --vault /app/vault
exit
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `AC_EMBEDDINGS` | 1 | Enable semantic search (0/1) |
| `AC_EMBEDDINGS_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `AC_LLM_ENDPOINT` | (none) | Optional remote LLM endpoint |
| `PORT` | 8000 | Server port |
| `VAULT_PATH` | `./vault` | Vault directory |

## Chat Features

### User Experience
- **Real-time streaming** - Watch tokens appear as they're generated
- **Citations** - Click sources to see where answers came from
- **Conversation history** - Persistent message history
- **Session tracking** - Unique session IDs for multi-user support

### Backend
- **Deterministic chunks** - SHA256 content-addressed for consistency
- **Hybrid search** - TF-IDF + embeddings for best results
- **Context windows** - Automatic retrieval of relevant documents
- **Fact extraction** - Optional: extract and persist facts from responses

## Architecture Details

### Request Flow
```
Browser Chat UI
    ↓
POST /api/chat
    ↓
Studio Server
    ├─ Vault Search (TF-IDF + embeddings)
    ├─ Evidence Retrieval
    └─ Agent Response with LLM
    ↓
SSE Stream (tokens + citations)
    ↓
Browser displays response
```

### Vault Structure
```
vault/
├── index/
│   ├── docs.jsonl          # Document metadata
│   ├── chunks.jsonl        # Chunk metadata + offsets
│   ├── embeddings/         # Vector index
│   └── facts.jsonl         # Extracted facts
├── objects/                # Content-addressed storage
│   └── <sha256>/           # Document objects by hash
└── cache/                  # Temporary files
```

## Troubleshooting

### "Vault is empty"
Seed the vault:
```bash
python run_studio.py seed
```

### "Connection refused" to LLM
If using remote LLM, set environment variable:
```bash
export AC_LLM_ENDPOINT=http://your-llm-server:8000
```

### Embeddings not working
Check installation:
```bash
python -c "import sentence_transformers; print('OK')"
```

If missing, install:
```bash
pip install sentence-transformers
```

### High memory usage
Disable embeddings for faster responses (less accurate search):
```bash
python run_studio.py local --no-embeddings
```

## Performance Notes

- **230k chunks** = ~200M tokens total
- **Mistral 7B** requires ~14GB VRAM (on Fly 16GB machine: safe)
- **Search latency**: 50-200ms (TF-IDF), 200-500ms (with embeddings)
- **Generation speed**: ~20 tokens/sec on Fly machine

## Development

### Run Tests
```bash
python -m pytest packages/vault/tests/
python -m pytest packages/core/tests/
```

### Check Vault Health
```bash
python -c "from packages.vault.src.vault import Vault; v = Vault('./vault'); print(v.get_stats())"
```

### View Chunk Details
```bash
python -c "from packages.vault.src.vault import Vault; v = Vault('./vault'); chunks = v.search('your query'); print(chunks[0]['text'])"
```

## File Structure

```
.
├── Dockerfile.fly-prod           # Production Docker image
├── fly.toml                      # Fly.io configuration
├── start_studio.ps1              # Windows startup script
├── start_studio.sh               # Linux/Mac startup script
├── run_studio.py                 # Studio launcher
├── packages/
│   ├── studio/
│   │   ├── src/
│   │   │   ├── studio_server.py          # Development server
│   │   │   └── studio_server_fly.py      # Production server
│   │   ├── web/
│   │   │   ├── app.js                    # Chat UI
│   │   │   └── index.html                # HTML template
│   │   └── scripts/
│   ├── vault/
│   │   └── src/vault.py          # Core vault implementation
│   └── core/
│       └── src/agent.py          # LLM agent + retrieval
├── vault/                        # Document storage (created at runtime)
└── docs/, KnowledgeTXT/          # Source documents
```

## Next Steps

1. **Seed vault**: `python run_studio.py seed`
2. **Test locally**: `python run_studio.py local`
3. **Deploy to Fly**: `python run_studio.py fly`
4. **Monitor**: `fly logs` and `fly ssh console`
5. **Customize**: Modify `packages/studio/src/studio_server_fly.py` as needed

## Support

For issues:
1. Check logs: `fly logs`
2. SSH into machine: `fly ssh console`
3. Check vault health: `vault/index/stats.json`
4. Review citations in browser console

---

**Status**: ✅ Ready for production
**Model**: Mistral 7B Instruct
**Chunks**: 230,000+
**Embeddings**: Enabled (hybrid search)
