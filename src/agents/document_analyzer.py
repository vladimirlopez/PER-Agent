"""
Document Analyzer Agent - Parses PDFs and extracts key findings.
"""

import asyncio
import json
import logging
import re
import tempfile
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import arxiv
import requests
import PyPDF2
import fitz  # PyMuPDF for better text extraction
from langchain_core.prompts import PromptTemplate

from .base_agent import BaseAgent
from core.models import AgentState, Paper, AnalyzedDocument


class DocumentAnalyzerAgent(BaseAgent):
    """
    Agent responsible for downloading, parsing, and analyzing academic papers.
    
    Capabilities:
    - PDF download from URLs
    - Text extraction from PDFs
    - Key finding identification using LLM
    - Structured analysis of academic content
    - Metadata extraction and validation
    """
    
    def __init__(self, config, ollama_host="http://localhost:11434"):
        super().__init__(config, ollama_host)
        self.logger = logging.getLogger("Document Analyzer")
        self.temp_dir = Path(tempfile.gettempdir()) / "per_agent_pdfs"
        self.temp_dir.mkdir(exist_ok=True)
        
    def _initialize_prompts(self) -> Dict[str, PromptTemplate]:
        """Initialize the prompts for document analysis."""
        return {
            "key_findings": PromptTemplate.from_template("""
You are an expert academic researcher analyzing a physics education research paper.

PAPER TITLE: {title}
PAPER ABSTRACT: {abstract}
PAPER FULL TEXT: {full_text}

Please extract and analyze the following key elements:

1. MAIN RESEARCH QUESTION(S):
   - What specific question(s) does this paper address?
   
2. METHODOLOGY:
   - What research methods were used?
   - Sample size and demographics if applicable
   - Data collection techniques

3. KEY FINDINGS:
   - What are the main results/conclusions?
   - Any statistical significance or effect sizes mentioned
   - Specific insights about physics education

4. PEDAGOGICAL IMPLICATIONS:
   - How can these findings be applied in physics teaching?
   - What teaching strategies are recommended?
   - Any tools or techniques mentioned

5. LIMITATIONS & FUTURE WORK:
   - What limitations does the study acknowledge?
   - What future research directions are suggested?

6. RELEVANCE SCORE (1-10):
   - How relevant is this paper to physics education research?
   - Justify your score

Format your response as structured JSON:
{{
    "research_questions": ["question1", "question2"],
    "methodology": {{
        "methods": ["method1", "method2"],
        "sample_size": "description",
        "data_collection": "description"
    }},
    "key_findings": ["finding1", "finding2", "finding3"],
    "pedagogical_implications": ["implication1", "implication2"],
    "limitations": ["limitation1", "limitation2"],
    "future_work": ["direction1", "direction2"],
    "relevance_score": 8,
    "relevance_justification": "explanation of score"
}}
"""),
            "summary": PromptTemplate.from_template("""
Create a concise academic summary of this physics education research paper.

TITLE: {title}
KEY FINDINGS: {key_findings}
METHODOLOGY: {methodology}
IMPLICATIONS: {implications}

Write a 2-3 paragraph summary that:
1. Introduces the research question and methodology
2. Presents the main findings clearly
3. Discusses implications for physics education practice

Keep the tone academic but accessible. Focus on actionable insights for educators.

SUMMARY:
""")
        }

    async def process(self, state: AgentState) -> AgentState:
        """
        Process papers by downloading, parsing, and analyzing them.
        
        Args:
            state: Current agent state with papers to analyze
            
        Returns:
            Updated state with analyzed documents
        """
        self.logger.info(f"Starting document analysis for {len(state.papers)} papers...")
        
        analyzed_docs = []
        
        for i, paper in enumerate(state.papers, 1):
            self.logger.info(f"Analyzing paper {i}/{len(state.papers)}: {paper.title[:50]}...")
            
            try:
                # Download and parse PDF
                pdf_text = await self._download_and_parse_pdf(paper)
                
                if not pdf_text:
                    self.logger.warning(f"Could not extract text from paper: {paper.title}")
                    continue
                
                # Analyze content with LLM
                analysis = await self._analyze_content(paper, pdf_text)
                
                if analysis:
                    # Generate summary
                    summary = await self._generate_summary(paper, analysis)
                    
                    # Create analyzed document
                    doc = AnalyzedDocument(
                        paper=paper,
                        full_text=pdf_text[:5000],  # Store first 5000 chars
                        key_findings=analysis.get("key_findings", []),
                        methodology=analysis.get("methodology", {}),
                        pedagogical_implications=analysis.get("pedagogical_implications", []),
                        limitations=analysis.get("limitations", []),
                        future_work=analysis.get("future_work", []),
                        relevance_score=analysis.get("relevance_score", 5),
                        summary=summary,
                        extraction_metadata={
                            "pdf_length": len(pdf_text),
                            "analysis_model": self.config.model.name,
                            "extraction_timestamp": str(asyncio.get_event_loop().time())
                        }
                    )
                    
                    analyzed_docs.append(doc)
                    self.logger.info(f"Successfully analyzed: {paper.title[:50]}... (Relevance: {doc.relevance_score}/10)")
                
            except Exception as e:
                self.logger.error(f"Error analyzing paper {paper.title}: {str(e)}")
                continue
        
        # Update state
        state.analyzed_documents = analyzed_docs
        self.logger.info(f"Document analysis completed: {len(analyzed_docs)} papers successfully analyzed")
        
        return state

    async def _download_and_parse_pdf(self, paper: Paper) -> Optional[str]:
        """Download PDF and extract text content."""
        
        # Try to get PDF URL
        pdf_url = None
        if paper.pdf_url:
            pdf_url = paper.pdf_url
        elif paper.url and paper.url.endswith('.pdf'):
            pdf_url = paper.url
        elif 'arxiv.org' in paper.url:
            # Convert arXiv abstract URL to PDF URL
            arxiv_id = re.search(r'arxiv\.org/abs/(\d+\.\d+)', paper.url)
            if arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id.group(1)}.pdf"
        
        if not pdf_url:
            self.logger.warning(f"No PDF URL found for paper: {paper.title}")
            return None
        
        try:
            # Download PDF
            response = requests.get(pdf_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save to temporary file
            pdf_path = self.temp_dir / f"paper_{hash(paper.url)}.pdf"
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract text using PyMuPDF (better than PyPDF2)
            text = self._extract_text_from_pdf(pdf_path)
            
            # Clean up
            pdf_path.unlink(missing_ok=True)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error downloading/parsing PDF from {pdf_url}: {str(e)}")
            return None

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyMuPDF for better results."""
        try:
            text = ""
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
            text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII
            text = text.strip()
            
            return text
            
        except Exception as e:
            self.logger.error(f"PyMuPDF extraction failed: {e}, trying PyPDF2...")
            
            # Fallback to PyPDF2
            try:
                text = ""
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text()
                
                # Clean up text
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'[^\x00-\x7F]+', ' ', text)
                text = text.strip()
                
                return text
                
            except Exception as e2:
                self.logger.error(f"PyPDF2 extraction also failed: {e2}")
                return ""

    async def _analyze_content(self, paper: Paper, full_text: str) -> Optional[Dict[str, Any]]:
        """Analyze paper content using LLM to extract key findings."""
        
        # Truncate text if too long (keep first 8000 chars for context)
        truncated_text = full_text[:8000] if len(full_text) > 8000 else full_text
        
        try:
            # Prepare prompt using template from prompt_templates
            prompt = self.prompt_templates["key_findings"].format(
                title=paper.title,
                abstract=paper.abstract or "No abstract available",
                full_text=truncated_text
            )
            
            # Call LLM
            response = await self.llm.ainvoke(prompt)
            
            # Try to parse JSON response
            import json
            try:
                # Extract JSON from response (handle cases where LLM adds extra text)
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    return analysis
                else:
                    self.logger.warning(f"No JSON found in LLM response for {paper.title}")
                    return None
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM analysis JSON for {paper.title}: {e}")
                # Return a basic structure with raw response
                return {
                    "key_findings": [response.content[:500]],
                    "methodology": {"methods": ["Analysis unavailable"]},
                    "pedagogical_implications": ["See raw analysis"],
                    "limitations": ["Analysis parsing failed"],
                    "future_work": ["Manual review needed"],
                    "relevance_score": 5,
                    "relevance_justification": "Analysis parsing failed, manual review needed"
                }
                
        except Exception as e:
            self.logger.error(f"Error in LLM analysis for {paper.title}: {str(e)}")
            return None

    async def _generate_summary(self, paper: Paper, analysis: Dict[str, Any]) -> str:
        """Generate a concise summary of the analyzed paper."""
        
        try:
            prompt = self.prompt_templates["summary"].format(
                title=paper.title,
                key_findings=", ".join(analysis.get("key_findings", [])),
                methodology=str(analysis.get("methodology", {})),
                implications=", ".join(analysis.get("pedagogical_implications", []))
            )
            
            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating summary for {paper.title}: {str(e)}")
            return f"Summary for '{paper.title}': {analysis.get('key_findings', ['No findings available'])[0] if analysis.get('key_findings') else 'Analysis unavailable'}"

    def _cleanup_temp_files(self):
        """Clean up temporary PDF files."""
        try:
            for pdf_file in self.temp_dir.glob("*.pdf"):
                pdf_file.unlink(missing_ok=True)
        except Exception as e:
            self.logger.warning(f"Error cleaning up temp files: {e}")

    def __del__(self):
        """Cleanup when agent is destroyed."""
        self._cleanup_temp_files()