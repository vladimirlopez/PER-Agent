"""
PER Agent system - Individual agent implementations.
"""

# Import base agent
from .base_agent import BaseAgent

# Import implemented agents
from .literature_scout import LiteratureScoutAgent
from .document_analyzer import DocumentAnalyzerAgent

# TODO: Import other agents as they are implemented
# from .physics_specialist import PhysicsSpecialistAgent
# from .content_synthesizer import ContentSynthesizerAgent
# from .report_generator import ReportGeneratorAgent
# from .quality_controller import QualityControllerAgent

__all__ = [
    "BaseAgent",
    "LiteratureScoutAgent",
    "DocumentAnalyzerAgent",
    # TODO: Add agent classes as they are implemented
]