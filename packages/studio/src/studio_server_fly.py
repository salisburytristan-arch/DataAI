"""Enhanced Studio Server for Fly.io with Full LLM Support.

Combines:
- Vault with 230k+ chunks
- Chat with context and citations
- Streaming responses
- Conversation persistence
"""

import json
import os
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import argparse
import sys
from pathlib import Path

# Add workspace to path
repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo_root))

from packages.vault.src.vault import Vault
from packages.core.src.agent import Agent
from packages.core.src.llm.llama_client import HttpLLM, MockLLM
from packages.core.src.config import get_llm_client


@dataclass
class ChatMessage:
    """Single chat message with full context."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    citations: Optional[List[Dict[str, Any]]] = None
    facts_extracted: Optional[List[Dict[str, str]]] = None


class FlyStudioServer:
    """Production Studio Server for Fly.io."""
    
    def __init__(
        self,
        vault_path: str = "/app/vault",
        models_dir: str = "/app/models",
        port: int = 8000,
        host: str = "0.0.0.0",
        embeddings: bool = True,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """Initialize server with vault, models, and LLM."""
        self.port = port
        self.host = host
        self.vault_path = vault_path
        self.models_dir = models_dir
        
        # Load vault (with 230k chunks)
        vault_path = Path(vault_path)
        vault_path.mkdir(parents=True, exist_ok=True)
        
        print(f"[*] Loading vault from {vault_path}")
        self.vault = Vault(str(vault_path))
        
        # Initialize LLM
        print("[*] Initializing LLM client")
        self.llm = self._init_llm(models_dir)
        
        # Initialize agent with vault + LLM
        print("[*] Initializing agent")
        self.agent = Agent(vault=self.vault, llm=self.llm)
        
        # Conversation state
        self.conversations: Dict[str, List[ChatMessage]] = {}
        self.memory_queue: List[Dict[str, Any]] = []
        self.base_dir = os.path.dirname(__file__)
        self.web_dir = os.path.join(os.path.dirname(self.base_dir), "web")
        
        print(f"[✓] Server ready on {self.host}:{self.port}")
    
    def _init_llm(self, models_dir: str):
        """Initialize LLM from environment or fallback."""
        # Try environment variables first
        llm_endpoint = os.environ.get("AC_LLM_ENDPOINT")
        if llm_endpoint:
            print(f"[*] Using remote LLM at {llm_endpoint}")
            return HttpLLM(endpoint=llm_endpoint)
        
        # Try local GGUF model
        gguf_path = os.environ.get("AC_GGUF_MODEL")
        if gguf_path and os.path.exists(gguf_path):
            print(f"[*] Loading GGUF model from {gguf_path}")
            try:
                from llama_cpp import Llama
                return Llama(model_path=gguf_path, n_gpu_layers=-1, verbose=False)
            except Exception as e:
                print(f"[!] Failed to load GGUF: {e}, using mock")
        
        # Fallback
        print("[*] Using MockLLM for development")
        return MockLLM()
    
    def run(self):
        """Start HTTP server."""
        server_address = (self.host, self.port)
        server_instance = self
        
        class FlyRequestHandler(BaseHTTPRequestHandler):
            """HTTP handler for all requests."""
            
            def do_GET(self):
                """Handle GET requests."""
                path = urlparse(self.path).path
                query = parse_qs(urlparse(self.path).query)
                
                try:
                    if path == "/api/health":
                        self._respond_json({
                            "status": "healthy",
                            "timestamp": datetime.now().isoformat(),
                            "vault_chunks": len(list(server_instance.vault.objects.glob("chunks/*"))),
                        })
                    
                    elif path == "/api/vault/stats":
                        self._handle_vault_stats()
                    
                    elif path == "/api/search":
                        self._handle_search(query)
                    
                    elif path == "/api/chat/conversations":
                        self._handle_list_conversations()
                    
                    elif path.startswith("/static/"):
                        self._handle_static(path)
                    
                    elif path == "/" or path == "/index.html":
                        self._serve_file(os.path.join(server_instance.web_dir, "index.html"), "text/html")
                    
                    else:
                        self._respond_json({"error": "Not found"}, 404)
                
                except Exception as e:
                    print(f"[!] GET {path}: {e}")
                    self._respond_json({"error": str(e)}, 500)
                
                self.log_message = lambda *args: None  # Suppress logs
            
            def do_POST(self):
                """Handle POST requests."""
                path = urlparse(self.path).path
                
                try:
                    content_length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(content_length).decode("utf-8")
                    data = json.loads(body) if body else {}
                    
                    if path == "/api/chat":
                        self._handle_chat(data)
                    
                    elif path == "/api/chat/stream":
                        self._handle_chat_stream(data)
                    
                    else:
                        self._respond_json({"error": "Not found"}, 404)
                
                except Exception as e:
                    print(f"[!] POST {path}: {e}")
                    self._respond_json({"error": str(e)}, 500)
                
                self.log_message = lambda *args: None
            
            def _handle_vault_stats(self):
                """Return vault statistics."""
                docs = len(list(server_instance.vault.index.glob("docs/*")))
                chunks = len(list(server_instance.vault.index.glob("chunks/*")))
                self._respond_json({
                    "docs_count": docs,
                    "chunks_count": chunks,
                    "vault_path": server_instance.vault_path,
                })
            
            def _handle_search(self, query_params):
                """Perform semantic + TF-IDF search."""
                q = query_params.get("q", [""])[0]
                limit = int(query_params.get("limit", [5])[0])
                
                if not q:
                    self._respond_json({"error": "Query required"}, 400)
                    return
                
                try:
                    evidence = server_instance.vault.get_evidence_pack(q, limit=limit)
                    self._respond_json({
                        "query": q,
                        "results": evidence.get("chunks", []),
                        "count": len(evidence.get("chunks", []))
                    })
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_list_conversations(self):
                """List all conversation IDs."""
                convos = list(server_instance.conversations.keys())
                self._respond_json({
                    "conversations": convos,
                    "count": len(convos)
                })
            
            def _handle_chat(self, data):
                """Handle single chat message with full response."""
                user_msg = data.get("message", "")
                convo_id = data.get("convo_id", f"conv-{datetime.now().timestamp()}")
                
                if not user_msg:
                    self._respond_json({"error": "Message required"}, 400)
                    return
                
                try:
                    # Get or create conversation
                    if convo_id not in server_instance.conversations:
                        server_instance.conversations[convo_id] = []
                    
                    # Add user message
                    user_chat = ChatMessage(
                        role="user",
                        content=user_msg,
                        timestamp=datetime.now().isoformat()
                    )
                    server_instance.conversations[convo_id].append(user_chat)
                    
                    # Get agent response
                    agent_response = server_instance.agent.respond(
                        user_msg,
                        evidence_limit=5,
                        persist=True,
                        convo_id=convo_id
                    )
                    
                    # Add assistant message
                    assistant_chat = ChatMessage(
                        role="assistant",
                        content=agent_response.get("text", ""),
                        timestamp=datetime.now().isoformat(),
                        citations=agent_response.get("citations", []),
                        facts_extracted=agent_response.get("facts", [])
                    )
                    server_instance.conversations[convo_id].append(assistant_chat)
                    
                    # Return response
                    self._respond_json({
                        "convo_id": convo_id,
                        "message": asdict(assistant_chat),
                        "history_length": len(server_instance.conversations[convo_id])
                    })
                
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_chat_stream(self, data):
                """Stream chat response token-by-token."""
                user_msg = data.get("message", "")
                convo_id = data.get("convo_id", f"conv-{datetime.now().timestamp()}")
                
                if not user_msg:
                    self._respond_json({"error": "Message required"}, 400)
                    return
                
                try:
                    if convo_id not in server_instance.conversations:
                        server_instance.conversations[convo_id] = []
                    
                    # Add user message
                    user_chat = ChatMessage(
                        role="user",
                        content=user_msg,
                        timestamp=datetime.now().isoformat()
                    )
                    server_instance.conversations[convo_id].append(user_chat)
                    
                    # Stream response
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-ndjson")
                    self.send_header("Transfer-Encoding", "chunked")
                    self.end_headers()
                    
                    # Simulate streaming (real impl would use LLM streaming)
                    agent_response = server_instance.agent.respond(
                        user_msg,
                        evidence_limit=5,
                        persist=True,
                        convo_id=convo_id
                    )
                    
                    text = agent_response.get("text", "")
                    for token in text.split():
                        event = json.dumps({"token": token, "type": "delta"})
                        self.wfile.write((event + "\n").encode())
                    
                    # Send final message
                    final = json.dumps({
                        "type": "done",
                        "citations": agent_response.get("citations", [])
                    })
                    self.wfile.write((final + "\n").encode())
                
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _handle_static(self, path):
                """Serve static files."""
                file_path = os.path.join(server_instance.web_dir, path.lstrip("/static/"))
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    ext = os.path.splitext(file_path)[1].lower()
                    content_types = {
                        ".html": "text/html",
                        ".css": "text/css",
                        ".js": "application/javascript",
                        ".json": "application/json",
                        ".svg": "image/svg+xml",
                        ".png": "image/png",
                    }
                    content_type = content_types.get(ext, "application/octet-stream")
                    self._serve_file(file_path, content_type)
                else:
                    self._respond_json({"error": "Not found"}, 404)
            
            def _serve_file(self, file_path, content_type):
                """Serve a file."""
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", len(content))
                    self.end_headers()
                    self.wfile.write(content)
                except Exception as e:
                    self._respond_json({"error": str(e)}, 500)
            
            def _respond_json(self, data: Dict, status: int = 200):
                """Send JSON response."""
                body = json.dumps(data, indent=2).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(body))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
        
        # Create and run server
        httpd = HTTPServer(server_address, FlyRequestHandler)
        print(f"[✓] Server listening on http://{self.host}:{self.port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("[*] Server shutting down...")
            httpd.shutdown()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="ArcticCodex Studio Server for Fly.io")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--vault", default="/app/vault", help="Vault directory path")
    parser.add_argument("--models-dir", default="/app/models", help="Models directory path")
    parser.add_argument("--embeddings", choices=["on", "off"], default="on", help="Enable embeddings")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    
    args = parser.parse_args()
    
    server = FlyStudioServer(
        vault_path=args.vault,
        models_dir=args.models_dir,
        port=args.port,
        host=args.host,
        embeddings=args.embeddings == "on",
        embedding_model=args.embedding_model
    )
    server.run()


if __name__ == "__main__":
    main()