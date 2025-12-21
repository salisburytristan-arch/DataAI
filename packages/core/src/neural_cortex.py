"""
Phase II: Neural Cortex (System 1) + Symbolic Frontal Lobe (System 2)

The Neural Cortex is a modified Transformer optimized for trinary sequences.
The Symbolic Frontal Lobe is the Orchestrator that manages perception, proposal,
critique, and refinement.

Together, they form the "Neuro-Symbolic Hybrid" cognitive architecture.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib


@dataclass
class Frame:
    """
    ForgeNumerics-S Frame: The atomic unit of thought.
    """
    frame_type: str  # TYPE: FACT, TRAIN_PAIR, QUERY, LOG, EXPLAIN, DICT_UPDATE, etc.
    payload: Dict  # Content-specific data
    metadata: Dict = None  # Timestamps, sources, confidence
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        self.metadata['timestamp'] = datetime.now().isoformat()
        self.metadata['hash'] = self.compute_hash()

    def compute_hash(self) -> str:
        """Compute SHA256 hash of frame for content-addressing."""
        content = f"{self.frame_type}{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        """Serialize frame."""
        return {
            'frame_type': self.frame_type,
            'payload': self.payload,
            'metadata': self.metadata
        }


class NeuralCortex:
    """
    System 1: Fast, intuitive pattern matching on trinary sequences.
    Implements a simplified Transformer-like architecture for ForgeNumerics-S tokens.
    """

    def __init__(self, vocab_size: int = 500, embedding_dim: int = 256, num_heads: int = 8):
        """
        Args:
            vocab_size: Number of distinct ForgeNumerics symbols
            embedding_dim: Dimension of token embeddings
            num_heads: Number of attention heads
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.head_dim = embedding_dim // num_heads

        # Initialize embeddings
        self.token_embeddings = np.random.normal(0, 0.01, (vocab_size, embedding_dim))
        
        # Trinary number embeddings (hard-coded for mathematical meaning)
        self.number_embeddings = {
            '0': np.array([1.0, 0.0, 0.0]),  # ⊙
            '1': np.array([0.0, 1.0, 0.0]),  # ⊗
            '2': np.array([0.0, 0.0, 1.0]),  # Φ
        }

        # Attention weights (Q, K, V per head)
        self.attention_weights = np.random.normal(
            0, 0.01, 
            (num_heads, embedding_dim, self.head_dim * 3)
        )

        # Feed-forward layers
        self.ff_w1 = np.random.normal(0, 0.01, (embedding_dim, embedding_dim * 4))
        self.ff_w2 = np.random.normal(0, 0.01, (embedding_dim * 4, embedding_dim))

        # Training history
        self.loss_history = []

    def embed_tokens(self, token_ids: List[int]) -> np.ndarray:
        """
        Embed token sequence.
        Tokens 0-2 (trinary numbers) use hard-coded embeddings.
        Tokens 3+ use learned embeddings.
        """
        embeddings = []
        for token_id in token_ids:
            if token_id < 3:
                # Trinary number: use hard-coded embedding
                emb = self.number_embeddings[str(token_id)]
                # Expand to embedding_dim
                emb = np.pad(emb, (0, self.embedding_dim - 3), constant_values=0)
            else:
                # Word/symbol: use learned embedding
                emb = self.token_embeddings[min(token_id, self.vocab_size - 1)]
            embeddings.append(emb)
        
        return np.array(embeddings)  # (seq_len, embedding_dim)

    def multi_head_attention(self, query: np.ndarray, key: np.ndarray, 
                           value: np.ndarray) -> np.ndarray:
        """
        Simplified multi-head attention.
        Args:
            query, key, value: (seq_len, embedding_dim)
        Returns:
            attention_output: (seq_len, embedding_dim)
        """
        seq_len = query.shape[0]
        attention_outputs = []

        for head_idx in range(self.num_heads):
            # Project Q, K, V
            w = self.attention_weights[head_idx]
            q_proj = query @ w[:, :self.head_dim]  # (seq_len, head_dim)
            k_proj = key @ w[:, self.head_dim:2*self.head_dim]
            v_proj = value @ w[:, 2*self.head_dim:]

            # Attention scores
            scores = (q_proj @ k_proj.T) / np.sqrt(self.head_dim)  # (seq_len, seq_len)
            
            # Softmax (approximate with tanh for stability)
            attn_weights = np.tanh(scores)  # (-1, 1) normalized

            # Apply attention to values
            output = attn_weights @ v_proj  # (seq_len, head_dim)
            attention_outputs.append(output)

        # Concatenate heads
        concat_output = np.concatenate(attention_outputs, axis=1)  # (seq_len, embedding_dim)
        return concat_output

    def forward(self, token_ids: List[int]) -> Tuple[np.ndarray, float]:
        """
        Forward pass: token_ids -> logits + prediction loss.
        Uses compression loss: prefer shorter valid encodings.
        """
        # Embed
        embeddings = self.embed_tokens(token_ids)

        # Self-attention
        attn_output = self.multi_head_attention(embeddings, embeddings, embeddings)

        # Add residual
        hidden = embeddings + attn_output

        # Feed-forward
        ff = np.maximum(0, hidden @ self.ff_w1)  # ReLU
        output = ff @ self.ff_w2

        # Predict next token (logits over vocab)
        logits = output[-1]  # Use last hidden state

        # Compute compression loss
        # Prefer predictions that lead to shorter encoding (Occam's Razor)
        probs = np.exp(logits) / np.sum(np.exp(logits))
        compression_loss = -np.log(np.max(probs) + 1e-8)

        return output, compression_loss

    def predict_next_token(self, token_ids: List[int], temperature: float = 1.0) -> int:
        """
        Predict next most likely token (greedy).
        """
        output, _ = self.forward(token_ids)
        logits = output[-1] / temperature
        probs = np.exp(logits) / np.sum(np.exp(logits))
        return np.argmax(probs)


class SymbolicFrontalLobe:
    """
    System 2: Slow, deliberate reasoning using explicit logic and rules.
    Implements the Orchestrator that manages the perception-propose-critique-refine loop.
    """

    def __init__(self, cortex: NeuralCortex, validator):
        """
        Args:
            cortex: The Neural Cortex instance
            validator: Frame validator for schema checking
        """
        self.cortex = cortex
        self.validator = validator
        self.fact_database = {}  # known_facts: fact_id -> Fact
        self.schema_rules = {}  # schema_name -> rules
        self.decision_log = []  # Audit trail of decisions

    def perceive(self, input_frame: Frame) -> Frame:
        """
        Step 1: Receive and validate input.
        """
        # Check against schema
        is_valid = self.validator.validate(input_frame)
        
        if not is_valid:
            return Frame(
                frame_type='ERROR',
                payload={
                    'error': 'Invalid frame schema',
                    'input': input_frame.to_dict()
                }
            )

        return input_frame

    def propose(self, perceived_frame: Frame, context: List[int]) -> Frame:
        """
        Step 2: Neural Cortex proposes a draft response.
        Uses the token context to predict next frame.
        """
        # Run cortex forward pass on context
        output, loss = self.cortex.forward(context)
        
        # Generate draft tokens
        draft_tokens = context.copy()
        for _ in range(50):  # Max 50 tokens for draft
            next_token = self.cortex.predict_next_token(draft_tokens)
            draft_tokens.append(next_token)
            if next_token == 0:  # Stop token
                break

        return Frame(
            frame_type='DRAFT_RESPONSE',
            payload={
                'tokens': draft_tokens,
                'loss': float(loss),
                'source': 'neural_cortex'
            }
        )

    def critique(self, draft_frame: Frame, known_facts: Dict) -> Tuple[bool, List[str]]:
        """
        Step 3: Symbolic logic checks draft against fact database.
        Returns (is_valid, error_messages).
        """
        errors = []

        # Check: Does draft create logical contradictions?
        draft_facts = self._extract_facts_from_frame(draft_frame)
        
        for fact in draft_facts:
            # Check against fact database
            conflicting = self._find_contradictions(fact, known_facts)
            if conflicting:
                errors.append(f"Draft contradicts known fact: {conflicting}")

        return len(errors) == 0, errors

    def refine(self, draft_frame: Frame, errors: List[str]) -> Frame:
        """
        Step 4: If critique found errors, refine the draft.
        Forces regeneration with constraints.
        """
        if not errors:
            return draft_frame

        # Mark draft as rejected
        refined = Frame(
            frame_type='REFINED_RESPONSE',
            payload={
                'original_draft': draft_frame.to_dict(),
                'errors_found': errors,
                'constraint': 'do_not_contradict_known_facts',
                'status': 'requires_regeneration'
            }
        )

        return refined

    def full_loop(self, input_frame: Frame, context: List[int], 
                 known_facts: Dict) -> Frame:
        """
        Execute full Perception → Proposal → Critique → Refine loop.
        """
        # 1. Perceive
        perceived = self.perceive(input_frame)
        if perceived.frame_type == 'ERROR':
            return perceived

        # 2. Propose
        draft = self.propose(perceived, context)

        # 3. Critique
        is_valid, errors = self.critique(draft, known_facts)

        # 4. Refine (if needed)
        if is_valid:
            result = Frame(
                frame_type='RESPONSE',
                payload=draft.payload,
                metadata={'critiqued': True, 'valid': True}
            )
        else:
            result = self.refine(draft, errors)

        # Log decision
        self.decision_log.append({
            'input': input_frame.to_dict(),
            'result': result.to_dict(),
            'valid': is_valid
        })

        return result

    def _extract_facts_from_frame(self, frame: Frame) -> List[Dict]:
        """
        Extract factual claims from a frame.
        """
        if frame.frame_type == 'FACT':
            return [frame.payload]
        # Recursively extract from nested frames
        facts = []
        if 'payload' in frame.to_dict():
            payload = frame.payload
            if isinstance(payload, dict) and 'facts' in payload:
                facts.extend(payload['facts'])
        return facts

    def _find_contradictions(self, fact: Dict, known_facts: Dict) -> Optional[str]:
        """
        Check if a fact contradicts any known facts.
        """
        # Simplified: just check for direct conflicts
        fact_key = f"{fact.get('subject')}_{fact.get('predicate')}"
        
        for known_key, known_value in known_facts.items():
            if known_key == fact_key:
                if known_value.get('object') != fact.get('object'):
                    return f"{fact_key}: conflicting objects"
        
        return None


class ExtensionDictionary:
    """
    Dynamic Vocabulary: Allocates new symbols for discovered concepts.
    Supports ~750,000 unique symbol combinations (from Phase II).
    """

    def __init__(self):
        self.entries = {}  # symbol -> definition
        self.next_id = 3  # Start after ⊙, ⊗, Φ
        self.broadcasts = []  # DICT_UPDATE frames sent

    def allocate_symbol(self, concept: str, definition: str) -> int:
        """
        Allocate a new symbol for a concept.
        Returns symbol ID.
        """
        if concept in self.entries:
            return self.entries[concept]['id']

        symbol_id = self.next_id
        self.next_id += 1

        self.entries[concept] = {
            'id': symbol_id,
            'definition': definition,
            'allocated_at': datetime.now().isoformat()
        }

        # Create broadcast frame
        broadcast = Frame(
            frame_type='DICT_UPDATE',
            payload={
                'concept': concept,
                'symbol_id': symbol_id,
                'definition': definition
            }
        )
        self.broadcasts.append(broadcast)

        return symbol_id

    def get_definition(self, symbol_id: int) -> Optional[str]:
        """Retrieve definition for a symbol."""
        for concept, entry in self.entries.items():
            if entry['id'] == symbol_id:
                return entry['definition']
        return None

    def size(self) -> int:
        """Total symbols allocated."""
        return len(self.entries) + 3  # +3 for base trits


if __name__ == "__main__":
    print("=== Phase II: Neural Cortex & Symbolic Lobe ===\n")

    # Initialize components
    cortex = NeuralCortex(vocab_size=500, embedding_dim=256, num_heads=8)

    class SimpleValidator:
        def validate(self, frame: Frame) -> bool:
            return True  # Demo: all frames valid

    orchestrator = SymbolicFrontalLobe(cortex, SimpleValidator())

    # Test perception-proposal-critique-refine loop
    print("=== Testing Full Loop ===")
    input_frame = Frame(
        frame_type='QUERY',
        payload={'question': 'What is 2+2?'}
    )

    context = [1, 0, 1, 0, 2]  # Simple token sequence
    known_facts = {
        '2_plus_2': {'object': '4'}
    }

    result = orchestrator.full_loop(input_frame, context, known_facts)
    print(f"Input: {input_frame.frame_type}")
    print(f"Result: {result.frame_type}")
    print(f"Valid: {result.metadata.get('valid', False)}\n")

    # Test extension dictionary
    print("=== Extension Dictionary ===")
    extdict = ExtensionDictionary()
    sym1 = extdict.allocate_symbol('superintelligence', 'AGI beyond human capability')
    sym2 = extdict.allocate_symbol('recursion', 'Self-referential process')
    print(f"Allocated 'superintelligence' as symbol {sym1}")
    print(f"Allocated 'recursion' as symbol {sym2}")
    print(f"Total symbols: {extdict.size()}")
    print(f"DICT_UPDATE broadcasts: {len(extdict.broadcasts)}")
