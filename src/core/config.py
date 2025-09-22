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
        """Initialize default model configurations."""
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
            "phi4": ModelConfig(
                name="Phi-4",
                model_id="phi4:latest",
                vram_usage=9,
                context_length=16000
            ),
            "mistral_7b": ModelConfig(
                name="Mistral-7B",
                model_id="mistral:7b",
                vram_usage=4,
                context_length=32000
            ),
            "llama_8b": ModelConfig(
                name="Llama-3.1-8B",
                model_id="llama3.1:8b",
                vram_usage=5,
                context_length=128000
            )
        }
    
    def _init_default_agents(self) -> Dict[str, AgentConfig]:
        """Initialize default agent configurations."""
        return {
            "literature_scout": AgentConfig(
                name="Literature Scout",
                model=self.models["qwen_coder_14b"],
                role="Search and rank academic papers",
                capabilities=["arxiv_search", "semantic_scholar", "ranking"]
            ),
            "document_analyzer": AgentConfig(
                name="Document Analyzer", 
                model=self.models["deepseek_14b"],
                role="Parse PDFs and extract key findings",
                capabilities=["pdf_parsing", "text_extraction", "summarization"]
            ),
            "physics_specialist": AgentConfig(
                name="Physics Specialist",
                model=self.models["phi4"],
                role="Validate physics concepts and mathematics",
                capabilities=["physics_validation", "math_checking", "concept_verification"]
            ),
            "content_synthesizer": AgentConfig(
                name="Content Synthesizer",
                model=self.models["deepseek_14b"],
                role="Combine insights and identify patterns",
                capabilities=["synthesis", "pattern_recognition", "contradiction_detection"]
            ),
            "report_generator": AgentConfig(
                name="Report Generator",
                model=self.models["qwen_coder_14b"],
                role="Generate formatted academic reports",
                capabilities=["latex_generation", "markdown_formatting", "pdf_creation"]
            ),
            "quality_controller": AgentConfig(
                name="Quality Controller",
                model=self.models["deepseek_14b"],
                role="Review outputs for accuracy and standards",
                capabilities=["quality_assessment", "accuracy_validation", "standard_compliance"]
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
    
    def validate_system_requirements(self) -> bool:
        """Validate that system meets requirements for configured models."""
        total_vram_needed = max(model.vram_usage for model in self.models.values())
        
        # Check if RTX 5070 Ti (16GB) can handle the largest model
        if total_vram_needed > 16:
            print(f"Warning: Largest model requires {total_vram_needed}GB VRAM, but system has 16GB")
            return False
            
        return True