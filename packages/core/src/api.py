"""
Agent Vault FastAPI service.
- Health check
- Run single phase or all phases
- Export audit log (in-memory)
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure workspace root on path for sibling package imports
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Add packages/core/src to path for phase imports
CORE_SRC = Path(__file__).resolve().parent
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from phase_manager import PhaseManager
from platform import AuditLog, PolicyEngine, Role, Action
from packages.vault.src.vault import Vault
from agent import Agent

app = FastAPI(title="Agent Vault API", version="1.0.0")

# CORS for local dev plus optionally configured domains (e.g., Vercel)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://localhost:3000",
]
extra_origins = os.environ.get("ALLOWED_ORIGINS", "")
if extra_origins:
    ALLOWED_ORIGINS.extend([o.strip() for o in extra_origins.split(",") if o.strip()])
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = PhaseManager()
audit = AuditLog()
policies = PolicyEngine()

# Simple vault + agent for chat; stored under workspace
VAULT_PATH = ROOT / "vault_api"
VAULT_PATH.mkdir(parents=True, exist_ok=True)
vault = Vault(str(VAULT_PATH))
agent = Agent(vault)


class PhaseRequest(BaseModel):
    org_id: str = Field(default="demo_org", description="Organization ID")
    user_id: str = Field(default="demo_user", description="User ID")
    roles: List[Role] = Field(default_factory=lambda: [Role.ADMIN], description="User roles")
    export: bool = Field(default=False, description="Export frames to response")


class PhaseResponse(BaseModel):
    phase: int
    status: str
    frame_count: int
    frames: Optional[List[str]] = None


class HealthResponse(BaseModel):
    status: str
    phases_loaded: int


class AuditEntryModel(BaseModel):
    timestamp: str
    org_id: str
    user_id: str
    action: str
    resource: str
    result: str
    frame_hash: str
    frame_content: Optional[str]
    details: dict
    entry_hash: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", phases_loaded=len(manager.phases))


@app.post("/phase/{phase_num}", response_model=PhaseResponse)
def run_phase(phase_num: int, body: PhaseRequest) -> PhaseResponse:
    # Policy check (simple demo: allow ADMIN only)
    if not policies.is_tool_allowed("phase", body.roles):
        raise HTTPException(status_code=403, detail="Phase execution not allowed for roles")

    result = manager.run_phase(phase_num)
    status = result.get("status", "UNKNOWN")
    frames = result.get("frames", []) if body.export else None

    # Audit entry (one per phase call)
    frame_hash = ""
    if frames:
        # Extract trailing hash chunk if present
        parts = frames[0].split("∴")
        frame_hash = parts[-1][:16] if parts else ""

    audit.log(
        org_id=body.org_id,
        user_id=body.user_id,
        action=Action.TOOL_CALL,
        resource=f"phase:{phase_num}",
        result=status,
        frame_hash=frame_hash,
    )

    return PhaseResponse(phase=phase_num, status=status, frame_count=len(result.get("frames", [])), frames=frames)


@app.post("/phase/all", response_model=dict)
def run_all_phases(body: PhaseRequest):
    if not policies.is_tool_allowed("phase", body.roles):
        raise HTTPException(status_code=403, detail="Phase execution not allowed for roles")
    results = manager.run_all_phases()
    summary = {
        "status": "ok",
        "complete": sum(1 for r in results.values() if r.get("status") == "COMPLETE"),
        "total": len(results),
    }
    return summary


class ChatRequest(BaseModel):
    org_id: str = Field(default="demo_org")
    user_id: str = Field(default="demo_user")
    roles: List[Role] = Field(default_factory=lambda: [Role.ADMIN])
    message: str
    persist: bool = False
    convo: Optional[str] = None


class ChatResponse(BaseModel):
    text: str
    citations: Optional[list] = None
    summary_id: Optional[str] = None
    convo_id: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    # Policy: only ADMIN/OPERATOR by default
    if not policies.is_tool_allowed("chat", body.roles):
        raise HTTPException(status_code=403, detail="Chat not allowed for roles")

    res = agent.respond(
        body.message,
        evidence_limit=5,
        persist=body.persist,
        convo_id=body.convo,
    )

    audit.log(
        org_id=body.org_id,
        user_id=body.user_id,
        action=Action.TOOL_CALL,
        resource="chat",
        result="SUCCESS",
        frame_hash="",
    )

    return ChatResponse(
        text=res.get("text", ""),
        citations=res.get("citations"),
        summary_id=res.get("persist", {}).get("summary_id"),
        convo_id=res.get("persist", {}).get("convo_id"),
    )


@app.get("/audit", response_model=List[AuditEntryModel])
def get_audit() -> List[AuditEntryModel]:
    return [AuditEntryModel(**e.to_dict()) for e in audit.entries]


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
