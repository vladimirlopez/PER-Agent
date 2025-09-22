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
        """Download PDF and extract text content with multiple fallback strategies."""
        
        # Try multiple PDF URL strategies
        pdf_urls = []
        
        # Primary PDF URL
        if paper.pdf_url:
            pdf_urls.append(paper.pdf_url)
        
        # Direct PDF links
        if paper.url and paper.url.endswith('.pdf'):
            pdf_urls.append(paper.url)
        
        # arXiv specific handling
        if 'arxiv.org' in paper.url:
            arxiv_id = re.search(r'arxiv\.org/abs/(\d+\.\d+)', paper.url)
            if arxiv_id:
                pdf_urls.append(f"https://arxiv.org/pdf/{arxiv_id.group(1)}.pdf")
                # Try alternative arXiv formats
                pdf_urls.append(f"https://export.arxiv.org/pdf/{arxiv_id.group(1)}.pdf")
        
        # Semantic Scholar PDF links (they sometimes provide direct URLs)
        if paper.pdf_url and 'semanticscholar.org' in paper.pdf_url:
            pdf_urls.append(paper.pdf_url)
        
        # Remove duplicates while preserving order
        pdf_urls = list(dict.fromkeys(pdf_urls))
        
        if not pdf_urls:
            self.logger.warning(f"No PDF URLs found for paper: {paper.title}")
            return None
        
        # Try each URL until one works
        for i, pdf_url in enumerate(pdf_urls, 1):
            self.logger.info(f"Trying PDF URL {i}/{len(pdf_urls)}: {pdf_url[:60]}...")
            
            try:
                # Set headers to appear more like a browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'application/pdf,application/octet-stream,*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                # Download PDF with timeout and headers
                response = requests.get(pdf_url, timeout=45, stream=True, headers=headers, allow_redirects=True)
                response.raise_for_status()
                
                # Check if response is actually a PDF
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' not in content_type and len(response.content) < 1000:
                    self.logger.warning(f"Response doesn't look like PDF: {content_type}")
                    continue
                
                # Save to temporary file
                pdf_path = self.temp_dir / f"paper_{hash(paper.url)}_{i}.pdf"
                with open(pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verify file size
                if pdf_path.stat().st_size < 1000:
                    self.logger.warning(f"Downloaded file too small: {pdf_path.stat().st_size} bytes")
                    pdf_path.unlink(missing_ok=True)
                    continue
                
                # Extract text using PyMuPDF (better than PyPDF2)
                text = self._extract_text_from_pdf(pdf_path)
                
                # Clean up
                pdf_path.unlink(missing_ok=True)
                
                if text and len(text.strip()) > 100:  # Ensure we got meaningful text
                    self.logger.info(f"Successfully extracted {len(text)} characters from PDF")
                    return text
                else:
                    self.logger.warning(f"Extracted text too short or empty: {len(text) if text else 0} chars")
                    continue
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed for {pdf_url}: {str(e)}")
                continue
            except Exception as e:
                self.logger.warning(f"Error processing PDF from {pdf_url}: {str(e)}")
                continue
        
        self.logger.error(f"All PDF download attempts failed for paper: {paper.title}")
        return None

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF using multiple methods for best results."""
        text = ""
        
        # Try PyMuPDF first (usually better)
        try:
            with fitz.open(pdf_path) as doc:
                self.logger.info(f"PDF has {len(doc)} pages")
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text()
                    
                    # Skip pages with very little text (likely images/figures)
                    if len(page_text.strip()) > 50:
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text
                
                # Clean up text
                text = self._clean_extracted_text(text)
                
                if len(text.strip()) > 100:
                    self.logger.info(f"PyMuPDF extracted {len(text)} characters successfully")
                    return text
                
        except Exception as e:
            self.logger.warning(f"PyMuPDF extraction failed: {e}")
        
        # Fallback to PyPDF2
        try:
            self.logger.info("Trying PyPDF2 as fallback...")
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                self.logger.info(f"PDF has {len(reader.pages)} pages (PyPDF2)")
                
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if len(page_text.strip()) > 50:
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text
            
            # Clean up text
            text = self._clean_extracted_text(text)
            
            if len(text.strip()) > 100:
                self.logger.info(f"PyPDF2 extracted {len(text)} characters successfully")
                return text
                
        except Exception as e:
            self.logger.error(f"PyPDF2 extraction also failed: {e}")
        
        self.logger.error("All text extraction methods failed")
        return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace but preserve paragraph breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple line breaks to double
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n ', '\n', text)  # Remove spaces at start of lines
        
        # Remove non-printable characters but keep common ones
        text = re.sub(r'[^\x20-\x7E\n\t]', ' ', text)
        
        # Remove header/footer patterns that appear on every page
        text = re.sub(r'\n--- Page \d+ ---\n', '\n', text)
        
        # Remove common PDF artifacts
        text = re.sub(r'\n\d+\n', '\n', text)  # Lone page numbers
        text = re.sub(r'\nreferences?\n', '\nREFERENCES\n', text, flags=re.IGNORECASE)
        
        return text.strip()

    async def _analyze_content(self, paper: Paper, full_text: str) -> Optional[Dict[str, Any]]:
        """Analyze paper content using LLM to extract key findings with timeout handling."""
        
        # Truncate text if too long (keep first 6000 chars for context)
        truncated_text = full_text[:6000] if len(full_text) > 6000 else full_text
        
        # Add some basic info if text is very short
        if len(truncated_text.strip()) < 200:
            self.logger.warning(f"Very short text extracted ({len(truncated_text)} chars), analysis may be limited")
        
        try:
            # Prepare prompt using template
            prompt = self.prompt_templates["key_findings"].format(
                title=paper.title,
                abstract=paper.abstract or "No abstract available",
                full_text=truncated_text
            )
            
            # Call LLM with timeout
            self.logger.info(f"Sending {len(prompt)} characters to LLM for analysis...")
            
            # Add timeout wrapper
            import asyncio
            response = await asyncio.wait_for(
                self.llm.ainvoke(prompt),
                timeout=120.0  # 2 minute timeout
            )
            
            # Handle different response types
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
            
            self.logger.info(f"Received LLM response: {len(response_text)} characters")
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (handle cases where LLM adds extra text)
                
                # Look for JSON block
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group()
                    analysis = json.loads(json_text)
                    
                    # Validate that we got expected fields
                    required_fields = ["key_findings", "methodology", "pedagogical_implications", "relevance_score"]
                    missing_fields = [f for f in required_fields if f not in analysis]
                    
                    if missing_fields:
                        self.logger.warning(f"Missing fields in analysis: {missing_fields}")
                        # Fill in missing fields with defaults
                        if "key_findings" not in analysis:
                            analysis["key_findings"] = ["Analysis incomplete - see raw response"]
                        if "methodology" not in analysis:
                            analysis["methodology"] = {"methods": ["Not specified"]}
                        if "pedagogical_implications" not in analysis:
                            analysis["pedagogical_implications"] = ["Analysis incomplete"]
                        if "relevance_score" not in analysis:
                            analysis["relevance_score"] = 5
                    
                    self.logger.info(f"Successfully parsed analysis with {len(analysis.get('key_findings', []))} findings")
                    return analysis
                    
                else:
                    self.logger.warning(f"No JSON found in LLM response for {paper.title}")
                    # Try to extract at least some information from plain text
                    return self._create_fallback_analysis(response_text, paper.title)
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM analysis JSON for {paper.title}: {e}")
                # Return a basic structure with raw response
                return self._create_fallback_analysis(response_text, paper.title)
                
        except asyncio.TimeoutError:
            self.logger.error(f"LLM analysis timed out for {paper.title}")
            return self._create_fallback_analysis("Analysis timed out", paper.title)
        except Exception as e:
            self.logger.error(f"Error in LLM analysis for {paper.title}: {str(e)}")
            return self._create_fallback_analysis(f"Analysis failed: {str(e)}", paper.title)
    
    def _create_fallback_analysis(self, response_text: str, paper_title: str) -> Dict[str, Any]:
        """Create a basic analysis structure when JSON parsing fails."""
        return {
            "key_findings": [f"Analysis parsing failed for '{paper_title}'. Raw response: {response_text[:200]}..."],
            "methodology": {"methods": ["Analysis unavailable"], "sample_size": "Unknown", "data_collection": "Unknown"},
            "pedagogical_implications": ["Manual review needed for proper analysis"],
            "limitations": ["Automated analysis failed"],
            "future_work": ["Requires manual review"],
            "relevance_score": 5,
            "relevance_justification": "Analysis parsing failed, manual review needed"
        }

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
            
            # Handle different response types
            if hasattr(response, 'content'):
                summary = response.content.strip()
            elif isinstance(response, str):
                summary = response.strip()
            else:
                summary = str(response).strip()
            
            return summary
            
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