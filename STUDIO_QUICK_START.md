# ArcticCodex Studio - Quick Reference

## One-Liner Commands

### Local Development (Windows)
```powershell
.\start_studio.ps1
```

### Local Development (Linux/Mac)
```bash
./start_studio.sh
```

### Manual Start
```bash
python run_studio.py seed    # Optional: populate vault
python run_studio.py local   # Start on port 8000
```

### Deploy to Fly.io
```bash
fly auth login               # One time only
python run_studio.py fly     # Deploy
fly logs                      # Watch logs
fly open                      # Open in browser
```

## What It Does

✅ Runs full conversational chat with 230k+ documents  
✅ Streams responses token-by-token  
✅ Shows citations from source documents  
✅ Persists conversations  
✅ Works offline (Mistral 7B locally)  
✅ Deploys to Fly.io with 16GB RAM  

## URLs

| Local | Fly.io |
|-------|--------|
| `http://localhost:8000` | `https://arcticcodex-studio.fly.dev` |
| `http://localhost:8000/api/health` | (auto) |

## Key Files

| File | Purpose |
|------|---------|
| `run_studio.py` | Main launcher |
| `start_studio.ps1` | Windows startup |
| `start_studio.sh` | Linux/Mac startup |
| `Dockerfile.fly-prod` | Production image |
| `fly.toml` | Fly.io config |
| `packages/studio/src/studio_server_fly.py` | Chat server |
| `packages/studio/web/app.js` | Chat UI |

## Verify Setup

```bash
python verify_studio_setup.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | `python run_studio.py local --port 9000` |
| Vault empty | `python run_studio.py seed` |
| Embeddings slow | `python run_studio.py local --no-embeddings` |
| Fly deployment fails | `fly logs` to check errors |
| SSH into Fly machine | `fly ssh console` |

## Environment

Set before running:
```bash
export AC_EMBEDDINGS=1
export AC_EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
export PYTHONPATH=$(pwd)
```

## Next Steps

1. **Verify setup**: `python verify_studio_setup.py`
2. **Seed vault**: `python run_studio.py seed`
3. **Test locally**: `python run_studio.py local`
4. **Deploy**: `python run_studio.py fly`

---

**Status**: Ready to deploy  
**Model**: Mistral 7B  
**Chunks**: 230,000+  
**Hosting**: Fly.io (16GB/4CPU)
