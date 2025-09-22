"""
Quality Controller Agent - Final validation and quality assurance for research output.
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from langchain_core.prompts import PromptTemplate

from .base_agent import BaseAgent
from core.models import AgentState, ResearchReport, QualityAssessment
from core.config import AgentConfig


class QualityControllerAgent(BaseAgent):
    """
    Agent responsible for final quality control, validation, and assessment of research output.
    
    Capabilities:
    - Comprehensive quality assessment of all research components
    - Cross-validation of findings across agents
    - Report completeness and accuracy verification
    - Citation and reference validation
    - Methodological rigor assessment
    - Final recommendations and improvements
    - Overall quality scoring and certification
    - Error detection and correction suggestions
    """
    
    def __init__(self, config: AgentConfig, ollama_host: str = "http://localhost:11434"):
        """Initialize Quality Controller Agent with advanced reasoning model."""
        super().__init__(config, ollama_host)
        self.agent_name = "Quality Controller"
        self.logger.info("Quality Controller Agent initialized successfully")
    
    def _initialize_prompts(self) -> Dict[str, PromptTemplate]:
        """Initialize prompt templates for quality assessment."""
        return {
            "quality_assessment": PromptTemplate.from_template("""
            You are an expert research quality assessor in physics education. 
            Evaluate the overall quality of this research analysis and provide scores (0-10) for each component.
            
            Research Question: {research_question}
            Literature Sources: {literature_summary}
            Analysis Results: {analysis_summary}
            
            Provide your assessment as JSON with component scores and recommendations.
            """),
            
            "cross_validation": PromptTemplate.from_template("""
            Validate the consistency and coherence of findings across multiple research agents.
            
            Analysis Findings: {analysis_findings}
            Physics Results: {physics_results}
            Synthesis Insights: {synthesis_insights}
            
            Identify consistency, contradictions, gaps, and confidence level.
            """)
        }
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Perform comprehensive quality control and final validation.
        
        Args:
            state: Current agent state with all previous agent outputs
            
        Returns:
            Updated state with quality assessment and final validation
        """
        self.logger.info("Starting comprehensive quality control assessment...")
        
        try:
            # Perform comprehensive quality assessment
            quality_assessment = await self._assess_overall_quality(state)
            
            # Cross-validate findings between agents
            cross_validation = await self._cross_validate_findings(state)
            
            # Validate citations and references
            citation_validation = await self._validate_citations(state)
            
            # Assess methodological rigor
            methodology_assessment = await self._assess_methodology(state)
            
            # Check report completeness
            completeness_check = await self._check_completeness(state)
            
            # Generate final recommendations
            final_recommendations = await self._generate_final_recommendations(state, quality_assessment)
            
            # Calculate final quality score
            final_score = await self._calculate_final_score(
                quality_assessment, cross_validation, citation_validation, 
                methodology_assessment, completeness_check
            )
            
            # Create comprehensive quality assessment
            state.quality_assessment = QualityAssessment(
                overall_score=final_score,
                component_scores={
                    "literature_quality": quality_assessment.get("literature_score", 0.0),
                    "analysis_rigor": quality_assessment.get("analysis_score", 0.0),
                    "physics_accuracy": quality_assessment.get("physics_score", 0.0),
                    "synthesis_depth": quality_assessment.get("synthesis_score", 0.0),
                    "report_quality": quality_assessment.get("report_score", 0.0),
                    "citation_accuracy": citation_validation.get("score", 0.0),
                    "methodology_rigor": methodology_assessment.get("score", 0.0),
                    "completeness": completeness_check.get("score", 0.0)
                },
                validation_results=cross_validation,
                recommendations=final_recommendations,
                assessment_timestamp=datetime.now(),
                quality_level=self._determine_quality_level(final_score)
            )
            
            # Update state with final results
            state.final_validation_complete = True
            state.quality_certified = final_score >= 7.0  # Certification threshold
            state.current_step = "quality_control_complete"
            
            self.logger.info(f"Quality control completed. Final score: {final_score:.2f}/10.0")
            self.logger.info(f"Quality level: {state.quality_assessment.quality_level}")
            
        except Exception as e:
            self.logger.error(f"Quality control failed: {e}")
            state.errors.append(f"Quality control error: {e}")
            # Create minimal quality assessment
            state.quality_assessment = QualityAssessment(
                overall_score=0.0,
                component_scores={},
                validation_results={"status": "failed", "error": str(e)},
                recommendations=["Quality control failed - manual review required"],
                assessment_timestamp=datetime.now(),
                quality_level="FAILED"
            )
        
        return state
    
    async def _assess_overall_quality(self, state: AgentState) -> Dict[str, Any]:
        """Assess overall quality of research components."""
        
        prompt = PromptTemplate.from_template("""
        You are an expert research quality assessor in physics education. Evaluate the overall quality of this research analysis.

        RESEARCH QUESTION: {research_question}

        LITERATURE SOURCES ({num_sources} papers):
        {literature_summary}

        DOCUMENT ANALYSIS RESULTS:
        {analysis_summary}

        PHYSICS VALIDATION RESULTS:
        {physics_validation}

        SYNTHESIS INSIGHTS:
        {synthesis_summary}

        GENERATED REPORT:
        {report_summary}

        Please provide a comprehensive quality assessment with scores (0-10) for each component:

        1. LITERATURE QUALITY ASSESSMENT:
        - Relevance and authority of sources
        - Coverage of the research question
        - Recency and significance of papers
        - Diversity of perspectives

        2. ANALYSIS RIGOR ASSESSMENT:
        - Depth of document analysis
        - Accuracy of content extraction
        - Completeness of findings

        3. PHYSICS ACCURACY ASSESSMENT:
        - Correctness of physics concepts
        - Accuracy of educational principles
        - Validity of pedagogical claims

        4. SYNTHESIS DEPTH ASSESSMENT:
        - Quality of cross-study analysis
        - Insight generation and patterns
        - Identification of research gaps

        5. REPORT QUALITY ASSESSMENT:
        - Professional presentation
        - Clear structure and flow
        - Comprehensive coverage

        Provide your assessment as JSON:
        {{
            "literature_score": <0-10>,
            "analysis_score": <0-10>,
            "physics_score": <0-10>,
            "synthesis_score": <0-10>,
            "report_score": <0-10>,
            "overall_assessment": "<detailed evaluation>",
            "strengths": ["<strength1>", "<strength2>"],
            "weaknesses": ["<weakness1>", "<weakness2>"],
            "critical_issues": ["<issue1>", "<issue2>"]
        }}
        """)
        
        # Prepare data for assessment
        literature_summary = self._summarize_literature(state)
        analysis_summary = self._summarize_analysis(state)
        physics_validation = self._summarize_physics_validation(state)
        synthesis_summary = self._summarize_synthesis(state)
        report_summary = self._summarize_report(state)
        
        num_sources = len(state.literature_results) if hasattr(state, 'literature_results') else 0
        
        formatted_prompt = prompt.format(
            research_question=state.query.question,
            num_sources=num_sources,
            literature_summary=literature_summary,
            analysis_summary=analysis_summary,
            physics_validation=physics_validation,
            synthesis_summary=synthesis_summary,
            report_summary=report_summary
        )
        
        response = await self.llm.ainvoke(formatted_prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                self.logger.warning("Could not extract JSON from quality assessment response")
                return self._create_default_quality_assessment()
        except json.JSONDecodeError:
            self.logger.error("Failed to parse quality assessment JSON")
            return self._create_default_quality_assessment()
    
    async def _cross_validate_findings(self, state: AgentState) -> Dict[str, Any]:
        """Cross-validate findings between different agents."""
        
        prompt = PromptTemplate.from_template("""
        You are validating the consistency and coherence of findings across multiple research agents.

        DOCUMENT ANALYSIS FINDINGS:
        {analysis_findings}

        PHYSICS VALIDATION RESULTS:
        {physics_results}

        SYNTHESIS INSIGHTS:
        {synthesis_insights}

        Please identify:
        1. CONSISTENCY: Do findings align across agents?
        2. CONTRADICTIONS: Any conflicting information?
        3. GAPS: Missing connections or validations?
        4. CONFIDENCE: How reliable are the overall findings?

        Provide validation results as JSON:
        {{
            "consistency_score": <0-10>,
            "contradiction_count": <number>,
            "identified_contradictions": ["<contradiction1>", "<contradiction2>"],
            "gaps_identified": ["<gap1>", "<gap2>"],
            "confidence_level": "<high/medium/low>",
            "validation_summary": "<overall assessment>",
            "recommendations": ["<rec1>", "<rec2>"]
        }}
        """)
        
        # Prepare findings summaries
        analysis_findings = self._extract_analysis_findings(state)
        physics_results = self._extract_physics_results(state)
        synthesis_insights = self._extract_synthesis_insights(state)
        
        formatted_prompt = prompt.format(
            analysis_findings=analysis_findings,
            physics_results=physics_results,
            synthesis_insights=synthesis_insights
        )
        
        response = await self.llm.ainvoke(formatted_prompt)
        
        try:
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"status": "validation_failed", "error": "Could not parse response"}
        except json.JSONDecodeError:
            return {"status": "validation_failed", "error": "JSON parsing error"}
    
    async def _validate_citations(self, state: AgentState) -> Dict[str, Any]:
        """Validate citations and references for accuracy."""
        
        if not hasattr(state, 'literature_results') or not state.literature_results:
            return {"score": 0.0, "message": "No citations to validate"}
        
        # Count valid citations
        valid_citations = 0
        total_citations = len(state.literature_results)
        citation_issues = []
        
        for paper in state.literature_results:
            # Check for required citation elements
            has_title = bool(paper.title and paper.title.strip())
            has_authors = bool(paper.authors)
            has_year = bool(paper.year)
            
            if has_title and has_authors and has_year:
                valid_citations += 1
            else:
                issues = []
                if not has_title: issues.append("missing title")
                if not has_authors: issues.append("missing authors")
                if not has_year: issues.append("missing year")
                citation_issues.append(f"{paper.title[:50]}...: {', '.join(issues)}")
        
        score = (valid_citations / total_citations) * 10.0 if total_citations > 0 else 0.0
        
        return {
            "score": score,
            "valid_citations": valid_citations,
            "total_citations": total_citations,
            "citation_issues": citation_issues,
            "validation_summary": f"{valid_citations}/{total_citations} citations properly formatted"
        }
    
    async def _assess_methodology(self, state: AgentState) -> Dict[str, Any]:
        """Assess methodological rigor of the research process."""
        
        # Evaluate methodology based on process completeness
        methodology_score = 0.0
        methodology_notes = []
        
        # Check if literature search was comprehensive
        if hasattr(state, 'literature_results') and len(state.literature_results) >= 3:
            methodology_score += 2.0
            methodology_notes.append("Adequate literature coverage")
        elif hasattr(state, 'literature_results') and len(state.literature_results) > 0:
            methodology_score += 1.0
            methodology_notes.append("Limited literature coverage")
        else:
            methodology_notes.append("Insufficient literature coverage")
        
        # Check document analysis quality
        if hasattr(state, 'analyzed_documents') and state.analyzed_documents:
            methodology_score += 2.0
            methodology_notes.append("Document analysis performed")
        else:
            methodology_notes.append("No document analysis performed")
        
        # Check physics validation
        if hasattr(state, 'validation_results') and state.validation_results:
            methodology_score += 2.0
            methodology_notes.append("Physics validation completed")
        else:
            methodology_notes.append("No physics validation")
        
        # Check synthesis quality
        if hasattr(state, 'synthesis_insights') and state.synthesis_insights:
            methodology_score += 2.0
            methodology_notes.append("Cross-study synthesis performed")
        else:
            methodology_notes.append("No synthesis performed")
        
        # Check report generation
        if hasattr(state, 'generated_report') and state.generated_report:
            methodology_score += 2.0
            methodology_notes.append("Professional report generated")
        else:
            methodology_notes.append("No report generated")
        
        return {
            "score": methodology_score,
            "max_score": 10.0,
            "methodology_notes": methodology_notes,
            "rigor_assessment": "High" if methodology_score >= 8.0 else "Medium" if methodology_score >= 5.0 else "Low"
        }
    
    async def _check_completeness(self, state: AgentState) -> Dict[str, Any]:
        """Check completeness of the research process."""
        
        completeness_items = [
            ("research_question", hasattr(state, 'query') and state.query.question),
            ("literature_search", hasattr(state, 'literature_results') and state.literature_results),
            ("document_analysis", hasattr(state, 'analyzed_documents') and state.analyzed_documents),
            ("physics_validation", hasattr(state, 'validation_results') and state.validation_results),
            ("content_synthesis", hasattr(state, 'synthesis_insights') and state.synthesis_insights),
            ("report_generation", hasattr(state, 'generated_report') and state.generated_report)
        ]
        
        completed_items = sum(1 for _, completed in completeness_items if completed)
        total_items = len(completeness_items)
        
        completeness_score = (completed_items / total_items) * 10.0
        
        missing_items = [item for item, completed in completeness_items if not completed]
        
        return {
            "score": completeness_score,
            "completed_items": completed_items,
            "total_items": total_items,
            "missing_items": missing_items,
            "completeness_percentage": (completed_items / total_items) * 100
        }
    
    async def _generate_final_recommendations(self, state: AgentState, quality_assessment: Dict[str, Any]) -> List[str]:
        """Generate final recommendations for improvement."""
        
        recommendations = []
        
        # Add recommendations based on quality scores
        if quality_assessment.get("literature_score", 0) < 7.0:
            recommendations.append("Expand literature search to include more recent and diverse sources")
        
        if quality_assessment.get("analysis_score", 0) < 7.0:
            recommendations.append("Improve document analysis depth and extraction accuracy")
        
        if quality_assessment.get("physics_score", 0) < 7.0:
            recommendations.append("Enhance physics concept validation and accuracy checking")
        
        if quality_assessment.get("synthesis_score", 0) < 7.0:
            recommendations.append("Strengthen cross-study analysis and pattern identification")
        
        if quality_assessment.get("report_score", 0) < 7.0:
            recommendations.append("Improve report structure, clarity, and professional presentation")
        
        # Add specific recommendations from quality assessment
        if "recommendations" in quality_assessment:
            recommendations.extend(quality_assessment["recommendations"])
        
        return recommendations
    
    async def _calculate_final_score(self, quality_assessment: Dict[str, Any], 
                                   cross_validation: Dict[str, Any],
                                   citation_validation: Dict[str, Any],
                                   methodology_assessment: Dict[str, Any],
                                   completeness_check: Dict[str, Any]) -> float:
        """Calculate final quality score."""
        
        # Weight different components
        weights = {
            "quality": 0.3,
            "cross_validation": 0.2,
            "citations": 0.1,
            "methodology": 0.2,
            "completeness": 0.2
        }
        
        # Get scores
        quality_score = sum([
            quality_assessment.get("literature_score", 0),
            quality_assessment.get("analysis_score", 0),
            quality_assessment.get("physics_score", 0),
            quality_assessment.get("synthesis_score", 0),
            quality_assessment.get("report_score", 0)
        ]) / 5.0
        
        cross_val_score = cross_validation.get("consistency_score", 0.0)
        citation_score = citation_validation.get("score", 0.0)
        methodology_score = methodology_assessment.get("score", 0.0)
        completeness_score = completeness_check.get("score", 0.0)
        
        # Calculate weighted final score
        final_score = (
            quality_score * weights["quality"] +
            cross_val_score * weights["cross_validation"] +
            citation_score * weights["citations"] +
            methodology_score * weights["methodology"] +
            completeness_score * weights["completeness"]
        )
        
        return round(final_score, 2)
    
    def _determine_quality_level(self, score: float) -> str:
        """Determine quality level based on score."""
        if score >= 9.0:
            return "EXCELLENT"
        elif score >= 8.0:
            return "VERY_GOOD"
        elif score >= 7.0:
            return "GOOD"
        elif score >= 6.0:
            return "SATISFACTORY"
        elif score >= 4.0:
            return "NEEDS_IMPROVEMENT"
        else:
            return "POOR"
    
    # Helper methods for data extraction and summarization
    def _summarize_literature(self, state: AgentState) -> str:
        """Summarize literature sources."""
        if not hasattr(state, 'literature_results') or not state.literature_results:
            return "No literature sources found"
        
        summaries = []
        for paper in state.literature_results[:5]:  # Top 5 papers
            summary = f"- {paper.title} ({paper.year}) - Score: {paper.relevance_score:.2f}"
            summaries.append(summary)
        
        if len(state.literature_results) > 5:
            summaries.append(f"... and {len(state.literature_results) - 5} more papers")
        
        return "\n".join(summaries)
    
    def _summarize_analysis(self, state: AgentState) -> str:
        """Summarize document analysis results."""
        if not hasattr(state, 'analyzed_documents') or not state.analyzed_documents:
            return "No document analysis performed"
        
        return f"Analyzed {len(state.analyzed_documents)} documents with comprehensive content extraction"
    
    def _summarize_physics_validation(self, state: AgentState) -> str:
        """Summarize physics validation results."""
        if not hasattr(state, 'validation_results') or not state.validation_results:
            return "No physics validation performed"
        
        return f"Validated {len(state.validation_results)} documents for physics accuracy"
    
    def _summarize_synthesis(self, state: AgentState) -> str:
        """Summarize synthesis insights."""
        if not hasattr(state, 'synthesis_insights') or not state.synthesis_insights:
            return "No synthesis insights generated"
        
        return f"Generated {len(state.synthesis_insights)} synthesis insights and patterns"
    
    def _summarize_report(self, state: AgentState) -> str:
        """Summarize generated report."""
        if not hasattr(state, 'generated_report') or not state.generated_report:
            return "No report generated"
        
        return "Professional research report generated in multiple formats"
    
    def _extract_analysis_findings(self, state: AgentState) -> str:
        """Extract key findings from document analysis."""
        if not hasattr(state, 'analyzed_documents') or not state.analyzed_documents:
            return "No analysis findings available"
        
        findings = []
        for doc in state.analyzed_documents[:3]:  # First 3 documents
            if hasattr(doc, 'key_findings') and doc.key_findings:
                findings.extend(doc.key_findings[:2])  # Top 2 findings per doc
        
        return "\n".join([f"- {finding}" for finding in findings[:5]])
    
    def _extract_physics_results(self, state: AgentState) -> str:
        """Extract physics validation results."""
        if not hasattr(state, 'validation_results') or not state.validation_results:
            return "No physics validation results available"
        
        return f"Physics validation completed for {len(state.validation_results)} documents"
    
    def _extract_synthesis_insights(self, state: AgentState) -> str:
        """Extract synthesis insights."""
        if not hasattr(state, 'synthesis_insights') or not state.synthesis_insights:
            return "No synthesis insights available"
        
        insights = []
        for insight in state.synthesis_insights[:3]:  # Top 3 insights
            if hasattr(insight, 'insight_text'):
                insights.append(f"- {insight.insight_text}")
        
        return "\n".join(insights)
    
    def _create_default_quality_assessment(self) -> Dict[str, Any]:
        """Create default quality assessment when parsing fails."""
        return {
            "literature_score": 5.0,
            "analysis_score": 5.0,
            "physics_score": 5.0,
            "synthesis_score": 5.0,
            "report_score": 5.0,
            "overall_assessment": "Assessment parsing failed - default scores applied",
            "strengths": ["System completed research process"],
            "weaknesses": ["Quality assessment parsing failed"],
            "critical_issues": ["Unable to generate detailed quality metrics"]
        }