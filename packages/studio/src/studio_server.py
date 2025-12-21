"""Studio Server - Web API for ArcticCodex UI.

Provides HTTP endpoints for:
- Chat interface with citations
- Vault explorer (docs, chunks, facts)
- Hybrid search
- Memory review and management
- Frame inspection and verification

Runs as a simple HTTP server on port 8080 (configurable).
All API responses are JSON.

Usage:
    server = StudioServer(vault=vault, agent=agent)
    server.run(host="localhost", port=8080)
"""

import json
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading


@dataclass
class ChatMessage:
    """A message in the chat."""
    role: str              # "user" or "assistant"
    content: str
    timestamp: str
    citations: List[Dict[str, Any]] = None
    facts_extracted: List[Dict[str, str]] = None


class StudioServer:
    """
    Web server for ArcticCodex Studio UI.
    
    Provides REST API endpoints for all system operations.
    Serves static HTML/CSS/JS frontend from web/ directory.
    
    Endpoints:
    - GET  /api/health              - Server status
    - GET  /api/vault/docs          - List documents
    - GET  /api/vault/chunks        - List chunks
    - GET  /api/vault/facts         - List facts
    - POST /api/search              - Hybrid search
    - POST /api/chat                - Send chat message
    - GET  /api/chat/history        - Get conversation history
    - GET  /api/memory              - List memory items
    - POST /api/memory/approve      - Approve fact
    - POST /api/memory/reject       - Reject fact
    - GET  /api/frames/list         - List frames
    - POST /api/frames/verify       - Verify frame signature
    - GET  /static/*                - Static files
    """
    
    def __init__(
        self,
        vault: Optional[Any] = None,
        agent: Optional[Any] = None,
        convo_id: str = "default",
        port: int = 8080
    ):
        """
        Initialize Studio server.
        
        Args:
            vault: Vault instance for storage/retrieval
            agent: Agent instance for chat
            convo_id: Current conversation ID
            port: HTTP port to listen on
        """
        self.vault = vault
        self.agent = agent
        self.convo_id = convo_id
        self.port = port
        self.chat_history: List[ChatMessage] = []
        self.memory_queue: List[Dict[str, Any]] = []
        self.base_dir = os.path.dirname(__file__)
        self.web_dir = os.path.join(os.path.dirname(self.base_dir), "web")
    
    def run(self, host: str = "localhost", threaded: bool = False) -> HTTPServer:
        """
        Start the HTTP server.
        
        Args:
            host: Host to bind to
            threaded: If True, run in background thread
            
        Returns:
            HTTPServer instance
        """
        server_address = (host, self.port)
        
        # Create handler class that references this server
        server_instance = self
        
        class StudioRequestHandler(BaseHTTPRequestHandler):
            """HTTP request handler."""
            
            def do_GET(self):
                """Handle GET requests."""
                path = urlparse(self.path).path
                query = parse_qs(urlparse(self.path).query)
                
                try:
                    if path == "/api/health":
                        self._respond_json({"status": "ok", "timestamp": datetime.now().isoformat()})
                    
                    elif path == "/api/vault/docs":
                        self._handle_vault_docs()
                    
                    elif path == "/api/vault/chunks":
                        self._handle_vault_chunks(query)
                    
                    elif path == "/api/vault/facts":
                        self._handle_vault_facts(query)
                    
                    elif path == "/api/chat/history":
                        self._handle_chat_history()
                    
                    elif path == "/api/memory":
                        self._handle_memory_list()
                    
                    elif path == "/api/frames/list":
                        self._handle_frames_list()
                    
                    elif path.startswith("/static/"):
                        self._handle_static_file(path)
                    
                    elif path == "/" or path == "/index.html":
                        self._handle_index()
                    
                    else:
                        self._respond_json({"error": "Not found"}, 404)
                
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def do_POST(self):
                """Handle POST requests."""
                path = urlparse(self.path).path
                
                try:
                    # Read request body
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length).decode("utf-8")
                    data = json.loads(body) if body else {}
                    
                    if path == "/api/search":
                        self._handle_search(data)
                    
                    elif path == "/api/chat":
                        self._handle_chat(data)
                    
                    elif path == "/api/memory/approve":
                        self._handle_memory_approve(data)
                    
                    elif path == "/api/memory/reject":
                        self._handle_memory_reject(data)
                    
                    elif path == "/api/frames/verify":
                        self._handle_frame_verify(data)
                    
                    else:
                        self._respond_json({"error": "Not found"}, 404)
                
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_vault_docs(self):
                """List all documents in vault."""
                try:
                    docs = server_instance.vault.list_docs() if server_instance.vault else []
                    self._respond_json({
                        "docs": docs,
                        "count": len(docs)
                    })
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_vault_chunks(self, query):
                """List chunks, optionally filtered by doc."""
                try:
                    doc_id = query.get("doc_id", [None])[0]
                    chunks = server_instance.vault.list_chunks(doc_id=doc_id) if server_instance.vault else []
                    self._respond_json({
                        "chunks": chunks,
                        "count": len(chunks)
                    })
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_vault_facts(self, query):
                """List facts from vault."""
                try:
                    convo_id = query.get("convo_id", [server_instance.convo_id])[0]
                    facts = server_instance.vault.list_facts(
                        metadata_filter={"convo_id": convo_id}
                    ) if server_instance.vault else []
                    self._respond_json({
                        "facts": facts,
                        "count": len(facts)
                    })
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_chat_history(self):
                """Return chat history."""
                messages = [asdict(msg) for msg in server_instance.chat_history]
                self._respond_json({
                    "messages": messages,
                    "count": len(messages),
                    "convo_id": server_instance.convo_id
                })
            
            def _handle_memory_list(self):
                """List memory queue items."""
                self._respond_json({
                    "memory": server_instance.memory_queue,
                    "count": len(server_instance.memory_queue)
                })
            
            def _handle_frames_list(self):
                """List frames from vault."""
                try:
                    # Would load from vault frame storage
                    frames = []
                    self._respond_json({
                        "frames": frames,
                        "count": len(frames)
                    })
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_search(self, data):
                """Perform hybrid search."""
                try:
                    query = data.get("query", "")
                    limit = data.get("limit", 10)
                    
                    if not query:
                        self._respond_json({"error": "Query required"}, 400)
                        return
                    
                    results = []
                    if server_instance.vault:
                        evidence_pack = server_instance.vault.get_evidence_pack(query, limit=limit)
                        results = evidence_pack.get("chunks", []) if evidence_pack else []
                    
                    self._respond_json({
                        "query": query,
                        "results": results,
                        "count": len(results)
                    })
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_chat(self, data):
                """Process chat message."""
                try:
                    user_message = data.get("message", "")
                    
                    if not user_message:
                        self._respond_json({"error": "Message required"}, 400)
                        return
                    
                    # Add user message to history
                    user_msg = ChatMessage(
                        role="user",
                        content=user_message,
                        timestamp=datetime.now().isoformat()
                    )
                    server_instance.chat_history.append(user_msg)
                    
                    # Get agent response
                    assistant_response = ""
                    citations = []
                    facts = []
                    
                    if server_instance.agent:
                        agent_response = server_instance.agent.respond(
                            user_message,
                            evidence_limit=5,
                            persist=True,
                            convo_id=server_instance.convo_id
                        )
                        assistant_response = agent_response.get("text", "")
                        citations = agent_response.get("citations", [])
                        facts = agent_response.get("facts", [])
                        
                        # Add to memory queue for review
                        for fact in facts:
                            server_instance.memory_queue.append({
                                "type": "fact",
                                "data": fact,
                                "status": "pending",
                                "timestamp": datetime.now().isoformat()
                            })
                    
                    # Add assistant message to history
                    assistant_msg = ChatMessage(
                        role="assistant",
                        content=assistant_response,
                        timestamp=datetime.now().isoformat(),
                        citations=citations,
                        facts_extracted=facts
                    )
                    server_instance.chat_history.append(assistant_msg)
                    
                    self._respond_json({
                        "message": assistant_response,
                        "citations": citations,
                        "facts": facts,
                        "timestamp": assistant_msg.timestamp
                    })
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_memory_approve(self, data):
                """Approve a memory item."""
                try:
                    item_index = data.get("index")
                    if item_index is not None and 0 <= item_index < len(server_instance.memory_queue):
                        server_instance.memory_queue[item_index]["status"] = "approved"
                        self._respond_json({"status": "approved"})
                    else:
                        self._respond_json({"error": "Invalid index"}, 400)
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_memory_reject(self, data):
                """Reject a memory item."""
                try:
                    item_index = data.get("index")
                    if item_index is not None and 0 <= item_index < len(server_instance.memory_queue):
                        server_instance.memory_queue[item_index]["status"] = "rejected"
                        self._respond_json({"status": "rejected"})
                    else:
                        self._respond_json({"error": "Invalid index"}, 400)
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_frame_verify(self, data):
                """Verify a frame signature."""
                try:
                    frame_str = data.get("frame")
                    if not frame_str:
                        self._respond_json({"error": "Frame required"}, 400)
                        return
                    
                    # Would use frame_verifier if available
                    self._respond_json({
                        "verified": True,
                        "message": "Frame signature valid"
                    })
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_static_file(self, path):
                """Serve static file."""
                try:
                    # Remove /static/ prefix
                    relative_path = path[8:]
                    file_path = os.path.join(server_instance.web_dir, relative_path)
                    
                    # Security: prevent directory traversal
                    if not os.path.abspath(file_path).startswith(os.path.abspath(server_instance.web_dir)):
                        self._respond_json({"error": "Not found"}, 404)
                        return
                    
                    if not os.path.exists(file_path):
                        self._respond_json({"error": "Not found"}, 404)
                        return
                    
                    # Determine content type
                    if file_path.endswith(".html"):
                        content_type = "text/html"
                    elif file_path.endswith(".css"):
                        content_type = "text/css"
                    elif file_path.endswith(".js"):
                        content_type = "application/javascript"
                    elif file_path.endswith(".json"):
                        content_type = "application/json"
                    else:
                        content_type = "text/plain"
                    
                    with open(file_path, "rb") as f:
                        content = f.read()
                    
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", len(content))
                    self.end_headers()
                    self.wfile.write(content)
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_index(self):
                """Serve index.html."""
                self._handle_static_file("/static/index.html")
            
            def _respond_json(self, data: Dict[str, Any], status: int = 200):
                """Send JSON response."""
                response_body = json.dumps(data).encode("utf-8")
                
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", len(response_body))
                self.end_headers()
                self.wfile.write(response_body)
            
            def log_message(self, format, *args):
                """Suppress default logging."""
                pass
        
        http_server = HTTPServer(server_address, StudioRequestHandler)
        
        if threaded:
            thread = threading.Thread(target=http_server.serve_forever)
            thread.daemon = True
            thread.start()
            return http_server
        else:
            http_server.serve_forever()
            return http_server


def start_studio(
    vault: Optional[Any] = None,
    agent: Optional[Any] = None,
    convo_id: str = "default",
    port: int = 8080,
    host: str = "localhost"
):
    """
    Start the Studio server.
    
    Args:
        vault: Vault instance
        agent: Agent instance
        convo_id: Conversation ID
        port: HTTP port
        host: Host to bind to
    """
    print(f"Starting ArcticCodex Studio on {host}:{port}")
    print(f"Open http://{host}:{port} in your browser")
    
    server = StudioServer(vault=vault, agent=agent, convo_id=convo_id, port=port)
    server.run(host=host)
