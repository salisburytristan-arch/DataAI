# 🎯 ArcticCodex Studio - Command Cheat Sheet

## 🚀 START HERE

### Windows
```powershell
.\start_studio.ps1
```

### Linux/Mac
```bash
./start_studio.sh
```

### Then Open
```
http://localhost:8000
```

---

## 📋 All Commands (Quick Reference)

### Setup & Verification
```bash
python verify_studio_setup.py          # Check everything is ready
python seed_vault_quick.py             # Populate vault with documents
```

### Local Development
```bash
# Default (port 8000)
python -m packages.studio.src.studio_server_fly --host 0.0.0.0 --port 8000 --vault ./vault

# Custom port
python run_studio.py local --port 9000

# Without embeddings (faster)
python run_studio.py local --no-embeddings
```

### Fly.io Deployment
```bash
# One-command deploy
python run_studio.py fly

# Manual deploy
fly auth login    # First time only
fly deploy --dockerfile Dockerfile.fly-prod

# Monitor
fly logs -f       # Watch logs
fly open          # Open in browser
fly ssh console   # SSH into machine
```

### Testing
```bash
# Check if server is running
curl http://localhost:8000/api/health

# Get vault stats
curl http://localhost:8000/api/vault/stats

# Send a chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is ArcticCodex?", "convo_id": "test"}'
```

### Vault Operations
```bash
# Seed vault
python seed_vault_quick.py

# Check vault stats
python -c "from packages.vault.src.vault import Vault; print(Vault('./vault').get_stats())"

# Search vault
python -c "from packages.vault.src.vault import Vault; v = Vault('./vault'); print(v.search('query')[0])"
```

---

## 📁 Important Files

| File | What It Does |
|------|--------------|
| `start_studio.ps1` | Windows: Launch chat server + UI |
| `start_studio.sh` | Linux/Mac: Launch chat server + UI |
| `Dockerfile.fly-prod` | Production Docker image for Fly.io |
| `fly.toml` | Fly.io configuration |
| `packages/studio/src/studio_server_fly.py` | Chat API server |
| `packages/studio/web/app.js` | Browser chat interface |
| `seed_vault_quick.py` | Populate vault with documents |
| `verify_studio_setup.py` | Check setup is complete |

---

## 🌐 URLs

| Environment | URL | Purpose |
|-------------|-----|---------|
| Local | `http://localhost:8000` | Development |
| Local API | `http://localhost:8000/api/chat` | Chat API |
| Fly.io | `https://arcticcodex-studio.fly.dev` | Production |
| Fly Logs | `fly logs -f` | Live logs |

---

## 📊 System Stats

```
Model:           Mistral 7B (14GB VRAM)
Chunks:          230,000+
Total Tokens:    ~200 million
Memory (Fly):    16GB
CPU (Fly):       4 cores
Cost (Fly):      ~$0.25/hour
```

---

## 🔧 Environment Variables

```bash
AC_EMBEDDINGS=1                                   # Enable semantic search
AC_EMBEDDINGS_MODEL=sentence-transformers/all-MiniLM-L6-v2
PORT=8000                                         # Server port
PYTHONPATH=$(pwd)                                 # Python path
```

Disable embeddings for speed:
```bash
AC_EMBEDDINGS=0 python -m packages.studio.src.studio_server_fly --host 0.0.0.0 --port 8000 --vault ./vault
```

---

## 🆘 Quick Troubleshooting

| Problem | Command to Fix |
|---------|---|
| Port in use | `python run_studio.py local --port 9000` |
| Vault empty | `python seed_vault_quick.py` |
| Slow chat | Set `AC_EMBEDDINGS=0` |
| Fly deploy fails | `fly logs` to see error |
| Need to debug | `fly ssh console` |

---

## 📚 Documentation Files

| File | Content |
|------|---------|
| `START_HERE_CHAT.md` | **← Start here first** |
| `STUDIO_QUICK_START.md` | One-liner quick start |
| `STUDIO_DEPLOYMENT_GUIDE.md` | Detailed deployment guide |
| `SETUP_COMPLETE.md` | Full setup summary (this document category) |

---

## ✅ Checklist

- [ ] Read `START_HERE_CHAT.md`
- [ ] Run `python verify_studio_setup.py` 
- [ ] Run `.\start_studio.ps1` (or `./start_studio.sh`)
- [ ] Open http://localhost:8000
- [ ] Test chat: Type "Hello"
- [ ] Optional: Run `python seed_vault_quick.py`
- [ ] Optional: Deploy with `python run_studio.py fly`

---

## 🎓 Example Queries to Try

```
"What is ArcticCodex?"
"How do I use the chat system?"
"What documents are in the vault?"
"Show me a summary of the knowledge base"
"What features does the system have?"
```

---

## 💡 Pro Tips

1. **First launch slow?** - Embeddings download on first use (~100MB)
2. **Want faster search?** - Disable embeddings: `AC_EMBEDDINGS=0`
3. **Multiple users?** - Use different `convo_id` in chat API
4. **Cloud backup?** - Mount vault to cloud storage
5. **Custom styling?** - Edit `packages/studio/web/app.js`

---

**Status**: ✅ Ready to use  
**Next**: Run `.\start_studio.ps1`
