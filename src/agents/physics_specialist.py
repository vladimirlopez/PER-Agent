"""
Physics Specialist Agent - Validates physics concepts and mathematical accuracy.
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.prompts import PromptTemplate

from .base_agent import BaseAgent
from core.models import AgentState, AnalyzedDocument, ValidationResult


class PhysicsSpecialistAgent(BaseAgent):
    """
    Agent responsible for validating physics concepts, checking mathematical accuracy,
    and reviewing research methodology from a physics education perspective.
    
    Capabilities:
    - Physics concept validation and accuracy checking
    - Mathematical equation and formula verification
    - Methodology review for physics education research
    - Identification of misconceptions and errors
    - Assessment of pedagogical physics content
    - Cross-referencing with established physics principles
    """
    
    def __init__(self, config, ollama_host="http://localhost:11434"):
        super().__init__(config, ollama_host)
        self.logger = logging.getLogger("Physics Specialist")
        
    def _initialize_prompts(self) -> Dict[str, PromptTemplate]:
        """Initialize the prompts for physics validation."""
        return {
            "concept_validation": PromptTemplate.from_template("""
You are a physics education expert with deep knowledge of physics concepts and common student misconceptions.

DOCUMENT TO VALIDATE:
Title: {title}
Key Findings: {key_findings}
Methodology: {methodology}
Full Summary: {summary}

Please perform a comprehensive physics validation:

1. CONCEPT ACCURACY:
   - Are the physics concepts correctly stated and explained?
   - Are there any physics misconceptions or errors?
   - Are the definitions and terminology accurate?
   - Rate accuracy from 1-10

2. MATHEMATICAL VALIDATION:
   - Are any equations, formulas, or calculations correct?
   - Are units and dimensional analysis proper?
   - Are numerical results reasonable and consistent?
   - Rate mathematical accuracy from 1-10

3. METHODOLOGY REVIEW:
   - Is the research methodology appropriate for physics education?
   - Are the experimental designs or surveys valid for physics learning?
   - Are the measurement techniques suitable for physics concepts?
   - Rate methodology soundness from 1-10

4. PEDAGOGICAL PHYSICS ASSESSMENT:
   - Do the teaching approaches align with physics education best practices?
   - Are the learning objectives appropriate for the physics level?
   - Are common physics misconceptions properly addressed?
   - Rate pedagogical effectiveness from 1-10

5. POTENTIAL ISSUES:
   - List any physics errors or misconceptions found
   - Identify questionable claims or unsupported assertions
   - Note any mathematical inconsistencies
   - Highlight methodology concerns

6. RECOMMENDATIONS:
   - Suggest improvements for physics accuracy
   - Recommend better physics teaching approaches if applicable
   - Propose additional validation needs

Respond in structured JSON format:
{{
    "concept_accuracy": {{
        "score": 8,
        "issues": ["issue1", "issue2"],
        "correct_concepts": ["concept1", "concept2"],
        "misconceptions_found": ["misconception1"]
    }},
    "mathematical_validation": {{
        "score": 9,
        "equations_correct": true,
        "units_proper": true,
        "calculations_verified": ["calc1", "calc2"],
        "mathematical_issues": ["issue1"]
    }},
    "methodology_review": {{
        "score": 7,
        "strengths": ["strength1", "strength2"],
        "weaknesses": ["weakness1"],
        "validity_concerns": ["concern1"]
    }},
    "pedagogical_assessment": {{
        "score": 8,
        "effective_approaches": ["approach1", "approach2"],
        "improvement_areas": ["area1"],
        "misconception_handling": "good/fair/poor"
    }},
    "overall_validation": {{
        "total_score": 8.0,
        "confidence_level": "high/medium/low",
        "recommendation": "accept/accept_with_revisions/major_revisions_needed/reject",
        "critical_issues": ["issue1", "issue2"],
        "strengths": ["strength1", "strength2"]
    }},
    "specific_recommendations": ["recommendation1", "recommendation2"]
}}
"""),
            "physics_cross_check": PromptTemplate.from_template("""
Cross-reference this physics education research against established physics principles.

RESEARCH CONTENT:
{content}

PHYSICS DOMAIN: {domain}

Perform a detailed cross-check:

1. PHYSICS PRINCIPLE ALIGNMENT:
   - Do the findings align with established physics laws and principles?
   - Are there any contradictions with well-known physics concepts?
   - Is the physics level appropriate (K-12, undergraduate, graduate)?

2. COMMON MISCONCEPTION ANALYSIS:
   - Does this research address known physics misconceptions?
   - Are the misconceptions correctly identified and described?
   - Are the proposed solutions effective for these misconceptions?

3. PHYSICS EDUCATION STANDARDS:
   - Does this align with physics education standards (NGSS, AP Physics, etc.)?
   - Are the learning objectives realistic and measurable?
   - Is the content age-appropriate for the target audience?

4. EXPERIMENTAL PHYSICS VALIDITY:
   - If experiments are described, are they physically sound?
   - Are the measurement techniques appropriate and accurate?
   - Are error analysis and uncertainty properly addressed?

Provide assessment as JSON:
{{
    "principle_alignment": {{
        "score": 8,
        "aligned_principles": ["conservation of energy", "Newton's laws"],
        "contradictions": ["contradiction1"],
        "physics_level": "high school/undergraduate/graduate"
    }},
    "misconception_analysis": {{
        "addresses_known_misconceptions": true,
        "misconceptions_identified": ["misconception1", "misconception2"],
        "solution_effectiveness": "high/medium/low"
    }},
    "standards_compliance": {{
        "meets_standards": true,
        "applicable_standards": ["NGSS HS-PS1", "AP Physics C"],
        "learning_objectives_quality": "excellent/good/fair/poor"
    }},
    "experimental_validity": {{
        "experiments_sound": true,
        "measurement_appropriate": true,
        "error_analysis_present": false,
        "validity_concerns": ["concern1"]
    }}
}}
"""),
            "misconception_detector": PromptTemplate.from_template("""
Analyze this physics education content for common physics misconceptions.

CONTENT: {content}

You are an expert at identifying physics misconceptions. Scan for:

COMMON PHYSICS MISCONCEPTIONS:
- Force and motion (objects need continuous force to move)
- Energy (energy is used up, not conserved)
- Electricity (current gets used up in circuits)
- Heat and temperature (heat and temperature are the same)
- Waves (sound needs air to travel through)
- Light (light travels instantaneously)
- Gravity (heavier objects fall faster)
- And many others...

Analysis required:
1. Identify any misconceptions present in the content
2. Determine if misconceptions are being studied or accidentally reinforced
3. Assess whether correct physics concepts are clearly presented
4. Evaluate misconception remediation strategies if present

Return JSON analysis:
{{
    "misconceptions_found": [
        {{
            "misconception": "description",
            "physics_topic": "mechanics/energy/electricity/etc",
            "severity": "critical/moderate/minor",
            "context": "how it appears in content",
            "correct_concept": "what should be taught instead"
        }}
    ],
    "misconception_handling": {{
        "explicitly_addresses": true,
        "remediation_strategy": "strategy description",
        "effectiveness": "high/medium/low",
        "evidence_based": true
    }},
    "concept_clarity": {{
        "clear_explanations": true,
        "potential_confusion": ["area1", "area2"],
        "improvement_suggestions": ["suggestion1", "suggestion2"]
    }}
}}
""")
        }

    async def process(self, state: AgentState) -> AgentState:
        """
        Process analyzed documents through physics validation.
        
        Args:
            state: Current agent state with analyzed documents
            
        Returns:
            Updated state with physics validation results
        """
        self.logger.info(f"Starting physics validation for {len(state.analyzed_documents)} documents...")
        
        validation_results = []
        
        for i, doc in enumerate(state.analyzed_documents, 1):
            self.logger.info(f"Validating document {i}/{len(state.analyzed_documents)}: {doc.paper.title[:50]}...")
            
            try:
                # Perform comprehensive physics validation
                validation = await self._validate_physics_content(doc)
                
                if validation:
                    # Cross-check against physics principles
                    cross_check = await self._cross_check_physics(doc)
                    
                    # Detect misconceptions
                    misconception_analysis = await self._detect_misconceptions(doc)
                    
                    # Create comprehensive validation result
                    result = ValidationResult(
                        document=doc,
                        concept_accuracy=validation.get("concept_accuracy", {}),
                        mathematical_validation=validation.get("mathematical_validation", {}),
                        methodology_review=validation.get("methodology_review", {}),
                        pedagogical_assessment=validation.get("pedagogical_assessment", {}),
                        overall_validation=validation.get("overall_validation", {}),
                        cross_check_results=cross_check,
                        misconception_analysis=misconception_analysis,
                        recommendations=validation.get("specific_recommendations", []),
                        validation_timestamp=datetime.now().isoformat(),
                        validator_model=self.config.model.name
                    )
                    
                    validation_results.append(result)
                    
                    overall_score = validation.get("overall_validation", {}).get("total_score", 0)
                    self.logger.info(f"Physics validation completed: {doc.paper.title[:50]}... (Score: {overall_score}/10)")
                
            except Exception as e:
                self.logger.error(f"Error validating document {doc.paper.title}: {str(e)}")
                continue
        
        # Update state with validation results
        state.validation_results = validation_results
        
        # Calculate summary statistics
        if validation_results:
            scores = [r.overall_validation.get("total_score", 0) for r in validation_results]
            avg_score = sum(scores) / len(scores)
            
            state.validation_summary = {
                "total_documents_validated": len(validation_results),
                "average_physics_score": avg_score,
                "high_quality_papers": len([s for s in scores if s >= 8]),
                "needs_revision": len([s for s in scores if s < 6]),
                "validation_timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Physics validation completed: {len(validation_results)} documents validated, average score: {avg_score:.1f}/10")
        else:
            self.logger.warning("No documents were successfully validated")
            state.validation_summary = {
                "total_documents_validated": 0,
                "average_physics_score": 0,
                "validation_timestamp": datetime.now().isoformat()
            }
        
        return state

    async def _validate_physics_content(self, doc: AnalyzedDocument) -> Optional[Dict[str, Any]]:
        """Perform comprehensive physics validation of document content."""
        
        try:
            prompt = self.prompt_templates["concept_validation"].format(
                title=doc.paper.title,
                key_findings=", ".join(doc.key_findings),
                methodology=str(doc.methodology),
                summary=doc.summary
            )
            
            response = await self.llm.ainvoke(prompt)
            
            # Handle different response types
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
            
            # Parse JSON response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    validation = json.loads(json_match.group())
                    return validation
                else:
                    self.logger.warning(f"No JSON found in physics validation response for {doc.paper.title}")
                    return None
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse physics validation JSON for {doc.paper.title}: {e}")
                # Return basic validation structure
                return {
                    "concept_accuracy": {"score": 5, "issues": ["Analysis parsing failed"]},
                    "mathematical_validation": {"score": 5, "equations_correct": None},
                    "methodology_review": {"score": 5, "validity_concerns": ["Review incomplete"]},
                    "pedagogical_assessment": {"score": 5, "improvement_areas": ["Manual review needed"]},
                    "overall_validation": {
                        "total_score": 5.0,
                        "confidence_level": "low",
                        "recommendation": "manual_review_needed",
                        "critical_issues": ["Automatic validation failed"]
                    },
                    "specific_recommendations": ["Manual physics expert review recommended"]
                }
                
        except Exception as e:
            self.logger.error(f"Error in physics validation for {doc.paper.title}: {str(e)}")
            return None

    async def _cross_check_physics(self, doc: AnalyzedDocument) -> Optional[Dict[str, Any]]:
        """Cross-check document against established physics principles."""
        
        try:
            # Determine physics domain from content
            domain = self._identify_physics_domain(doc)
            
            content = f"Title: {doc.paper.title}\nSummary: {doc.summary}\nKey Findings: {', '.join(doc.key_findings)}"
            
            prompt = self.prompt_templates["physics_cross_check"].format(
                content=content,
                domain=domain
            )
            
            response = await self.llm.ainvoke(prompt)
            
            # Parse JSON response
            try:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"cross_check_status": "parsing_failed"}
                    
            except json.JSONDecodeError:
                return {"cross_check_status": "json_parse_error"}
                
        except Exception as e:
            self.logger.error(f"Error in physics cross-check for {doc.paper.title}: {str(e)}")
            return {"cross_check_status": "error", "error": str(e)}

    async def _detect_misconceptions(self, doc: AnalyzedDocument) -> Optional[Dict[str, Any]]:
        """Detect physics misconceptions in the document content."""
        
        try:
            content = f"Title: {doc.paper.title}\nSummary: {doc.summary}\nKey Findings: {', '.join(doc.key_findings)}\nMethodology: {str(doc.methodology)}"
            
            prompt = self.prompt_templates["misconception_detector"].format(content=content)
            
            response = await self.llm.ainvoke(prompt)
            
            # Parse JSON response
            try:
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"misconception_detection_status": "parsing_failed"}
                    
            except json.JSONDecodeError:
                return {"misconception_detection_status": "json_parse_error"}
                
        except Exception as e:
            self.logger.error(f"Error in misconception detection for {doc.paper.title}: {str(e)}")
            return {"misconception_detection_status": "error", "error": str(e)}

    def _identify_physics_domain(self, doc: AnalyzedDocument) -> str:
        """Identify the primary physics domain of the document."""
        
        content = (doc.paper.title + " " + doc.summary + " " + " ".join(doc.key_findings)).lower()
        
        # Physics domain keywords
        domains = {
            "mechanics": ["force", "motion", "velocity", "acceleration", "momentum", "energy", "work", "power"],
            "electricity": ["electric", "current", "voltage", "circuit", "resistance", "capacitor", "magnetic"],
            "thermodynamics": ["heat", "temperature", "thermal", "entropy", "gas laws", "thermodynamic"],
            "waves": ["wave", "sound", "light", "optics", "frequency", "wavelength", "interference"],
            "quantum": ["quantum", "atomic", "electron", "photon", "particle", "wave-particle"],
            "relativity": ["relativity", "spacetime", "gravity", "einstein", "mass-energy"],
            "general": ["physics", "education", "learning", "teaching", "student", "misconception"]
        }
        
        # Count keyword matches for each domain
        domain_scores = {}
        for domain, keywords in domains.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                domain_scores[domain] = score
        
        # Return domain with highest score, default to general
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        else:
            return "general"

    def get_validation_summary(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate a summary of validation results."""
        
        if not validation_results:
            return {"status": "no_validations_performed"}
        
        # Calculate aggregate scores
        concept_scores = [r.concept_accuracy.get("score", 0) for r in validation_results]
        math_scores = [r.mathematical_validation.get("score", 0) for r in validation_results]
        method_scores = [r.methodology_review.get("score", 0) for r in validation_results]
        pedagogy_scores = [r.pedagogical_assessment.get("score", 0) for r in validation_results]
        overall_scores = [r.overall_validation.get("total_score", 0) for r in validation_results]
        
        # Collect common issues
        all_issues = []
        all_misconceptions = []
        all_recommendations = []
        
        for result in validation_results:
            all_issues.extend(result.concept_accuracy.get("issues", []))
            if result.misconception_analysis and "misconceptions_found" in result.misconception_analysis:
                all_misconceptions.extend([m.get("misconception", "") for m in result.misconception_analysis["misconceptions_found"]])
            all_recommendations.extend(result.recommendations)
        
        return {
            "total_documents": len(validation_results),
            "average_scores": {
                "concept_accuracy": sum(concept_scores) / len(concept_scores) if concept_scores else 0,
                "mathematical_validation": sum(math_scores) / len(math_scores) if math_scores else 0,
                "methodology_review": sum(method_scores) / len(method_scores) if method_scores else 0,
                "pedagogical_assessment": sum(pedagogy_scores) / len(pedagogy_scores) if pedagogy_scores else 0,
                "overall": sum(overall_scores) / len(overall_scores) if overall_scores else 0
            },
            "quality_distribution": {
                "excellent": len([s for s in overall_scores if s >= 9]),
                "good": len([s for s in overall_scores if 7 <= s < 9]),
                "fair": len([s for s in overall_scores if 5 <= s < 7]),
                "poor": len([s for s in overall_scores if s < 5])
            },
            "common_issues": list(set(all_issues))[:10],  # Top 10 unique issues
            "misconceptions_detected": list(set(all_misconceptions))[:10],  # Top 10 unique misconceptions
            "key_recommendations": list(set(all_recommendations))[:10]  # Top 10 unique recommendations
        }