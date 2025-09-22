"""
Content Synthesizer Agent - Combines insights and identifies patterns across analyzed documents.
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.prompts import PromptTemplate

from .base_agent import BaseAgent
from core.models import AgentState, AnalyzedDocument, ValidationResult, SynthesisInsight


class ContentSynthesizerAgent(BaseAgent):
    """
    Agent responsible for synthesizing content across analyzed documents to identify patterns,
    contradictions, research gaps, and generate comprehensive insights.
    
    Capabilities:
    - Pattern recognition across multiple research papers
    - Contradiction detection and analysis
    - Research gap identification
    - Trend analysis and synthesis
    - Cross-study comparison and validation
    - Meta-analysis of educational approaches
    - Evidence strength assessment
    - Recommendation generation based on synthesized findings
    """
    
    def __init__(self, config, ollama_host="http://localhost:11434"):
        super().__init__(config, ollama_host)
        self.logger = logging.getLogger("Content Synthesizer")
        
    def _initialize_prompts(self) -> Dict[str, PromptTemplate]:
        """Initialize the prompts for content synthesis."""
        return {
            "pattern_analysis": PromptTemplate.from_template("""
You are an expert research synthesizer specializing in physics education research analysis.

TASK: Analyze multiple research papers to identify patterns, trends, and insights.

RESEARCH QUESTION: {research_question}

VALIDATED DOCUMENTS: {documents_summary}

VALIDATION RESULTS: {validation_summary}

Perform comprehensive pattern analysis:

1. CONVERGENT PATTERNS:
   - What consistent findings appear across multiple studies?
   - Which pedagogical approaches show repeated success?
   - What physics concepts consistently benefit from specific teaching methods?

2. DIVERGENT FINDINGS:
   - Where do studies contradict each other?
   - What conflicting evidence exists?
   - How can contradictions be explained or reconciled?

3. METHODOLOGICAL PATTERNS:
   - What research methods are most commonly used?
   - Which methodologies produce the strongest evidence?
   - Are there gaps in research approaches?

4. EFFECTIVENESS TRENDS:
   - Which teaching strategies show the highest success rates?
   - What factors correlate with improved student outcomes?
   - How do different contexts (age, level, setting) affect results?

5. RESEARCH GAPS:
   - What important questions remain unanswered?
   - Which physics topics need more research?
   - What methodological improvements are needed?

Provide analysis as structured JSON:
{{
    "convergent_patterns": [
        {{
            "pattern_description": "description",
            "supporting_studies": ["study1", "study2"],
            "evidence_strength": "strong/moderate/weak",
            "physics_concepts": ["concept1", "concept2"],
            "pedagogical_approaches": ["approach1", "approach2"]
        }}
    ],
    "divergent_findings": [
        {{
            "contradiction_description": "description",
            "conflicting_studies": ["study1", "study2"],
            "possible_explanations": ["explanation1", "explanation2"],
            "resolution_suggestions": ["suggestion1"]
        }}
    ],
    "methodological_insights": {{
        "common_methods": ["method1", "method2"],
        "strongest_evidence_methods": ["method1"],
        "methodological_gaps": ["gap1", "gap2"]
    }},
    "effectiveness_trends": {{
        "high_impact_strategies": ["strategy1", "strategy2"],
        "context_dependencies": ["context1", "context2"],
        "success_factors": ["factor1", "factor2"]
    }},
    "research_gaps": {{
        "content_gaps": ["gap1", "gap2"],
        "methodological_gaps": ["gap1", "gap2"],
        "priority_research_needs": ["need1", "need2"]
    }}
}}
"""),
            "evidence_synthesis": PromptTemplate.from_template("""
Synthesize evidence across physics education research studies to generate actionable insights.

RESEARCH FOCUS: {research_question}

STUDY SUMMARIES:
{study_summaries}

PHYSICS VALIDATION SCORES:
{physics_scores}

Create evidence-based synthesis:

1. EVIDENCE STRENGTH ASSESSMENT:
   - Categorize findings by evidence quality (strong/moderate/weak)
   - Consider sample sizes, methodology quality, and replication
   - Weight findings by physics accuracy and validation scores

2. PRACTICAL IMPLICATIONS:
   - What specific teaching strategies are most effective?
   - How should physics educators modify their practice?
   - What tools or resources are most beneficial?

3. THEORETICAL INSIGHTS:
   - What learning theories are supported by the evidence?
   - How do physics-specific factors influence learning?
   - What cognitive principles emerge from the research?

4. IMPLEMENTATION GUIDANCE:
   - Step-by-step recommendations for educators
   - Considerations for different educational contexts
   - Potential challenges and mitigation strategies

5. FUTURE RESEARCH PRIORITIES:
   - Most critical research questions to address
   - Methodological improvements needed
   - Emerging areas for investigation

Respond in structured JSON format:
{{
    "evidence_synthesis": {{
        "strong_evidence": [
            {{
                "finding": "description",
                "supporting_studies": ["study1", "study2"],
                "practical_implication": "what educators should do",
                "implementation_difficulty": "easy/moderate/challenging"
            }}
        ],
        "moderate_evidence": [
            {{
                "finding": "description",
                "supporting_studies": ["study1"],
                "caveat": "limitation or uncertainty",
                "additional_research_needed": "what's needed for confirmation"
            }}
        ],
        "weak_evidence": [
            {{
                "finding": "description",
                "limitations": ["limitation1", "limitation2"],
                "potential_value": "why still worth considering"
            }}
        ]
    }},
    "practical_recommendations": [
        {{
            "recommendation": "specific action",
            "physics_topics": ["topic1", "topic2"],
            "target_audience": "K-12/undergraduate/graduate/all",
            "implementation_steps": ["step1", "step2"],
            "expected_outcomes": ["outcome1", "outcome2"],
            "evidence_basis": "brief justification"
        }}
    ],
    "theoretical_insights": [
        {{
            "insight": "theoretical understanding",
            "learning_theory_connection": "theory name/principle",
            "physics_specific_factors": ["factor1", "factor2"],
            "implications_for_practice": "how this changes teaching"
        }}
    ],
    "future_research_priorities": [
        {{
            "research_question": "specific question",
            "importance": "high/medium/low",
            "feasibility": "high/medium/low",
            "potential_impact": "description",
            "suggested_methodology": "approach"
        }}
    ]
}}
"""),
            "comparative_analysis": PromptTemplate.from_template("""
Perform comparative analysis across physics education research studies.

STUDIES TO COMPARE:
{comparative_data}

COMPARISON CRITERIA:
- Sample sizes and demographics
- Research methodologies and designs
- Physics concepts and educational levels
- Measured outcomes and effect sizes
- Study quality and validation scores

Analyze and compare:

1. STUDY CHARACTERISTICS:
   - How do sample sizes compare?
   - What methodological approaches were used?
   - Which physics topics were addressed?
   - What educational levels were studied?

2. OUTCOME COMPARISONS:
   - Which studies show the strongest effects?
   - How consistent are the findings across studies?
   - Where do results diverge and why?

3. QUALITY ASSESSMENT:
   - Which studies have the highest validation scores?
   - What makes some studies more reliable than others?
   - How does study quality relate to findings?

4. CONTEXTUAL FACTORS:
   - How do educational settings influence results?
   - What cultural or demographic factors matter?
   - Which findings are most generalizable?

Provide structured comparison:
{{
    "study_comparison": [
        {{
            "study_group": "studies with similar findings",
            "studies": ["study1", "study2"],
            "common_characteristics": ["characteristic1", "characteristic2"],
            "shared_findings": ["finding1", "finding2"],
            "combined_evidence_strength": "strong/moderate/weak"
        }}
    ],
    "outcome_analysis": {{
        "strongest_effects": [
            {{
                "finding": "description",
                "effect_size": "large/medium/small",
                "studies": ["study1", "study2"],
                "consistency": "high/medium/low"
            }}
        ],
        "inconsistent_findings": [
            {{
                "topic": "area of disagreement",
                "conflicting_results": ["result1", "result2"],
                "possible_explanations": ["explanation1", "explanation2"]
            }}
        ]
    }},
    "quality_insights": {{
        "highest_quality_studies": ["study1", "study2"],
        "quality_factors": ["factor1", "factor2"],
        "reliability_assessment": "overall reliability level"
    }},
    "generalizability": {{
        "most_generalizable_findings": ["finding1", "finding2"],
        "context_dependent_findings": ["finding1", "finding2"],
        "transferability_factors": ["factor1", "factor2"]
    }}
}}
""")
        }

    async def process(self, state: AgentState) -> AgentState:
        """
        Process validated documents and generate comprehensive synthesis.
        
        Args:
            state: Current agent state with analyzed documents and validation results
            
        Returns:
            Updated state with synthesis insights and patterns
        """
        self.logger.info(f"Starting content synthesis for {len(state.analyzed_documents)} documents...")
        
        if not state.analyzed_documents:
            self.logger.warning("No analyzed documents found for synthesis")
            state.synthesis_insights = []
            state.synthesized_content = {
                "status": "no_content",
                "message": "No analyzed documents available for synthesis"
            }
            return state
        
        try:
            # Step 1: Pattern Analysis across all documents
            pattern_analysis = await self._analyze_patterns(state)
            
            # Step 2: Evidence Synthesis
            evidence_synthesis = await self._synthesize_evidence(state)
            
            # Step 3: Comparative Analysis
            comparative_analysis = await self._perform_comparative_analysis(state)
            
            # Step 4: Generate synthesis insights
            synthesis_insights = self._extract_synthesis_insights(
                pattern_analysis, evidence_synthesis, comparative_analysis
            )
            
            # Step 5: Create comprehensive synthesis
            synthesized_content = {
                "pattern_analysis": pattern_analysis,
                "evidence_synthesis": evidence_synthesis,
                "comparative_analysis": comparative_analysis,
                "total_documents_analyzed": len(state.analyzed_documents),
                "synthesis_timestamp": datetime.now().isoformat(),
                "synthesizer_model": self.config.model.name,
                "research_question": state.query.question,
                "synthesis_quality_score": self._calculate_synthesis_quality(
                    state.analyzed_documents, synthesis_insights
                )
            }
            
            # Update state
            state.synthesis_insights = synthesis_insights
            state.synthesized_content = synthesized_content
            
            self.logger.info(f"Content synthesis completed: {len(synthesis_insights)} insights generated")
            
        except Exception as e:
            self.logger.error(f"Content synthesis failed: {str(e)}")
            state.errors.append(f"Content synthesis error: {e}")
            state.synthesized_content = {"status": "error", "error": str(e)}
        
        return state

    async def _analyze_patterns(self, state: AgentState) -> Dict[str, Any]:
        """Analyze patterns across all analyzed documents."""
        try:
            # Prepare document summaries
            documents_summary = []
            for doc in state.analyzed_documents:
                summary = {
                    "title": doc.paper.title,
                    "key_findings": doc.key_findings,
                    "methodology": str(doc.methodology),
                    "physics_concepts": getattr(doc, 'physics_concepts', []),
                    "educational_approaches": getattr(doc, 'educational_approaches', []),
                    "relevance_score": doc.paper.relevance_score
                }
                documents_summary.append(summary)
            
            # Prepare validation summary
            validation_summary = []
            if hasattr(state, 'validation_results') and state.validation_results:
                for validation in state.validation_results:
                    summary = {
                        "document": validation.document.paper.title,
                        "overall_score": validation.overall_validation.get("total_score", 0),
                        "physics_accuracy": validation.concept_accuracy.get("score", 0),
                        "math_accuracy": validation.mathematical_validation.get("score", 0)
                    }
                    validation_summary.append(summary)
            
            # Execute pattern analysis
            prompt = self.prompt_templates["pattern_analysis"].format(
                research_question=state.query.question,
                documents_summary=json.dumps(documents_summary, indent=2),
                validation_summary=json.dumps(validation_summary, indent=2)
            )
            
            response = await self.llm.ainvoke(prompt)
            
            # Parse JSON response
            try:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"status": "parsing_failed", "raw_response": response.content}
            except json.JSONDecodeError:
                return {"status": "json_parse_error", "raw_response": response.content}
                
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _synthesize_evidence(self, state: AgentState) -> Dict[str, Any]:
        """Synthesize evidence across all studies."""
        try:
            # Prepare study summaries
            study_summaries = []
            for doc in state.analyzed_documents:
                summary = f"""
Title: {doc.paper.title}
Authors: {', '.join(doc.paper.authors[:3])}
Key Findings: {', '.join(doc.key_findings)}
Methodology: {str(doc.methodology)}
Limitations: {', '.join(getattr(doc, 'limitations', []))}
Relevance Score: {doc.paper.relevance_score}
"""
                study_summaries.append(summary)
            
            # Prepare physics validation scores
            physics_scores = []
            if hasattr(state, 'validation_results') and state.validation_results:
                for validation in state.validation_results:
                    score_info = f"{validation.document.paper.title}: Overall={validation.overall_validation.get('total_score', 0)}/10, Physics={validation.concept_accuracy.get('score', 0)}/10"
                    physics_scores.append(score_info)
            
            prompt = self.prompt_templates["evidence_synthesis"].format(
                research_question=state.query.question,
                study_summaries="\n".join(study_summaries),
                physics_scores="\n".join(physics_scores)
            )
            
            response = await self.llm.ainvoke(prompt)
            
            # Parse JSON response
            try:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"status": "parsing_failed", "raw_response": response.content}
            except json.JSONDecodeError:
                return {"status": "json_parse_error", "raw_response": response.content}
                
        except Exception as e:
            self.logger.error(f"Evidence synthesis failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _perform_comparative_analysis(self, state: AgentState) -> Dict[str, Any]:
        """Perform comparative analysis across studies."""
        try:
            # Prepare comparative data
            comparative_data = []
            for doc in state.analyzed_documents:
                data = {
                    "title": doc.paper.title,
                    "sample_info": str(doc.methodology).get("sample_size", "Not specified"),
                    "methodology": str(doc.methodology),
                    "physics_topics": getattr(doc, 'physics_concepts', []),
                    "findings": doc.key_findings,
                    "quality_indicators": {
                        "citations": doc.paper.citations,
                        "relevance_score": doc.paper.relevance_score,
                        "extraction_confidence": getattr(doc, 'extraction_confidence', 0)
                    }
                }
                
                # Add validation scores if available
                if hasattr(state, 'validation_results') and state.validation_results:
                    for validation in state.validation_results:
                        if validation.document.paper.title == doc.paper.title:
                            data["validation_scores"] = {
                                "overall": validation.overall_validation.get("total_score", 0),
                                "physics": validation.concept_accuracy.get("score", 0),
                                "math": validation.mathematical_validation.get("score", 0)
                            }
                            break
                
                comparative_data.append(data)
            
            prompt = self.prompt_templates["comparative_analysis"].format(
                comparative_data=json.dumps(comparative_data, indent=2)
            )
            
            response = await self.llm.ainvoke(prompt)
            
            # Parse JSON response
            try:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"status": "parsing_failed", "raw_response": response.content}
            except json.JSONDecodeError:
                return {"status": "json_parse_error", "raw_response": response.content}
                
        except Exception as e:
            self.logger.error(f"Comparative analysis failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _extract_synthesis_insights(
        self, 
        pattern_analysis: Dict[str, Any], 
        evidence_synthesis: Dict[str, Any], 
        comparative_analysis: Dict[str, Any]
    ) -> List[SynthesisInsight]:
        """Extract structured insights from synthesis results."""
        insights = []
        
        try:
            # Extract convergent patterns as insights
            if "convergent_patterns" in pattern_analysis:
                for pattern in pattern_analysis["convergent_patterns"]:
                    insight = SynthesisInsight(
                        insight_type="pattern",
                        description=pattern.get("pattern_description", ""),
                        supporting_evidence=pattern.get("supporting_studies", []),
                        confidence=self._map_evidence_strength(pattern.get("evidence_strength", "weak")),
                        related_papers=pattern.get("supporting_studies", [])
                    )
                    insights.append(insight)
            
            # Extract contradictions as insights
            if "divergent_findings" in pattern_analysis:
                for contradiction in pattern_analysis["divergent_findings"]:
                    insight = SynthesisInsight(
                        insight_type="contradiction",
                        description=contradiction.get("contradiction_description", ""),
                        supporting_evidence=contradiction.get("possible_explanations", []),
                        confidence=0.7,  # Moderate confidence for contradictions
                        related_papers=contradiction.get("conflicting_studies", [])
                    )
                    insights.append(insight)
            
            # Extract research gaps as insights
            if "research_gaps" in pattern_analysis:
                gaps = pattern_analysis["research_gaps"]
                for gap_category, gap_list in gaps.items():
                    if isinstance(gap_list, list):
                        for gap in gap_list:
                            insight = SynthesisInsight(
                                insight_type="gap",
                                description=f"{gap_category.replace('_', ' ').title()}: {gap}",
                                supporting_evidence=[f"Analysis of {len(pattern_analysis.get('convergent_patterns', []))} studies"],
                                confidence=0.8,
                                related_papers=[]
                            )
                            insights.append(insight)
            
            # Extract evidence-based insights
            if "evidence_synthesis" in evidence_synthesis:
                synthesis = evidence_synthesis["evidence_synthesis"]
                for evidence_level in ["strong_evidence", "moderate_evidence"]:
                    if evidence_level in synthesis:
                        for finding in synthesis[evidence_level]:
                            confidence = 0.9 if evidence_level == "strong_evidence" else 0.7
                            insight = SynthesisInsight(
                                insight_type="evidence",
                                description=finding.get("finding", ""),
                                supporting_evidence=[finding.get("practical_implication", "")],
                                confidence=confidence,
                                related_papers=finding.get("supporting_studies", [])
                            )
                            insights.append(insight)
            
            # Extract trends from comparative analysis
            if "outcome_analysis" in comparative_analysis:
                outcomes = comparative_analysis["outcome_analysis"]
                if "strongest_effects" in outcomes:
                    for effect in outcomes["strongest_effects"]:
                        insight = SynthesisInsight(
                            insight_type="trend",
                            description=f"Strong effect: {effect.get('finding', '')}",
                            supporting_evidence=[f"Effect size: {effect.get('effect_size', 'unknown')}"],
                            confidence=self._map_consistency(effect.get("consistency", "low")),
                            related_papers=effect.get("studies", [])
                        )
                        insights.append(insight)
            
        except Exception as e:
            self.logger.error(f"Error extracting synthesis insights: {str(e)}")
        
        return insights

    def _map_evidence_strength(self, strength: str) -> float:
        """Map evidence strength to confidence score."""
        mapping = {
            "strong": 0.9,
            "moderate": 0.7,
            "weak": 0.5
        }
        return mapping.get(strength.lower(), 0.5)

    def _map_consistency(self, consistency: str) -> float:
        """Map consistency level to confidence score."""
        mapping = {
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5
        }
        return mapping.get(consistency.lower(), 0.5)

    def _calculate_synthesis_quality(
        self, 
        analyzed_documents: List[AnalyzedDocument], 
        synthesis_insights: List[SynthesisInsight]
    ) -> float:
        """Calculate overall quality score for the synthesis."""
        if not analyzed_documents or not synthesis_insights:
            return 0.0
        
        # Factors contributing to synthesis quality
        document_count_factor = min(len(analyzed_documents) / 10.0, 1.0)  # Up to 10 documents is optimal
        insight_count_factor = min(len(synthesis_insights) / 15.0, 1.0)   # Up to 15 insights is good
        
        # Average confidence of insights
        avg_confidence = sum(insight.confidence for insight in synthesis_insights) / len(synthesis_insights)
        
        # Average document relevance
        avg_relevance = sum(doc.paper.relevance_score for doc in analyzed_documents) / len(analyzed_documents)
        
        # Insight type diversity (bonus for having different types of insights)
        insight_types = set(insight.insight_type for insight in synthesis_insights)
        diversity_factor = len(insight_types) / 5.0  # Up to 5 types (pattern, contradiction, gap, evidence, trend)
        
        # Weighted average
        quality_score = (
            document_count_factor * 0.2 +
            insight_count_factor * 0.2 +
            avg_confidence * 0.3 +
            avg_relevance * 0.2 +
            diversity_factor * 0.1
        )
        
        return min(quality_score, 1.0)

    def get_synthesis_summary(self, synthesized_content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the synthesis results."""
        if not synthesized_content or synthesized_content.get("status") == "error":
            return {"status": "no_synthesis_available"}
        
        summary = {
            "total_documents": synthesized_content.get("total_documents_analyzed", 0),
            "synthesis_quality": synthesized_content.get("synthesis_quality_score", 0.0),
            "model_used": synthesized_content.get("synthesizer_model", "Unknown"),
            "timestamp": synthesized_content.get("synthesis_timestamp", "Unknown")
        }
        
        # Extract key metrics from pattern analysis
        pattern_analysis = synthesized_content.get("pattern_analysis", {})
        if pattern_analysis and "convergent_patterns" in pattern_analysis:
            summary["convergent_patterns_found"] = len(pattern_analysis["convergent_patterns"])
            summary["contradictions_found"] = len(pattern_analysis.get("divergent_findings", []))
        
        # Extract key metrics from evidence synthesis
        evidence_synthesis = synthesized_content.get("evidence_synthesis", {})
        if evidence_synthesis and "evidence_synthesis" in evidence_synthesis:
            evidence = evidence_synthesis["evidence_synthesis"]
            summary["strong_evidence_findings"] = len(evidence.get("strong_evidence", []))
            summary["practical_recommendations"] = len(evidence_synthesis.get("practical_recommendations", []))
        
        # Extract key metrics from comparative analysis
        comparative_analysis = synthesized_content.get("comparative_analysis", {})
        if comparative_analysis and "outcome_analysis" in comparative_analysis:
            outcomes = comparative_analysis["outcome_analysis"]
            summary["strongest_effects_found"] = len(outcomes.get("strongest_effects", []))
        
        return summary