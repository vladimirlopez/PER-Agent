"""
Configuration management for PER Agent system.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class ModelConfig:
    """Configuration for individual LLM models."""
    name: str
    model_id: str
    vram_usage: int  # in GB
    context_length: int
    quantization: str = "Q4_K_M"
    temperature: float = 0.1
    max_tokens: int = 4096


@dataclass
class AgentConfig:
    """Configuration for individual agents."""
    name: str
    model: ModelConfig
    role: str
    capabilities: List[str]
    max_retries: int = 3
    timeout: int = 300  # seconds


@dataclass
class APIConfig:
    """Configuration for external APIs."""
    arxiv_base_url: str = "http://export.arxiv.org/api/query"
    semantic_scholar_url: str = "https://api.semanticscholar.org/graph/v1"
    google_scholar_enabled: bool = True
    rate_limit_delay: float = 1.0  # seconds between requests


@dataclass
class Config:
    """Main configuration class for PER Agent system."""
    
    # System settings
    project_root: Path = Path(__file__).parent.parent.parent
    logs_dir: Path = project_root / "logs"
    cache_dir: Path = project_root / "cache"
    outputs_dir: Path = project_root / "research_outputs"
    
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_timeout: int = 600
    # Prefer GPU variants for models when available (try GPU first, fall back to CPU)
    prefer_gpu: bool = True
    
    # Model configurations
    models: Dict[str, ModelConfig] = None
    
    # Agent configurations
    agents: Dict[str, AgentConfig] = None
    
    # API configurations
    apis: APIConfig = None
    
    # LangGraph settings
    workflow_timeout: int = 1800  # 30 minutes
    max_workflow_retries: int = 2
    checkpoint_enabled: bool = True
    
    # Quality settings
    min_quality_score: float = 0.8
    max_sources_per_query: int = 20
    min_sources_per_report: int = 5
    
    def __post_init__(self):
        """Initialize default configurations."""
        if self.models is None:
            self.models = self._init_default_models()
        
        if self.agents is None:
            self.agents = self._init_default_agents()
            
        if self.apis is None:
            self.apis = APIConfig()
            
        # Create directories
        self.logs_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        self.outputs_dir.mkdir(exist_ok=True)
    
    def _init_default_models(self) -> Dict[str, ModelConfig]:
        """Initialize default model configurations optimized for 16GB VRAM."""
        return {
            "qwen_coder_14b": ModelConfig(
                name="Qwen2.5-Coder-14B",
                model_id="qwen2.5-coder:14b",
                vram_usage=9,
                context_length=32000
            ),
            "deepseek_14b": ModelConfig(
                name="DeepSeek-R1-14B", 
                model_id="deepseek-r1:14b",
                vram_usage=9,
                context_length=64000
            ),
            "deepseek_8b": ModelConfig(
                name="DeepSeek-R1-8B",
                model_id="deepseek-r1:8b", 
                vram_usage=5,
                context_length=64000
            ),
            "phi4": ModelConfig(
                name="Phi-4",
                model_id="phi4:latest",
                vram_usage=9,
                context_length=16000
            ),
            "mistral_7b_gpu": ModelConfig(
                name="Mistral-7B-GPU",
                model_id="mistral:7b-gpu",
                vram_usage=4,
                context_length=32000
            ),
            "pixtral_12b": ModelConfig(
                name="Pixtral-12B",
                model_id="pixtral:12b",
                vram_usage=8,
                context_length=16000
            ),
            "qwen_coder_32b": ModelConfig(
                name="Qwen2.5-Coder-32B-Instruct",
                model_id="qwen2.5-coder:32b-instruct-q4_K_M",
                vram_usage=19,
                context_length=32000
            )
        }
    
    def _init_default_agents(self) -> Dict[str, AgentConfig]:
        """Initialize default agent configurations optimized for 16GB VRAM."""
        return {
            "literature_scout": AgentConfig(
                name="Literature Scout",
                model=self.models["qwen_coder_14b"],  # Use 14B for VRAM efficiency, 32B as alternate
                role="Search and rank academic papers",
                capabilities=["arxiv_search", "semantic_scholar", "ranking"],
                max_retries=3,
                timeout=300
            ),
            "document_analyzer": AgentConfig(
                name="Document Analyzer", 
                model=self.models["qwen_coder_14b"],  # Use 14B, can fall back to 32B if needed
                role="Parse PDFs and extract key findings",
                capabilities=["pdf_parsing", "text_extraction", "summarization"],
                max_retries=3,
                timeout=300
            ),
            "physics_specialist": AgentConfig(
                name="Physics Specialist",
                model=self.models["deepseek_14b"],  # Primary: deepseek-r1:14b
                role="Validate physics concepts and mathematics",
                capabilities=["physics_validation", "math_checking", "concept_verification"],
                max_retries=3,
                timeout=300
            ),
            "content_synthesizer": AgentConfig(
                name="Content Synthesizer",
                model=self.models["deepseek_14b"],  # Primary: deepseek-r1:14b
                role="Combine insights and identify patterns",
                capabilities=["synthesis", "pattern_recognition", "contradiction_detection"],
                max_retries=3,
                timeout=300
            ),
            "report_generator": AgentConfig(
                name="Report Generator",
                model=self.models["qwen_coder_14b"],  # Primary: qwen2.5-coder:14b
                role="Generate formatted academic reports",
                capabilities=["latex_generation", "markdown_formatting", "pdf_creation"],
                max_retries=3,
                timeout=300
            ),
            "quality_controller": AgentConfig(
                name="Quality Controller",
                model=self.models["deepseek_14b"],  # Primary: deepseek-r1:14b
                role="Review outputs for accuracy and standards",
                capabilities=["quality_assessment", "accuracy_validation", "standard_compliance"],
                max_retries=3,
                timeout=300
            )
        }
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables if present
        if os.getenv("OLLAMA_HOST"):
            config.ollama_host = os.getenv("OLLAMA_HOST")
            
        if os.getenv("MIN_QUALITY_SCORE"):
            config.min_quality_score = float(os.getenv("MIN_QUALITY_SCORE"))
            
        if os.getenv("MAX_SOURCES"):
            config.max_sources_per_query = int(os.getenv("MAX_SOURCES"))

        # Prefer GPU flag (env var defaults to True unless explicitly set to '0' or 'false')
        if os.getenv("OLLAMA_PREFER_GPU"):
            val = os.getenv("OLLAMA_PREFER_GPU").lower()
            config.prefer_gpu = not (val in ("0", "false", "no"))
            
        return config
    
    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found in configuration")
        return self.models[model_name]
    
    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """Get configuration for a specific agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent '{agent_name}' not found in configuration")
        return self.agents[agent_name]
    
    def get_alternate_model_for_agent(self, agent_name: str) -> Optional[ModelConfig]:
        """Get alternate model configuration for an agent if primary fails."""
        alternates = {
            "literature_scout": "deepseek_14b",      # From qwen_coder_14b to deepseek_14b
            "document_analyzer": "phi4",             # From qwen_coder_14b to phi4
            "physics_specialist": "qwen_coder_14b",  # From deepseek_14b to qwen_coder_14b
            "content_synthesizer": "mistral_7b_gpu", # From deepseek_14b to mistral_7b_gpu
            "report_generator": "deepseek_14b",      # From qwen_coder_14b to deepseek_14b
            "quality_controller": "qwen_coder_14b"   # From deepseek_14b to qwen_coder_14b
        }
        
        alternate_key = alternates.get(agent_name)
        if alternate_key and alternate_key in self.models:
            return self.models[alternate_key]
        return None

    def find_gpu_variant(self, model: ModelConfig) -> Optional[ModelConfig]:
        """Try to find a GPU-optimized variant of the supplied model in the registry.

        Heuristic used:
        - Prefer models whose model_id or name contains 'gpu'
        - Prefer models that share the same base provider name (e.g. 'mistral', 'qwen')
        - Return the first reasonable match
        """
        base_keyword = model.model_id.split(":")[0].lower()
        # Search for models that indicate GPU usage
        for m in self.models.values():
            mid = (m.model_id or "").lower()
            mname = (m.name or "").lower()
            if "gpu" in mid or "-gpu" in mid or "gpu" in mname:
                if base_keyword in mid or base_keyword in mname:
                    return m

        # If no clear GPU-labeled variant found, try any model with 'gpu' in name/id
        for m in self.models.values():
            mid = (m.model_id or "").lower()
            mname = (m.name or "").lower()
            if "gpu" in mid or "gpu" in mname:
                return m

        return None
    
    def validate_system_requirements(self) -> bool:
        """Validate that system meets requirements for configured models."""
        total_vram_needed = max(model.vram_usage for model in self.models.values())
        
        # Check if RTX 5070 Ti (16GB) can handle the largest model
        if total_vram_needed > 16:
            print(f"Warning: Largest model requires {total_vram_needed}GB VRAM, but RTX 5070 Ti has 16GB")
            print(f"Recommendation: Use alternate models or enable model offloading")
            return False
            
        return True
    
    def get_vram_efficient_models(self) -> Dict[str, ModelConfig]:
        """Get models that fit within 16GB VRAM limit."""
        return {name: model for name, model in self.models.items() 
                if model.vram_usage <= 16}
    
    def recommend_model_for_agent(self, agent_name: str, max_vram: int = 16) -> ModelConfig:
        """Recommend the best model for an agent within VRAM constraints."""
        agent_config = self.get_agent_config(agent_name)
        primary_model = agent_config.model
        
        # If primary model fits, use it
        if primary_model.vram_usage <= max_vram:
            return primary_model
            
        # Otherwise, get the alternate
        alternate = self.get_alternate_model_for_agent(agent_name)
        if alternate and alternate.vram_usage <= max_vram:
            return alternate
            
        # Fallback to smallest available model
        efficient_models = self.get_vram_efficient_models()
        if efficient_models:
            return min(efficient_models.values(), key=lambda m: m.vram_usage)
            
        raise ValueError(f"No suitable model found for agent {agent_name} within {max_vram}GB VRAM")