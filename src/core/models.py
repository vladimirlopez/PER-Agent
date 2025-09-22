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
    pdf_url: Optional[str] = None  # Direct link to PDF if available
    
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
            "keywords": self.keywords,
            "pdf_url": self.pdf_url
        }


@dataclass
class AnalyzedDocument:
    """Document analysis results."""
    paper: Paper
    full_text: str  # Extracted PDF text (truncated)
    key_findings: List[str]
    methodology: Dict[str, Any]  # Methodology details from LLM analysis
    pedagogical_implications: List[str]
    limitations: List[str]
    future_work: List[str]
    relevance_score: int  # 1-10 relevance score
    summary: str  # Generated summary
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Additional fields for compatibility
    physics_concepts: List[str] = field(default_factory=list)
    educational_approaches: List[str] = field(default_factory=list)
    results_summary: str = ""  # For backward compatibility
    statistical_data: Dict[str, Any] = field(default_factory=dict)
    extraction_confidence: float = 0.0
    
    def __post_init__(self):
        """Set compatibility fields after initialization."""
        if not self.results_summary:
            self.results_summary = self.summary
        if not self.educational_approaches:
            self.educational_approaches = self.pedagogical_implications
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "paper": self.paper.to_dict(),
            "full_text": self.full_text,
            "key_findings": self.key_findings,
            "methodology": self.methodology,
            "pedagogical_implications": self.pedagogical_implications,
            "limitations": self.limitations,
            "future_work": self.future_work,
            "relevance_score": self.relevance_score,
            "summary": self.summary,
            "extraction_metadata": self.extraction_metadata,
            "physics_concepts": self.physics_concepts,
            "educational_approaches": self.educational_approaches,
            "results_summary": self.results_summary,
            "statistical_data": self.statistical_data,
            "extraction_confidence": self.extraction_confidence
        }


@dataclass
class ValidationResult:
    """Physics concept validation results."""
    document: "AnalyzedDocument"  # The document that was validated
    concept_accuracy: Dict[str, Any]  # Physics concept accuracy assessment
    mathematical_validation: Dict[str, Any]  # Mathematical validation results
    methodology_review: Dict[str, Any]  # Research methodology review
    pedagogical_assessment: Dict[str, Any]  # Educational approach assessment
    overall_validation: Dict[str, Any]  # Overall validation summary
    cross_check_results: Dict[str, Any]  # Cross-reference validation
    misconception_analysis: Dict[str, Any]  # Misconception detection results
    recommendations: List[str]  # Specific recommendations
    validation_timestamp: str  # When validation was performed
    validator_model: str  # Model used for validation
    
    # Legacy fields for backward compatibility
    concept: str = ""
    is_valid: bool = True
    confidence: float = 0.0
    explanation: str = ""
    mathematical_accuracy: float = 0.0
    physics_accuracy: float = 0.0
    suggested_corrections: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set legacy fields for backward compatibility."""
        if not self.concept:
            self.concept = self.document.paper.title
        
        overall = self.overall_validation
        if overall and "total_score" in overall:
            self.confidence = overall["total_score"] / 10.0
            self.is_valid = overall["total_score"] >= 6.0
            
        if self.concept_accuracy and "score" in self.concept_accuracy:
            self.physics_accuracy = self.concept_accuracy["score"] / 10.0
            
        if self.mathematical_validation and "score" in self.mathematical_validation:
            self.mathematical_accuracy = self.mathematical_validation["score"] / 10.0
            
        if not self.explanation:
            self.explanation = overall.get("recommendation", "Validation completed")
            
        if not self.suggested_corrections:
            self.suggested_corrections = self.recommendations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "document_title": self.document.paper.title,
            "concept_accuracy": self.concept_accuracy,
            "mathematical_validation": self.mathematical_validation,
            "methodology_review": self.methodology_review,
            "pedagogical_assessment": self.pedagogical_assessment,
            "overall_validation": self.overall_validation,
            "cross_check_results": self.cross_check_results,
            "misconception_analysis": self.misconception_analysis,
            "recommendations": self.recommendations,
            "validation_timestamp": self.validation_timestamp,
            "validator_model": self.validator_model,
            # Legacy fields
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
    final_validation_complete: bool = False
    quality_certified: bool = False
    
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


@dataclass
class ResearchReport:
    """Final research report with multiple formats."""
    query: ResearchQuery
    executive_summary: str
    literature_review: str
    key_findings: str
    recommendations: str
    conclusion: str
    bibliography: str
    metadata: Dict[str, Any]
    file_paths: Dict[str, str]  # format -> file_path mapping
    quality_score: float
    generation_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query.to_dict(),
            "executive_summary": self.executive_summary,
            "literature_review": self.literature_review,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "conclusion": self.conclusion,
            "bibliography": self.bibliography,
            "metadata": self.metadata,
            "file_paths": self.file_paths,
            "quality_score": self.quality_score,
            "generation_timestamp": self.generation_timestamp.isoformat()
        }


@dataclass
class QualityAssessment:
    """Quality assessment results from Quality Controller Agent."""
    overall_score: float
    component_scores: Dict[str, float]
    validation_results: Dict[str, Any]
    recommendations: List[str]
    assessment_timestamp: datetime
    quality_level: str  # EXCELLENT, VERY_GOOD, GOOD, SATISFACTORY, NEEDS_IMPROVEMENT, POOR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "component_scores": self.component_scores,
            "validation_results": self.validation_results,
            "recommendations": self.recommendations,
            "assessment_timestamp": self.assessment_timestamp.isoformat(),
            "quality_level": self.quality_level
        }