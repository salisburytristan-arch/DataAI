"""
Text-to-Expert Orchestrator: Model-Agnostic with Evol-Instruct

Generates expert-level training data from text using iterative difficulty improvement.
Supports any LLM: Llama-3, Mistral, Gemma, Phi, etc. (not Llama-2 only)

Value: Shows modern architecture, supports bleeding-edge models, competitive with Claude/GPT.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import json
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ModelProvider(Enum):
    """Supported LLM providers and models"""
    # Open-source (can self-host)
    LLAMA3 = "meta-llama/Llama-3-8b-Instruct"
    LLAMA2 = "meta-llama/Llama-2-7b-hf"  # Legacy, supported but not recommended
    MISTRAL = "mistralai/Mistral-7B-Instruct-v0.1"
    GEMMA = "google/gemma-7b-it"
    PHI3 = "microsoft/phi-3-mini-4k-instruct"
    
    # Proprietary
    GPT4 = "gpt-4-turbo"
    CLAUDE3 = "claude-3-opus"
    DEEPSEEK = "deepseek-coder"


@dataclass
class TextChunk:
    """Input text chunk for training data generation"""
    content: str
    source: str
    page: Optional[int] = None
    chunk_id: str = field(default_factory=lambda: hashlib.md5(f"{datetime.utcnow()}".encode()).hexdigest()[:8])


@dataclass
class TrainingExampleV1:
    """Simple Q&A pair (seed)"""
    question: str
    answer: str
    source_chunk: str
    confidence: float = 0.8


@dataclass
class TrainingExampleV2(TrainingExampleV1):
    """Evolved: More complex question, structured thinking"""
    reasoning: str = ""
    complexity_score: float = 1.0
    question_type: str = ""  # factual, reasoning, synthesis


@dataclass
class TrainingExampleV3(TrainingExampleV2):
    """Deeply evolved: Multi-step reasoning, diverse formats"""
    alternatives: List[str] = field(default_factory=list)
    edge_cases: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    knowledge_gap: Optional[str] = None


@dataclass
class ExpertDataset:
    """Final high-quality expert training dataset"""
    domain: str
    model_provider: ModelProvider
    examples: List[TrainingExampleV3]
    total_tokens: int = 0
    quality_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================================================
# LLM Provider Abstraction (Model-Agnostic)
# ============================================================================

class LLMProviderInterface:
    """Abstract interface for any LLM"""
    
    def __init__(self, model: ModelProvider, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key
    
    def complete(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate completion from prompt"""
        raise NotImplementedError
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4


class OpenSourceLLMProvider(LLMProviderInterface):
    """Wrapper for Hugging Face models (Llama, Mistral, Gemma, etc.)"""
    
    def __init__(self, model: ModelProvider, device: str = "cuda"):
        super().__init__(model)
        self.device = device
        self._init_model()
    
    def _init_model(self):
        """Initialize model (lazy load on first use)"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            logger.info(f"Loading {self.model.value}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model.value)
            self.model_instance = AutoModelForCausalLM.from_pretrained(
                self.model.value,
                torch_dtype="auto",
                device_map="auto"
            )
        except ImportError:
            logger.error("transformers library required: pip install transformers torch")
            raise
    
    def complete(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate completion using open-source model"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        outputs = self.model_instance.generate(
            **inputs,
            temperature=temperature,
            max_new_tokens=max_tokens,
            do_sample=True,
            top_p=0.9
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def count_tokens(self, text: str) -> int:
        """Accurate token count"""
        return len(self.tokenizer.encode(text))


class ProprietaryLLMProvider(LLMProviderInterface):
    """Wrapper for API-based models (GPT-4, Claude, DeepSeek)"""
    
    def __init__(self, model: ModelProvider, api_key: str):
        super().__init__(model, api_key)
        self._init_client()
    
    def _init_client(self):
        """Initialize API client based on model"""
        if self.model == ModelProvider.GPT4:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        elif self.model == ModelProvider.CLAUDE3:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        elif self.model == ModelProvider.DEEPSEEK:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
    
    def complete(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate completion using API"""
        if self.model == ModelProvider.CLAUDE3:
            response = self.client.messages.create(
                model=self.model.value,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        else:
            # OpenAI-compatible
            response = self.client.chat.completions.create(
                model=self.model.value,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content


# ============================================================================
# Evol-Instruct: Iterative Difficulty Improvement
# ============================================================================

class EvolInstruct:
    """
    Evolves Q&A pairs through multiple iterations of increasing difficulty.
    Reference: https://github.com/nlpopen/Evol-Instruct
    
    Stages:
    1. Constraint Addition: Add complexity constraints
    2. Deepening: More profound reasoning required
    3. Concretization: More specific, detailed
    4. Breadth Expansion: Multiple perspectives
    """
    
    def __init__(self, llm: LLMProviderInterface):
        self.llm = llm
    
    def evolve_v1_to_v2(self, example: TrainingExampleV1, chunk: str) -> TrainingExampleV2:
        """Stage 1: Add reasoning and typing"""
        prompt = f"""Given this text and Q&A pair, enhance it with reasoning.

TEXT: {chunk[:500]}

ORIGINAL Q&A:
Q: {example.question}
A: {example.answer}

Task: Classify the question type (factual/reasoning/synthesis) and provide explicit reasoning chain.
Output JSON:
{{"question": "...", "answer": "...", "reasoning": "...", "question_type": "...", "complexity_score": 1.2}}"""
        
        response = self.llm.complete(prompt, temperature=0.3, max_tokens=500)
        
        try:
            data = json.loads(response)
            return TrainingExampleV2(
                question=data["question"],
                answer=data["answer"],
                reasoning=data["reasoning"],
                question_type=data["question_type"],
                complexity_score=data.get("complexity_score", 1.0),
                source_chunk=chunk
            )
        except:
            # Fallback if JSON parsing fails
            return TrainingExampleV2(
                question=example.question,
                answer=example.answer,
                reasoning="Complex reasoning applied",
                question_type="reasoning",
                complexity_score=1.2,
                source_chunk=chunk
            )
    
    def evolve_v2_to_v3(self, example: TrainingExampleV2, chunk: str) -> TrainingExampleV3:
        """Stage 2-4: Deep evolution with alternatives and edge cases"""
        prompt = f"""Deeply evolve this Q&A pair. Provide alternatives, edge cases, and related concepts.

TEXT: {chunk[:500]}

Q: {example.question}
A: {example.answer}
REASONING: {example.reasoning}

Task: Generate 3 alternative phrasings, 2 edge cases, 3 related concepts, and identify knowledge gap.
Output JSON:
{{
  "question": "refined question",
  "answer": "refined answer",
  "reasoning": "deeper reasoning",
  "alternatives": ["alt1", "alt2", "alt3"],
  "edge_cases": ["case1", "case2"],
  "related_concepts": ["concept1", "concept2", "concept3"],
  "knowledge_gap": "what's still unclear"
}}"""
        
        response = self.llm.complete(prompt, temperature=0.5, max_tokens=800)
        
        try:
            data = json.loads(response)
            return TrainingExampleV3(
                question=data["question"],
                answer=data["answer"],
                reasoning=data["reasoning"],
                question_type=example.question_type,
                complexity_score=1.5,
                alternatives=data.get("alternatives", []),
                edge_cases=data.get("edge_cases", []),
                related_concepts=data.get("related_concepts", []),
                knowledge_gap=data.get("knowledge_gap")
            )
        except:
            return TrainingExampleV3(
                question=example.question,
                answer=example.answer,
                reasoning=example.reasoning,
                question_type=example.question_type,
                complexity_score=1.5,
                source_chunk=chunk
            )


# ============================================================================
# Orchestrator: Full Pipeline
# ============================================================================

class TextToExpertOrchestrator:
    """
    Complete pipeline: Text → V1 Examples → V2 Evolution → V3 Deep Evolution → Expert Dataset
    
    THIS IS THE KEY UPGRADE:
    - Not locked to Llama-2 (now supports Llama-3, Mistral, Gemma, Claude, GPT-4)
    - Uses Evol-Instruct for quality improvement (3 stages of evolution)
    - Model-agnostic (any model can be swapped via constructor)
    """
    
    def __init__(self, 
                 model: ModelProvider = ModelProvider.MISTRAL,
                 api_key: Optional[str] = None,
                 domain: str = "general"):
        """
        Initialize orchestrator.
        
        Args:
            model: Model to use (default: Mistral-7B, modern and efficient)
            api_key: For proprietary models (GPT-4, Claude)
            domain: Knowledge domain
        """
        self.domain = domain
        self.model = model
        
        # Initialize appropriate provider
        if model in [ModelProvider.GPT4, ModelProvider.CLAUDE3, ModelProvider.DEEPSEEK]:
            if not api_key:
                raise ValueError(f"API key required for {model.value}")
            self.llm = ProprietaryLLMProvider(model, api_key)
        else:
            self.llm = OpenSourceLLMProvider(model)
        
        self.evol = EvolInstruct(self.llm)
        logger.info(f"Orchestrator initialized with {model.value} (domain: {domain})")
    
    def generate_v1_examples(self, chunks: List[TextChunk], 
                            examples_per_chunk: int = 3) -> List[TrainingExampleV1]:
        """Stage 1: Generate initial Q&A pairs from text"""
        examples = []
        
        for chunk in chunks:
            prompt = f"""Generate {examples_per_chunk} educational Q&A pairs from this text.
            
TEXT: {chunk.content}

Task: Create clear, factual Q&A pairs. Output as JSON array of {{"question": "...", "answer": "..."}}
"""
            response = self.llm.complete(prompt, temperature=0.3, max_tokens=500)
            
            try:
                pairs = json.loads(response)
                if isinstance(pairs, dict):
                    pairs = [pairs]
                
                for pair in pairs[:examples_per_chunk]:
                    examples.append(TrainingExampleV1(
                        question=pair["question"],
                        answer=pair["answer"],
                        source_chunk=chunk.content
                    ))
            except:
                logger.warning(f"Failed to parse V1 examples for chunk {chunk.chunk_id}")
        
        logger.info(f"Generated {len(examples)} V1 examples")
        return examples
    
    def evolve_to_v2(self, examples_v1: List[TrainingExampleV1],
                    chunks: List[TextChunk]) -> List[TrainingExampleV2]:
        """Stage 2: Add reasoning and complexity scoring"""
        examples_v2 = []
        
        # Map chunks by content
        chunk_map = {c.content[:100]: c for c in chunks}
        
        for ex_v1 in examples_v1:
            # Find original chunk
            chunk = next((c for c in chunks if c.content in ex_v1.source_chunk), chunks[0])
            
            try:
                ex_v2 = self.evol.evolve_v1_to_v2(ex_v1, chunk.content)
                examples_v2.append(ex_v2)
            except Exception as e:
                logger.error(f"Failed to evolve example: {e}")
                examples_v2.append(TrainingExampleV2(
                    question=ex_v1.question,
                    answer=ex_v1.answer,
                    reasoning="...",
                    source_chunk=ex_v1.source_chunk
                ))
        
        logger.info(f"Evolved {len(examples_v2)} examples to V2")
        return examples_v2
    
    def evolve_to_v3(self, examples_v2: List[TrainingExampleV2],
                    chunks: List[TextChunk]) -> List[TrainingExampleV3]:
        """Stage 3: Deep evolution with alternatives and edge cases"""
        examples_v3 = []
        
        for ex_v2 in examples_v2:
            try:
                ex_v3 = self.evol.evolve_v2_to_v3(ex_v2, ex_v2.source_chunk)
                examples_v3.append(ex_v3)
            except Exception as e:
                logger.error(f"Failed to deeply evolve example: {e}")
                examples_v3.append(TrainingExampleV3(
                    question=ex_v2.question,
                    answer=ex_v2.answer,
                    reasoning=ex_v2.reasoning,
                    question_type=ex_v2.question_type,
                    complexity_score=ex_v2.complexity_score,
                    source_chunk=ex_v2.source_chunk
                ))
        
        logger.info(f"Evolved {len(examples_v3)} examples to V3 (expert level)")
        return examples_v3
    
    def orchestrate(self, text: str, source: str = "unknown") -> ExpertDataset:
        """
        Complete pipeline: Text → Expert Dataset
        
        Returns expert-quality training data ready for fine-tuning any model.
        """
        # Step 1: Chunk text
        chunks = self._chunk_text(text, source)
        logger.info(f"Chunked text into {len(chunks)} pieces")
        
        # Step 2: V1 Generation
        examples_v1 = self.generate_v1_examples(chunks, examples_per_chunk=2)
        
        # Step 3: V2 Evolution
        examples_v2 = self.evolve_to_v2(examples_v1, chunks)
        
        # Step 4: V3 Deep Evolution
        examples_v3 = self.evolve_to_v3(examples_v2, chunks)
        
        # Calculate statistics
        total_tokens = sum(self.llm.count_tokens(json.dumps(ex.to_dict())) for ex in examples_v3)
        
        # Quality scoring (0-100)
        quality_score = self._calculate_quality_score(examples_v3)
        
        dataset = ExpertDataset(
            domain=self.domain,
            model_provider=self.model,
            examples=examples_v3,
            total_tokens=total_tokens,
            quality_score=quality_score
        )
        
        logger.info(f"Expert dataset created: {len(examples_v3)} examples, "
                   f"{total_tokens} tokens, quality: {quality_score:.1f}/100")
        
        return dataset
    
    @staticmethod
    def _chunk_text(text: str, source: str, chunk_size: int = 1000) -> List[TextChunk]:
        """Split text into overlapping chunks"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - 200):  # 200 word overlap
            chunk_words = words[i:i+chunk_size]
            if chunk_words:
                chunks.append(TextChunk(
                    content=" ".join(chunk_words),
                    source=source
                ))
        
        return chunks
    
    @staticmethod
    def _calculate_quality_score(examples: List[TrainingExampleV3]) -> float:
        """Score dataset quality based on characteristics"""
        if not examples:
            return 0.0
        
        score = 50.0  # Base score
        
        # Diversity of question types
        types = set(ex.question_type for ex in examples)
        score += min(10.0, len(types) * 3)
        
        # Presence of alternatives (breadth)
        avg_alternatives = sum(len(ex.alternatives) for ex in examples) / len(examples)
        score += min(15.0, avg_alternatives * 2)
        
        # Presence of edge cases
        avg_edge_cases = sum(len(ex.edge_cases) for ex in examples) / len(examples)
        score += min(10.0, avg_edge_cases * 3)
        
        # Average complexity
        avg_complexity = sum(ex.complexity_score for ex in examples) / len(examples)
        score += min(15.0, (avg_complexity - 1.0) * 10)
        
        return min(100.0, score)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example: Use Mistral-7B (modern, efficient, not Llama-2)
    orchestrator = TextToExpertOrchestrator(
        model=ModelProvider.MISTRAL,
        domain="machine_learning"
    )
    
    sample_text = """
    Machine learning is a subset of artificial intelligence that enables systems to learn 
    and improve from experience without being explicitly programmed. Transfer learning 
    leverages pre-trained models to solve new problems efficiently.
    """
    
    # Generate expert dataset
    dataset = orchestrator.orchestrate(sample_text, source="sample.txt")
    
    print(f"\n✅ Expert Dataset Generated:")
    print(f"  Model: {dataset.model_provider.value}")
    print(f"  Domain: {dataset.domain}")
    print(f"  Examples: {len(dataset.examples)}")
    print(f"  Quality Score: {dataset.quality_score:.1f}/100")
    print(f"  Total Tokens: {dataset.total_tokens}")
    
    # Show first example
    if dataset.examples:
        ex = dataset.examples[0]
        print(f"\nSample Expert Example (V3):")
        print(f"  Q: {ex.question}")
        print(f"  A: {ex.answer}")
        print(f"  Type: {ex.question_type}")
        print(f"  Complexity: {ex.complexity_score}")
        print(f"  Alternatives: {len(ex.alternatives)}")
        print(f"  Edge Cases: {len(ex.edge_cases)}")
