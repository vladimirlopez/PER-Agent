"""
Physics Education Research (PER) Agent
A multi-agent AI system for automating physics education research.
"""

__version__ = "0.1.0"
__author__ = "PER Agent Team"
__email__ = "contact@per-agent.dev"
__description__ = "Multi-agent AI system for physics education research automation"

# Import main components
from .core.orchestrator import ResearchOrchestrator
from .core.config import Config
from .agents.literature_scout import LiteratureScoutAgent
from .agents.document_analyzer import DocumentAnalyzerAgent
from .agents.physics_specialist import PhysicsSpecialistAgent
from .agents.content_synthesizer import ContentSynthesizerAgent
from .agents.report_generator import ReportGeneratorAgent
from .agents.quality_controller import QualityControllerAgent

__all__ = [
    "ResearchOrchestrator",
    "Config",
    "LiteratureScoutAgent",
    "DocumentAnalyzerAgent", 
    "PhysicsSpecialistAgent",
    "ContentSynthesizerAgent",
    "ReportGeneratorAgent",
    "QualityControllerAgent"
]