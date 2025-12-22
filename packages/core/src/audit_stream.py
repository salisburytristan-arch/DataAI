"""
Audit Event Stream with Hash-Chaining

Append-only, tamper-evident audit log for enterprise compliance.
Every operation generates ordered events with cryptographic integrity.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path


EventType = Literal[
    "request_received",
    "evidence_retrieved",
    "tool_called",
    "tool_approved",
    "model_called",
    "response_signed",
    "claim_assessed",
    "phi_detected",
    "escalation_triggered",
    "persisted",
    "user_action"
]


@dataclass
class AuditEvent:
    """Single audit event with hash-chaining"""
    event_id: str
    timestamp: str  # ISO 8601
    event_type: EventType
    user_id: str
    org_id: str
    session_id: str
    data: Dict[str, Any]
    prev_event_hash: str  # Hash of previous event (chain)
    event_hash: str  # SHA256(prev_hash + event_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), sort_keys=True)


class AuditStream:
    """Append-only audit event stream with hash-chaining"""
    
    def __init__(self, storage_dir: str = "./audit_logs"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_stream_file = self.storage_dir / f"stream_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self.event_count = 0
        self.last_event_hash = "0" * 64  # Genesis hash
        
        # Load last hash if stream exists
        if self.current_stream_file.exists():
            self._load_last_hash()
    
    def _load_last_hash(self):
        """Load the last event hash from existing stream"""
        with open(self.current_stream_file, 'r') as f:
            lines = f.readlines()
            if lines:
                last_event = json.loads(lines[-1])
                self.last_event_hash = last_event['event_hash']
                self.event_count = len(lines)
    
    def _compute_event_hash(self, event_data: Dict[str, Any], prev_hash: str) -> str:
        """Compute SHA256 hash of event + previous hash"""
        # Create deterministic string representation
        event_json = json.dumps(event_data, sort_keys=True)
        combined = f"{prev_hash}{event_json}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def append_event(
        self,
        event_type: EventType,
        user_id: str,
        org_id: str,
        session_id: str,
        data: Dict[str, Any]
    ) -> AuditEvent:
        """
        Append new event to stream with hash-chaining.
        Returns the created AuditEvent.
        """
        self.event_count += 1
        event_id = f"{org_id}_{session_id}_{self.event_count:06d}"
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Prepare event data for hashing
        event_data = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "user_id": user_id,
            "org_id": org_id,
            "session_id": session_id,
            "data": data
        }
        
        # Compute hash with chain
        event_hash = self._compute_event_hash(event_data, self.last_event_hash)
        
        # Create event object
        event = AuditEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=data,
            prev_event_hash=self.last_event_hash,
            event_hash=event_hash
        )
        
        # Write to stream (append-only)
        with open(self.current_stream_file, 'a') as f:
            f.write(event.to_json() + '\n')
        
        # Update chain
        self.last_event_hash = event_hash
        
        return event
    
    def verify_chain(self, start_index: int = 0, end_index: Optional[int] = None) -> tuple[bool, Optional[str]]:
        """
        Verify hash-chain integrity.
        Returns (is_valid, error_message).
        """
        if not self.current_stream_file.exists():
            return True, None
        
        with open(self.current_stream_file, 'r') as f:
            events = [json.loads(line) for line in f]
        
        if end_index is None:
            end_index = len(events)
        
        # Verify each event's hash
        for i in range(start_index, end_index):
            event = events[i]
            
            # Get previous hash (or genesis)
            prev_hash = events[i-1]['event_hash'] if i > 0 else "0" * 64
            
            # Verify prev_event_hash matches
            if event['prev_event_hash'] != prev_hash:
                return False, f"Event {i} prev_hash mismatch: expected {prev_hash}, got {event['prev_event_hash']}"
            
            # Recompute hash
            event_data = {
                "event_id": event['event_id'],
                "timestamp": event['timestamp'],
                "event_type": event['event_type'],
                "user_id": event['user_id'],
                "org_id": event['org_id'],
                "session_id": event['session_id'],
                "data": event['data']
            }
            expected_hash = self._compute_event_hash(event_data, prev_hash)
            
            if event['event_hash'] != expected_hash:
                return False, f"Event {i} hash mismatch: expected {expected_hash}, got {event['event_hash']}"
        
        return True, None
    
    def query_events(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        event_types: Optional[List[EventType]] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """
        Query events with filters.
        Returns list of matching AuditEvent objects.
        """
        if not self.current_stream_file.exists():
            return []
        
        results = []
        
        with open(self.current_stream_file, 'r') as f:
            for line in f:
                event_dict = json.loads(line)
                
                # Apply filters
                if start_time and event_dict['timestamp'] < start_time:
                    continue
                if end_time and event_dict['timestamp'] > end_time:
                    continue
                if event_types and event_dict['event_type'] not in event_types:
                    continue
                if user_id and event_dict['user_id'] != user_id:
                    continue
                if org_id and event_dict['org_id'] != org_id:
                    continue
                if session_id and event_dict['session_id'] != session_id:
                    continue
                
                # Convert to AuditEvent
                event = AuditEvent(**event_dict)
                results.append(event)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def export_audit_package(
        self,
        output_path: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        include_config: bool = True
    ) -> Dict[str, Any]:
        """
        Export audit package with events, signatures, and metadata.
        Returns export manifest.
        """
        import zipfile
        import shutil
        
        # Create temp directory
        temp_dir = Path(f"/tmp/audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Query events
        events = self.query_events(start_time=start_time, end_time=end_time, limit=100000)
        
        # Write events JSON
        events_file = temp_dir / "events.jsonl"
        with open(events_file, 'w') as f:
            for event in events:
                f.write(event.to_json() + '\n')
        
        # Verify chain
        is_valid, error = self.verify_chain()
        verification_result = {
            "is_valid": is_valid,
            "error": error,
            "verified_at": datetime.utcnow().isoformat() + "Z",
            "event_count": len(events)
        }
        
        verification_file = temp_dir / "verification.json"
        with open(verification_file, 'w') as f:
            json.dump(verification_result, f, indent=2)
        
        # Config snapshot (if requested)
        if include_config:
            config_data = {
                "export_timestamp": datetime.utcnow().isoformat() + "Z",
                "start_time": start_time,
                "end_time": end_time,
                "event_count": len(events),
                "storage_dir": str(self.storage_dir)
            }
            config_file = temp_dir / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        
        # Create ZIP archive
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in temp_dir.glob('*'):
                zipf.write(file, arcname=file.name)
        
        # Cleanup temp
        shutil.rmtree(temp_dir)
        
        manifest = {
            "export_path": output_path,
            "event_count": len(events),
            "chain_valid": is_valid,
            "exported_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return manifest


class AuditLogger:
    """High-level audit logging interface"""
    
    def __init__(self, stream: AuditStream):
        self.stream = stream
    
    def log_request(self, user_id: str, org_id: str, session_id: str, query: str):
        """Log incoming request"""
        return self.stream.append_event(
            event_type="request_received",
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data={"query": query, "query_length": len(query)}
        )
    
    def log_evidence_retrieval(
        self,
        user_id: str,
        org_id: str,
        session_id: str,
        query: str,
        chunk_ids: List[str],
        scores: List[float]
    ):
        """Log evidence retrieval"""
        return self.stream.append_event(
            event_type="evidence_retrieved",
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data={
                "query": query,
                "chunk_count": len(chunk_ids),
                "chunk_ids": chunk_ids,
                "scores": scores,
                "avg_score": sum(scores) / len(scores) if scores else 0.0
            }
        )
    
    def log_tool_call(
        self,
        user_id: str,
        org_id: str,
        session_id: str,
        tool_name: str,
        args: Dict[str, Any],
        approved_by: Optional[str] = None
    ):
        """Log tool execution"""
        args_hash = hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest()
        
        return self.stream.append_event(
            event_type="tool_called",
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data={
                "tool_name": tool_name,
                "args_hash": args_hash,
                "approved_by": approved_by,
                "auto_approved": approved_by is None
            }
        )
    
    def log_model_call(
        self,
        user_id: str,
        org_id: str,
        session_id: str,
        provider: str,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        latency_ms: float
    ):
        """Log LLM API call"""
        return self.stream.append_event(
            event_type="model_called",
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data={
                "provider": provider,
                "model_id": model_id,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms
            }
        )
    
    def log_phi_detection(
        self,
        user_id: str,
        org_id: str,
        session_id: str,
        phi_count: int,
        high_impact_count: int,
        contradiction_count: int,
        escalation_triggered: bool
    ):
        """Log State Φ detection"""
        return self.stream.append_event(
            event_type="phi_detected",
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data={
                "phi_count": phi_count,
                "high_impact_count": high_impact_count,
                "contradiction_count": contradiction_count,
                "escalation_triggered": escalation_triggered
            }
        )
    
    def log_response_signed(
        self,
        user_id: str,
        org_id: str,
        session_id: str,
        response_hash: str,
        signature: str
    ):
        """Log response signing"""
        return self.stream.append_event(
            event_type="response_signed",
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data={
                "response_hash": response_hash,
                "signature": signature
            }
        )


# Example usage
if __name__ == "__main__":
    # Initialize stream
    stream = AuditStream(storage_dir="./test_audit")
    logger = AuditLogger(stream)
    
    # Log some events
    logger.log_request("user123", "org_demo", "session_001", "What is Python?")
    logger.log_evidence_retrieval("user123", "org_demo", "session_001", "What is Python?", ["chunk1", "chunk2"], [0.9, 0.8])
    logger.log_model_call("user123", "org_demo", "session_001", "openai", "gpt-4", 100, 50, 0.003, 1200.5)
    logger.log_phi_detection("user123", "org_demo", "session_001", 2, 1, 0, True)
    
    # Verify chain
    is_valid, error = stream.verify_chain()
    print(f"Chain valid: {is_valid}")
    if error:
        print(f"Error: {error}")
    
    # Query events
    events = stream.query_events(org_id="org_demo")
    print(f"\nFound {len(events)} events for org_demo")
    
    for event in events:
        print(f"  {event.event_type}: {event.data}")
    
    # Export package
    manifest = stream.export_audit_package("audit_package.zip", include_config=True)
    print(f"\nExported: {manifest}")
