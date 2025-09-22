"""
Data models for the PER Agent system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class ResearchDomain(Enum):
    """Available research domains."""
    PHYSICS_EDUCATION = "physics_education"
    GENERAL_PHYSICS = "general_physics"
    EDUCATION_TECHNOLOGY = "education_technology"
    PEDAGOGY = "pedagogy"


class ReportFormat(Enum):
    """Available report output formats."""
    MARKDOWN = "markdown"
    LATEX = "latex"
    PDF = "pdf"
    HTML = "html"


@dataclass
class ResearchQuery:
    """Research query submitted by user."""
    question: str
    domain: ResearchDomain = ResearchDomain.PHYSICS_EDUCATION
    max_sources: int = 20
    min_sources: int = 5
    preferred_years: Optional[tuple] = None  # (start_year, end_year)
    keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    report_format: ReportFormat = ReportFormat.MARKDOWN
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: str = field(default_factory=lambda: f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "question": self.question,
            "domain": self.domain.value,
            "max_sources": self.max_sources,
            "min_sources": self.min_sources,
            "preferred_years": self.preferred_years,
            "keywords": self.keywords,
            "exclude_keywords": self.exclude_keywords,
            "report_format": self.report_format.value,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id
        }


@dataclass
class Paper:
    """Individual research paper metadata."""
    title: str
    authors: List[str]
    abstract: str
    url: str
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    published_date: Optional[datetime] = None
    journal: Optional[str] = None
    citations: int = 0
    relevance_score: float = 0.0
    source: str = "unknown"  # arxiv, semantic_scholar, google_scholar
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "url": self.url,
            "arxiv_id": self.arxiv_id,
            "doi": self.doi,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "journal": self.journal,
            "citations": self.citations,
            "relevance_score": self.relevance_score,
            "source": self.source,
            "keywords": self.keywords
        }


@dataclass
class AnalyzedDocument:
    """Document analysis results."""
    paper: Paper
    key_findings: List[str]
    methodology: str
    results_summary: str
    limitations: List[str]
    physics_concepts: List[str]
    educational_approaches: List[str]
    statistical_data: Dict[str, Any] = field(default_factory=dict)
    extraction_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "paper": self.paper.to_dict(),
            "key_findings": self.key_findings,
            "methodology": self.methodology,
            "results_summary": self.results_summary,
            "limitations": self.limitations,
            "physics_concepts": self.physics_concepts,
            "educational_approaches": self.educational_approaches,
            "statistical_data": self.statistical_data,
            "extraction_confidence": self.extraction_confidence
        }


@dataclass
class ValidationResult:
    """Physics concept validation results."""
    concept: str
    is_valid: bool
    confidence: float
    explanation: str
    mathematical_accuracy: float
    physics_accuracy: float
    suggested_corrections: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "concept": self.concept,
            "is_valid": self.is_valid,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "mathematical_accuracy": self.mathematical_accuracy,
            "physics_accuracy": self.physics_accuracy,
            "suggested_corrections": self.suggested_corrections
        }


@dataclass
class SynthesisInsight:
    """Content synthesis insight."""
    insight_type: str  # pattern, contradiction, gap, trend
    description: str
    supporting_evidence: List[str]
    confidence: float
    related_papers: List[str]  # paper titles or IDs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "insight_type": self.insight_type,
            "description": self.description,
            "supporting_evidence": self.supporting_evidence,
            "confidence": self.confidence,
            "related_papers": self.related_papers
        }


@dataclass
class GeneratedReport:
    """Generated research report."""
    title: str
    executive_summary: str
    methodology: str
    findings: str
    conclusions: str
    recommendations: str
    references: str
    content: str  # Full formatted content
    format: ReportFormat
    word_count: int
    generation_time: timedelta
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "executive_summary": self.executive_summary,
            "methodology": self.methodology,
            "findings": self.findings,
            "conclusions": self.conclusions,
            "recommendations": self.recommendations,
            "references": self.references,
            "content": self.content,
            "format": self.format.value,
            "word_count": self.word_count,
            "generation_time": str(self.generation_time)
        }


@dataclass
class QualityAssessment:
    """Quality assessment results."""
    overall_score: float  # 0.0 to 1.0
    accuracy_score: float
    completeness_score: float
    coherence_score: float
    academic_standards_score: float
    feedback: List[str]
    suggestions: List[str]
    passed_quality_check: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "accuracy_score": self.accuracy_score,
            "completeness_score": self.completeness_score,
            "coherence_score": self.coherence_score,
            "academic_standards_score": self.academic_standards_score,
            "feedback": self.feedback,
            "suggestions": self.suggestions,
            "passed_quality_check": self.passed_quality_check
        }


@dataclass
class AgentState:
    """State object for LangGraph workflow."""
    query: ResearchQuery
    current_step: str
    
    # Literature search results
    literature_results: List[Paper] = field(default_factory=list)
    
    # Document analysis results
    analyzed_documents: List[AnalyzedDocument] = field(default_factory=list)
    
    # Physics validation results
    validation_results: List[ValidationResult] = field(default_factory=list)
    
    # Content synthesis results
    synthesis_insights: List[SynthesisInsight] = field(default_factory=list)
    synthesized_content: Dict[str, Any] = field(default_factory=dict)
    
    # Report generation results
    generated_report: Optional[GeneratedReport] = None
    
    # Quality control results
    quality_assessment: Optional[QualityAssessment] = None
    
    # Workflow management
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    revision_count: int = 0
    processing_start_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query.to_dict(),
            "current_step": self.current_step,
            "literature_results": [p.to_dict() for p in self.literature_results],
            "analyzed_documents": [d.to_dict() for d in self.analyzed_documents],
            "validation_results": [v.to_dict() for v in self.validation_results],
            "synthesis_insights": [s.to_dict() for s in self.synthesis_insights],
            "synthesized_content": self.synthesized_content,
            "generated_report": self.generated_report.to_dict() if self.generated_report else None,
            "quality_assessment": self.quality_assessment.to_dict() if self.quality_assessment else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "revision_count": self.revision_count,
            "processing_start_time": self.processing_start_time.isoformat()
        }


@dataclass
class ResearchResult:
    """Final research result."""
    query: ResearchQuery
    literature_sources: List[Paper]
    analyzed_documents: List[AnalyzedDocument]
    validation_results: List[ValidationResult]
    synthesis_insights: List[SynthesisInsight]
    generated_report: Optional[GeneratedReport]
    quality_assessment: Optional[QualityAssessment]
    processing_time: timedelta
    total_sources_found: int = 0
    total_sources_analyzed: int = 0
    quality_score: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query.to_dict(),
            "literature_sources": [p.to_dict() for p in self.literature_sources],
            "analyzed_documents": [d.to_dict() for d in self.analyzed_documents],
            "validation_results": [v.to_dict() for v in self.validation_results],
            "synthesis_insights": [s.to_dict() for s in self.synthesis_insights],
            "generated_report": self.generated_report.to_dict() if self.generated_report else None,
            "quality_assessment": self.quality_assessment.to_dict() if self.quality_assessment else None,
            "processing_time": str(self.processing_time),
            "total_sources_found": self.total_sources_found,
            "total_sources_analyzed": self.total_sources_analyzed,
            "quality_score": self.quality_score,
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def get_summary(self) -> str:
        """Get a brief summary of the research results."""
        return f"""
Research Summary:
- Query: {self.query.question}
- Sources Found: {self.total_sources_found}
- Sources Analyzed: {self.total_sources_analyzed}
- Quality Score: {self.quality_score:.2f}
- Processing Time: {self.processing_time}
- Insights Generated: {len(self.synthesis_insights)}
- Report Generated: {'Yes' if self.generated_report else 'No'}
"""