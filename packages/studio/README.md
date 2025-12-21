# ArcticCodex Studio MVP

A web-based user interface for interacting with the ArcticCodex knowledge management system.

## Features

- **Chat Interface**: Natural language interaction with the ArcticCodex agent
- **Citation Management**: View and explore sources for generated responses
- **Vault Explorer**: Browse documents, extracted facts, and memory queue
- **Hybrid Search**: Search across your knowledge base with keyword + vector ranking
- **Memory Review**: Human-in-the-loop fact approval and rejection
- **Frame Verification**: Inspect and verify cryptographically signed frames

## Architecture

### Backend (`src/studio_server.py`)

HTTP server providing REST API endpoints for all Studio operations:

```python
from packages.studio.src.studio_server import start_studio
from packages.vault.src.vault import Vault
from packages.core.src.agent import Agent

vault = Vault()
agent = Agent(vault=vault, llm=http_client)

# Start Studio on port 8080
start_studio(vault=vault, agent=agent, convo_id="session-1", port=8080)

# Open http://localhost:8080 in browser
```

### Frontend (`web/`)

- `index.html` - Main page structure with semantic HTML5
- `style.css` - Styling and responsive layout (400+ lines)
- `app.js` - Client-side JavaScript for interactivity (600+ lines)

## API Endpoints

### GET Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/health` | Server status and timestamp |
| `/api/vault/docs` | List all documents in vault |
| `/api/vault/chunks` | List chunks (filterable by document) |
| `/api/vault/facts` | List extracted facts (filterable by conversation) |
| `/api/chat/history` | Get current conversation history |
| `/api/memory` | List memory queue items (pending approvals) |
| `/api/frames/list` | List frames from vault |
| `/static/*` | Serve static files (HTML/CSS/JS) with security checks |
| `/` | Serve index.html |

### POST Endpoints

| Endpoint | Description | Payload |
|----------|-------------|---------|
| `/api/search` | Hybrid search | `{"query": "search text"}` |
| `/api/chat` | Send message and get response | `{"message": "text", "conversation_id": "id"}` |
| `/api/memory/approve` | Approve a memory item | `{"fact_id": "id"}` |
| `/api/memory/reject` | Reject a memory item | `{"fact_id": "id"}` |
| `/api/frames/verify` | Verify frame signature | `{"frame_id": "id", "signature": "hex"}` |

All responses are JSON.

## UI Components

### Header
- ArcticCodex logo with frame marker (⧈)
- Current conversation ID display
- Real-time server status indicator

### Sidebar (Vault Explorer)
Three tabbed sections:
1. **Documents** - Browse loaded documents with chunk count and size
2. **Facts** - View extracted facts with subject/predicate/object
3. **Memory** - Review pending facts awaiting approval/rejection

### Main Chat Area
- Welcome message (on first load)
- Chat history with alternating user/assistant messages
- Citation links inline with responses
- Auto-scroll to latest message
- Textarea input with Send button
- Keyboard shortcut: Shift+Enter for newline, Enter to send

### Right Panel (Search)
- Text input for search queries
- Real-time results display with relevance scores
- Click results to view details in modal

### Modals
- **Document Details**: Show metadata, chunk count, file size, ID
- **Citation Details**: Source information and context

## Installation & Usage

### Prerequisites
- Python 3.12+
- Vault instance (with documents loaded)
- Agent instance (with LLM client configured)

### Start Server

```bash
cd packages/studio

python -m studio_server --vault vault_instance --agent agent_instance --port 8080
```

Or programmatically:

```python
from packages.studio.src.studio_server import start_studio

start_studio(
    vault=vault_instance,
    agent=agent_instance,
    convo_id="session-1",
    port=8080,
    threaded=True  # Run in background
)
```

Then open http://localhost:8080 in your browser.

### Configuration

The server automatically:
1. Detects the `web/` directory for static files
2. Tracks conversation ID for fact filtering
3. Manages chat history and memory queue in memory
4. Provides CORS headers for browser access

## Testing

Run all tests:
```bash
python -m unittest packages.studio.tests.test_studio_server -v
```

Test coverage:
- **29 tests** covering:
  - ChatMessage dataclass
  - Server initialization
  - API endpoint logic
  - Search functionality
  - Chat flows
  - Frame verification
  - Integration tests (complete chat workflow + memory management)

## File Structure

```
packages/studio/
├── __init__.py
├── src/
│   ├── __init__.py
│   └── studio_server.py     (550+ LOC, HTTP server + endpoints)
├── web/
│   ├── index.html           (350+ LOC, HTML structure)
│   ├── style.css            (400+ LOC, responsive styling)
│   └── app.js               (600+ LOC, client-side logic)
├── tests/
│   ├── __init__.py
│   └── test_studio_server.py (500+ LOC, 29 tests)
└── README.md                (this file)
```

## Browser Compatibility

Tested and working on:
- Chrome/Chromium 120+
- Firefox 121+
- Safari 17+
- Edge 120+

Uses modern CSS (CSS Grid, Flexbox) and ES6+ JavaScript.

## Performance Considerations

- **Chat history**: Stored in memory (cleared on server restart)
- **Static files**: Served with security checks preventing directory traversal
- **API responses**: JSON serialization, no compression (streaming recommended for large datasets)
- **Memory queue**: Unbounded growth (production would use persistent storage)

## Future Enhancements

1. **Persistent Storage**: Store chat history and memory queue to disk/database
2. **Real Embeddings**: Replace TF-IDF with transformer embeddings (sentence-transformers)
3. **Tool Execution**: Add UI for sandboxed tool operations
4. **Frame Management**: Browse, search, and manage cryptographically signed frames
5. **Export**: Download conversations, facts, and search results
6. **Multi-User**: Session isolation with user authentication
7. **Mobile Responsive**: Enhanced mobile UX (currently desktop-focused)
8. **Dark Mode**: Toggle between light/dark theme

## Dependencies

**Backend**:
- Python stdlib only (http.server, json, etc.)
- No external packages required
- Optional: Vault and Agent instances from core/packages

**Frontend**:
- Plain HTML5, CSS3, JavaScript ES6+
- No frameworks or build tools required
- No npm/node.js dependency

## Security Notes

- **CORS**: Server sends CORS headers for browser access
- **Static Files**: Path validation prevents directory traversal attacks
- **XSS Prevention**: API responses are JSON (not HTML)
- **CSRF**: Not applicable for stateless REST API
- **Auth**: Currently no authentication (add before production)

## License

Part of ArcticCodex project. See main repository for license.
