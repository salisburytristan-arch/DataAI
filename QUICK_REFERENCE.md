# ArcticCodex Quick Reference

## Running Tests

```powershell
# All ForgeNumerics tests
cd ForgeNumerics_Language
python run_tests.py

# All Vault tests
cd packages/vault
python run_tests.py

# All Core tests (Agent, Teachers, etc)
cd packages/core
python run_tests.py

# Studio tests
cd packages/studio
python -m unittest tests.test_studio_server -v

# All tests at once (from root)
cd <root>
python -c "import subprocess; [subprocess.run(['python', p]) for p in ['ForgeNumerics_Language/run_tests.py', 'packages/vault/run_tests.py', 'packages/core/run_tests.py']]"
```

## Running Studio

### Quick Launch
```bash
python launch_studio.py --open
```

### With Options
```bash
# Custom port
python launch_studio.py --port 9000

# Custom vault
python launch_studio.py --vault /path/to/vault

# Custom conversation ID
python launch_studio.py --convo my-session
```

### Programmatic Launch
```python
from packages.studio.src.studio_server import start_studio
from packages.vault.src.vault import Vault

vault = Vault()
start_studio(vault=vault, port=8080, threaded=True)
```

## Using the Agent

### Chat Mode
```bash
python -m packages.core.src.cli chat --vault ./vault --persist --convo session-1
```

### Export to ForgeNumerics
```bash
python -m packages.core.src.cli export-fn --vault ./vault --convo session-1 --out ./facts.fn.jsonl
```

### Import ForgeNumerics Frames
```bash
python -m packages.core.src.cli import-fn --vault ./vault --file ./facts.fn.jsonl
```

## Using the Vault

### Python API
```python
from packages.vault.src.vault import Vault

vault = Vault(data_dir="./vault")

# List documents
docs = vault.list_docs()

# List facts
facts = vault.list_facts(metadata_filter={"convo_id": "session-1"})

# Search
results = vault.search("keyword")

# Add document
vault.add_document(title="Doc", content="...", doc_id="doc-1")

# Extract and add fact
vault.add_fact(subject="X", predicate="is", object="Y", convo_id="session-1")
```

## Using Frame Verification

### Sign Frames
```python
from packages.core.src.frame_verifier import FrameVerifier

verifier = FrameVerifier(private_key=b"secret", signer_id="agent-1")
signed_frame = verifier.sign_frame(frame_string)
```

### Verify Frames
```python
result = verifier.verify_frame(signed_frame, b"secret")
if result.verified:
    print(f"Signed by: {result.signer_id}")
    print(f"Timestamp: {result.timestamp}")
```

## Using Teacher System

### DeepSeek Client
```python
from packages.core.src.teacher_client import DeepSeekClient

client = DeepSeekClient(api_key="sk-xxx")
response = client.verify("statement", "evidence")
print(f"Verified: {response.score}")
```

### Vast.ai Provisioning
```python
from packages.core.src.vast_provisioner import VastProvisioner

provisioner = VastProvisioner(api_key="xxx")
search = provisioner.search(min_vram=16, max_price=1.0)
instance = provisioner.provision(search[0])
print(f"Connected at {instance.ssh_host}:{instance.ssh_port}")
```

### Distillation Writer
```python
from packages.core.src.distillation_writer import DistillationDatasetWriter

writer = DistillationDatasetWriter()
writer.add_pair(instruction="Q", completion="A", teacher_feedback="Good", score=0.95)
writer.export("training_pairs.jsonl")
```

## File Locations

```
d:\ArcticCodex - AGI\
├── ForgeNumerics_Language/       - Trinary codec and EBNF grammar
├── packages/
│   ├── vault/                    - Document storage and indexing
│   ├── core/                     - Agent, teachers, fact extraction
│   └── studio/                   - Web interface
└── launch_studio.py              - Quick launcher
```

## API Endpoints

### Studio Server (http://localhost:8080)

```
GET  /                      - Serve index.html
GET  /api/health            - Server status
GET  /api/vault/docs        - List documents
GET  /api/vault/chunks      - List chunks
GET  /api/vault/facts       - List facts
GET  /api/chat/history      - Chat history
GET  /api/memory            - Memory queue
GET  /api/frames/list       - List frames
GET  /static/*              - Static files

POST /api/search            - Search query
POST /api/chat              - Send message
POST /api/memory/approve    - Approve fact
POST /api/memory/reject     - Reject fact
POST /api/frames/verify     - Verify signature
```

## Test Commands

```powershell
# Studio tests only
python -m unittest packages.studio.tests.test_studio_server -v

# Run specific test class
python -m unittest packages.studio.tests.test_studio_server.TestChatMessage -v

# Run specific test
python -m unittest packages.studio.tests.test_studio_server.TestChatMessage.test_create_message -v

# Run all tests with discovery
python -m unittest discover -s packages -p "test_*.py" -v
```

## Key Classes

### Vault
```python
from packages.vault.src.vault import Vault
vault = Vault(data_dir="./vault")
```

### Agent
```python
from packages.core.src.agent import Agent
agent = Agent(vault=vault, llm=http_client)
response = agent.respond(message, evidence_limit=5)
```

### Studio Server
```python
from packages.studio.src.studio_server import start_studio
start_studio(vault=vault, agent=agent, port=8080)
```

### Frame Verifier
```python
from packages.core.src.frame_verifier import FrameVerifier
verifier = FrameVerifier(private_key=b"secret", signer_id="id")
```

## Common Issues

### Vault not found
```
ERROR: Vault not found at ./vault
SOLUTION: Create vault directory or use --vault option
```

### Port already in use
```
ERROR: Address already in use
SOLUTION: Use different port: python launch_studio.py --port 9000
```

### Agent timeout
```
ERROR: LLM client timeout
SOLUTION: Check LLM service is running, increase timeout
```

## Performance Tips

1. **Cache searches**: Results are not cached, add Redis for production
2. **Index facts**: Use metadata filters to narrow down queries
3. **Batch imports**: Import multiple documents at once
4. **Archive old facts**: Move old conversations to separate vault
5. **Monitor memory**: Watch memory growth on long-running agents

## Debugging

### Enable logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test API endpoint
```bash
curl http://localhost:8080/api/health | python -m json.tool
```

### Check vault contents
```bash
ls -la vault/objects/
cat vault/index/documents.json
```

### Browser DevTools
1. Press F12
2. Network tab shows API requests
3. Console shows JavaScript errors
4. Debugger tab for stepping through code

## Resources

- [Main README](README.md)
- [Studio README](packages/studio/README.md)
- [Vault README](packages/vault/README.md)
- [Core README](packages/core/README.md)
- [ForgeNumerics README](ForgeNumerics_Language/README.md)

## Quick Links

- **Vault Explorer**: http://localhost:8080
- **API Health**: http://localhost:8080/api/health
- **Search Results**: Use right panel in Studio UI

## Next Steps

1. Load documents into vault
2. Start agent conversations
3. Review and approve extracted facts
4. Export training data for fine-tuning
5. Add your own tools and extensions

---

**Version**: 1.0  
**Last Updated**: 2025-12-20
