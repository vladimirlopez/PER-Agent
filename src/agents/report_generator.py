"""
Report Generator Agent - Creates professional research reports with PDF preservation.
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from langchain_core.prompts import PromptTemplate

from .base_agent import BaseAgent
from core.models import AgentState, ResearchReport, ReportFormat, ResearchQuery


class ReportGeneratorAgent(BaseAgent):
    """
    Agent responsible for generating professional research reports.
    
    Capabilities:
    - LaTeX, Markdown, and HTML report generation
    - PDF preservation and organization
    - Citation management (BibTeX, EndNote)
    - Professional formatting and styling
    - Bibliography generation
    - Research summary and recommendations
    """
    
    def __init__(self, config, ollama_host="http://localhost:11434"):
        super().__init__(config, ollama_host)
        self.logger = logging.getLogger("Report Generator")
        
        # Setup output directories
        self.setup_output_directories()
        
    def setup_output_directories(self):
        """Setup organized output directory structure."""
        self.outputs_dir = Path("research_outputs")
        self.pdfs_dir = self.outputs_dir / "pdfs"
        self.reports_dir = self.outputs_dir / "reports"
        self.citations_dir = self.outputs_dir / "citations"
        
        # Create main directories
        for dir_path in [self.outputs_dir, self.pdfs_dir, self.reports_dir, self.citations_dir]:
            dir_path.mkdir(exist_ok=True)
            
        self.logger.info(f"Output directories created: {self.outputs_dir}")
    
    def _create_research_session_folder(self, query: ResearchQuery) -> Tuple[Path, Dict[str, Path]]:
        """Create organized folder structure for the research session."""
        # Create session-specific folder name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create safe topic name from query
        topic_words = []
        for word in query.question.lower().split():
            if word.isalnum() and len(word) > 2:
                topic_words.append(word)
            if len(topic_words) >= 4:  # Limit to 4 words for folder name
                break
        
        topic_name = "_".join(topic_words) if topic_words else "research"
        session_name = f"{topic_name}_{timestamp}"
        
        # Create session folder structure
        session_dir = self.pdfs_dir / session_name
        session_dir.mkdir(exist_ok=True)
        
        # Create subfolders by source
        source_dirs = {
            'arxiv': session_dir / "arxiv",
            'semantic_scholar': session_dir / "semantic_scholar", 
            'google_scholar': session_dir / "google_scholar",
            'other': session_dir / "other_sources"
        }
        
        for source_dir in source_dirs.values():
            source_dir.mkdir(exist_ok=True)
        
        # Create session metadata file
        metadata = {
            "session_id": query.session_id,
            "research_question": query.question,
            "keywords": query.keywords,
            "domain": query.domain.value,
            "timestamp": timestamp,
            "folder_structure": {
                "session_folder": str(session_dir),
                "source_folders": {k: str(v) for k, v in source_dirs.items()}
            }
        }
        
        metadata_file = session_dir / "session_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Created organized session folder: {session_dir}")
        return session_dir, source_dirs
        
    def _initialize_prompts(self) -> Dict[str, PromptTemplate]:
        """Initialize prompts for report generation."""
        return {
            "executive_summary": PromptTemplate.from_template("""
You are an expert academic writer creating an executive summary for a physics education research report.

RESEARCH QUESTION: {research_question}
NUMBER OF PAPERS ANALYZED: {num_papers}
KEY PATTERNS: {patterns}
MAIN FINDINGS: {findings}

Create a concise executive summary (2-3 paragraphs) that:
1. States the research question and scope
2. Highlights the most significant findings
3. Presents key implications for physics education
4. Mentions the evidence base (number of papers, methodologies)

Write in professional academic tone, suitable for educators and researchers.

EXECUTIVE SUMMARY:
"""),
            
            "literature_review": PromptTemplate.from_template("""
Create a comprehensive literature review section for a physics education research report.

RESEARCH QUESTION: {research_question}
ANALYZED PAPERS: {papers_data}

For each paper, provide:
1. Citation and brief description
2. Key findings relevant to the research question
3. Methodology used
4. Significance to physics education

Organize papers thematically when possible. Identify consensus areas and disagreements.
Use academic writing style with proper transitions between papers.

LITERATURE REVIEW:
"""),
            
            "key_findings": PromptTemplate.from_template("""
Create a comprehensive "Key Findings" section for a physics education research report.

RESEARCH QUESTION: {research_question}
SYNTHESIS PATTERNS: {patterns}
EVIDENCE STRENGTH: {evidence}
CONTRADICTIONS: {contradictions}

Organize findings into:
1. **Strong Evidence Findings** (well-supported across multiple studies)
2. **Moderate Evidence Findings** (some support, needs more research)
3. **Emerging Trends** (early evidence, promising directions)
4. **Unresolved Questions** (contradictory evidence)

For each finding, mention:
- Supporting evidence
- Number of studies
- Practical implications

KEY FINDINGS:
"""),
            
            "recommendations": PromptTemplate.from_template("""
Create practical recommendations for physics educators based on research synthesis.

RESEARCH QUESTION: {research_question}
KEY PATTERNS: {patterns}
PEDAGOGICAL IMPLICATIONS: {implications}
EVIDENCE STRENGTH: {evidence}

Create recommendations in these categories:
1. **Immediate Implementation** (ready to use now)
2. **Pilot Testing** (promising but needs local validation)
3. **Long-term Development** (requires significant preparation)
4. **Research Priorities** (areas needing more study)

For each recommendation:
- Provide specific, actionable steps
- Mention evidence strength
- Include implementation considerations
- Suggest success metrics

RECOMMENDATIONS:
"""),
            
            "report_conclusion": PromptTemplate.from_template("""
Write a strong conclusion for a physics education research report.

RESEARCH QUESTION: {research_question}
MAIN FINDINGS: {main_findings}
RECOMMENDATIONS: {recommendations}
RESEARCH GAPS: {research_gaps}

The conclusion should:
1. Restate the research question and its importance
2. Summarize the most significant findings
3. Highlight implications for physics education practice
4. Identify priority areas for future research
5. End with a forward-looking statement about physics education

CONCLUSION:
""")
        }

    async def process(self, state: AgentState) -> AgentState:
        """
        Generate comprehensive research report with PDF preservation.
        
        Args:
            state: Current agent state with synthesis and analysis results
            
        Returns:
            Updated state with generated research report
        """
        self.logger.info("Starting report generation...")
        
        try:
            # Preserve PDFs from earlier processing
            await self._preserve_pdfs(state)
            
            # Generate report sections
            report_content = await self._generate_report_content(state)
            
            # Create different report formats
            reports = await self._create_reports(state, report_content)
            
            # Generate citations and bibliography
            await self._generate_citations(state)
            
            # Create research report object
            research_report = ResearchReport(
                query=state.query,
                executive_summary=report_content["executive_summary"],
                literature_review=report_content["literature_review"],
                key_findings=report_content["key_findings"],
                recommendations=report_content["recommendations"],
                conclusion=report_content["conclusion"],
                bibliography=self._create_bibliography(state),
                metadata={
                    "generation_timestamp": datetime.now().isoformat(),
                    "papers_analyzed": len(state.analyzed_documents) if hasattr(state, 'analyzed_documents') else 0,
                    "papers_validated": len(state.validated_documents) if hasattr(state, 'validated_documents') else 0,
                    "synthesis_available": hasattr(state, 'content_synthesis'),
                    "report_formats": list(reports.keys()),
                    "pdfs_preserved": len(self._get_preserved_pdfs(state)),
                    "citations_generated": True,
                    "pdf_organization": getattr(state, '_pdf_session_info', {})
                },
                file_paths=reports,
                quality_score=self._calculate_report_quality(state)
            )
            
            # Update state
            state.research_report = research_report
            
            self.logger.info(f"Report generation completed successfully")
            self.logger.info(f"Generated {len(reports)} report formats")
            self.logger.info(f"Preserved {research_report.metadata['pdfs_preserved']} PDF files")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error in report generation: {str(e)}")
            raise

    async def _preserve_pdfs(self, state: AgentState):
        """Preserve PDF files in organized folder structure."""
        if not hasattr(state, 'analyzed_documents'):
            self.logger.warning("No analyzed documents found for PDF preservation")
            return
            
        # Create organized session folder
        session_dir, source_dirs = self._create_research_session_folder(state.query)
        
        preserved_count = 0
        preservation_log = []
        
        for doc in state.analyzed_documents:
            if doc.paper.pdf_url:
                try:
                    # Determine source directory
                    source = doc.paper.source.lower()
                    if source in source_dirs:
                        target_dir = source_dirs[source]
                    else:
                        target_dir = source_dirs['other']
                    
                    # Create enhanced filename with metadata
                    safe_title = "".join(c for c in doc.paper.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    safe_title = safe_title[:40]  # Reasonable length
                    
                    # Add author and year if available
                    author_part = ""
                    if doc.paper.authors:
                        first_author = doc.paper.authors[0].split()[-1] if doc.paper.authors[0] else ""
                        author_part = f"_{first_author}" if first_author else ""
                    
                    year_part = ""
                    if doc.paper.published_date:
                        year_part = f"_{doc.paper.published_date.year}"
                    
                    # Create filename: Title_Author_Year_Source.pdf
                    pdf_filename = f"{safe_title}{author_part}{year_part}_{source}.pdf"
                    pdf_path = target_dir / pdf_filename
                    
                    # Download PDF if not already exists
                    if not pdf_path.exists():
                        import requests
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        response = requests.get(doc.paper.pdf_url, timeout=30, headers=headers)
                        response.raise_for_status()
                        
                        with open(pdf_path, 'wb') as f:
                            f.write(response.content)
                        
                        preserved_count += 1
                        
                        # Log preservation details
                        preservation_info = {
                            "title": doc.paper.title,
                            "source": source,
                            "file_path": str(pdf_path),
                            "pdf_url": doc.paper.pdf_url,
                            "file_size": pdf_path.stat().st_size,
                            "authors": doc.paper.authors
                        }
                        preservation_log.append(preservation_info)
                        
                        self.logger.info(f"Preserved PDF: {pdf_filename} → {target_dir.name}/")
                    else:
                        self.logger.info(f"PDF already exists: {pdf_filename}")
                    
                except Exception as e:
                    self.logger.warning(f"Could not preserve PDF for {doc.paper.title}: {e}")
        
        # Create preservation summary
        summary_file = session_dir / "pdf_preservation_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "session_summary": {
                    "total_papers_analyzed": len(state.analyzed_documents),
                    "pdfs_preserved": preserved_count,
                    "preservation_timestamp": datetime.now().isoformat(),
                    "session_folder": str(session_dir)
                },
                "preserved_files": preservation_log
            }, f, indent=2)
        
        # Store session info in state for report generation
        if not hasattr(state, '_pdf_session_info'):
            state._pdf_session_info = {
                "session_dir": session_dir,
                "source_dirs": source_dirs,
                "preserved_count": preserved_count
            }
        
        self.logger.info(f"PDF preservation completed: {preserved_count} files preserved in organized structure")
        self.logger.info(f"Session folder: {session_dir}")
        self.logger.info(f"Organized by source: {list(source_dirs.keys())}")

    async def _generate_report_content(self, state: AgentState) -> Dict[str, str]:
        """Generate all report sections using LLM."""
        self.logger.info("Generating report content sections...")
        
        # Prepare data for prompts
        research_question = state.query.question
        num_papers = len(state.analyzed_documents) if hasattr(state, 'analyzed_documents') else 0
        
        # Extract synthesis data if available
        patterns = []
        evidence = {}
        contradictions = []
        if hasattr(state, 'content_synthesis') and state.content_synthesis:
            patterns = [p.description for p in state.content_synthesis.patterns]
            evidence = state.content_synthesis.evidence_synthesis
            contradictions = [c.description for c in state.content_synthesis.contradictions]
        
        # Extract analyzed papers data
        papers_data = []
        if hasattr(state, 'analyzed_documents'):
            for doc in state.analyzed_documents:
                papers_data.append({
                    "title": doc.paper.title,
                    "authors": doc.paper.authors,
                    "key_findings": doc.key_findings,
                    "methodology": doc.methodology,
                    "implications": doc.pedagogical_implications
                })
        
        report_content = {}
        
        # Generate executive summary
        try:
            prompt = self.prompt_templates["executive_summary"].format(
                research_question=research_question,
                num_papers=num_papers,
                patterns=patterns[:3],  # Top 3 patterns
                findings=[p for p in patterns[:3]]
            )
            response = await self.llm.ainvoke(prompt)
            report_content["executive_summary"] = self._extract_text(response)
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {e}")
            report_content["executive_summary"] = f"Executive summary generation failed: {e}"
        
        # Generate literature review
        try:
            prompt = self.prompt_templates["literature_review"].format(
                research_question=research_question,
                papers_data=json.dumps(papers_data, indent=2)
            )
            response = await self.llm.ainvoke(prompt)
            report_content["literature_review"] = self._extract_text(response)
        except Exception as e:
            self.logger.error(f"Error generating literature review: {e}")
            report_content["literature_review"] = f"Literature review generation failed: {e}"
        
        # Generate key findings
        try:
            prompt = self.prompt_templates["key_findings"].format(
                research_question=research_question,
                patterns=patterns,
                evidence=str(evidence),
                contradictions=contradictions
            )
            response = await self.llm.ainvoke(prompt)
            report_content["key_findings"] = self._extract_text(response)
        except Exception as e:
            self.logger.error(f"Error generating key findings: {e}")
            report_content["key_findings"] = f"Key findings generation failed: {e}"
        
        # Generate recommendations
        try:
            implications = []
            if hasattr(state, 'analyzed_documents'):
                for doc in state.analyzed_documents:
                    implications.extend(doc.pedagogical_implications)
            
            prompt = self.prompt_templates["recommendations"].format(
                research_question=research_question,
                patterns=patterns,
                implications=implications,
                evidence=str(evidence)
            )
            response = await self.llm.ainvoke(prompt)
            report_content["recommendations"] = self._extract_text(response)
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            report_content["recommendations"] = f"Recommendations generation failed: {e}"
        
        # Generate conclusion
        try:
            prompt = self.prompt_templates["report_conclusion"].format(
                research_question=research_question,
                main_findings=patterns[:3],
                recommendations=report_content.get("recommendations", ""),
                research_gaps=getattr(state.content_synthesis, 'research_gaps', []) if hasattr(state, 'content_synthesis') else []
            )
            response = await self.llm.ainvoke(prompt)
            report_content["conclusion"] = self._extract_text(response)
        except Exception as e:
            self.logger.error(f"Error generating conclusion: {e}")
            report_content["conclusion"] = f"Conclusion generation failed: {e}"
        
        self.logger.info("Report content generation completed")
        return report_content

    def _extract_text(self, response) -> str:
        """Extract text from LLM response."""
        if hasattr(response, 'content'):
            return response.content.strip()
        elif isinstance(response, str):
            return response.strip()
        else:
            return str(response).strip()

    async def _create_reports(self, state: AgentState, report_content: Dict[str, str]) -> Dict[str, str]:
        """Create reports in different formats."""
        reports = {}
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_short = "".join(c for c in state.query.question[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
        
        # Markdown report
        markdown_path = self.reports_dir / f"research_report_{query_short}_{timestamp}.md"
        markdown_content = self._create_markdown_report(state, report_content)
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        reports["markdown"] = str(markdown_path)
        
        # HTML report  
        html_path = self.reports_dir / f"research_report_{query_short}_{timestamp}.html"
        html_content = self._create_html_report(state, report_content)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        reports["html"] = str(html_path)
        
        # LaTeX report
        latex_path = self.reports_dir / f"research_report_{query_short}_{timestamp}.tex"
        latex_content = self._create_latex_report(state, report_content)
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        reports["latex"] = str(latex_path)
        
        self.logger.info(f"Created reports: {list(reports.keys())}")
        return reports

    def _create_markdown_report(self, state: AgentState, content: Dict[str, str]) -> str:
        """Create Markdown format report."""
        preserved_pdfs = self._get_preserved_pdfs(state)
        
        # Get organized folder info if available
        pdf_organization = ""
        if hasattr(state, '_pdf_session_info'):
            session_info = state._pdf_session_info
            session_dir = session_info["session_dir"]
            pdf_organization = f"""

## PDF Organization

**Session Folder:** `{session_dir}`

The research papers have been organized by source:
"""
            for source, source_dir in session_info["source_dirs"].items():
                source_pdfs = list(source_dir.glob("*.pdf"))
                if source_pdfs:
                    pdf_organization += f"\n### {source.replace('_', ' ').title()} ({len(source_pdfs)} papers)\n"
                    pdf_organization += f"**Folder:** `{source_dir}`\n\n"
                    for pdf_file in source_pdfs:
                        pdf_organization += f"- [{pdf_file.name}]({pdf_file})\n"
                    pdf_organization += "\n"
        
        md = f"""# Physics Education Research Report

**Research Question:** {state.query.question}

**Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

**Analysis Summary:**
- Papers analyzed: {len(state.analyzed_documents) if hasattr(state, 'analyzed_documents') else 0}
- PDFs preserved: {len(preserved_pdfs)}
- Synthesis completed: {'Yes' if hasattr(state, 'content_synthesis') else 'No'}

---

## Executive Summary

{content['executive_summary']}

---

## Literature Review

{content['literature_review']}

---

## Key Findings

{content['key_findings']}

---

## Recommendations for Physics Educators

{content['recommendations']}

---

## Conclusion

{content['conclusion']}

---

## Bibliography

{self._create_bibliography(state)}

---
{pdf_organization}

## All Preserved Research Papers

Total papers preserved: {len(preserved_pdfs)}

"""
        
        if not pdf_organization:  # Fallback for simple listing
            for pdf_path in preserved_pdfs:
                md += f"- [{pdf_path.name}]({pdf_path})\n"
        
        md += f"""
---

*Report generated by PER Agent v1.0 - Physics Education Research Assistant*
*For questions about this report, please review the methodology and source papers.*
"""
        
        return md

    def _create_html_report(self, state: AgentState, content: Dict[str, str]) -> str:
        """Create HTML format report."""
        preserved_pdfs = self._get_preserved_pdfs(state)
        
        # Create organized PDF section
        pdf_section = ""
        if hasattr(state, '_pdf_session_info'):
            session_info = state._pdf_session_info
            pdf_section = """
    <div class="section">
        <h2>Research Papers - Organized by Source</h2>
        <div class="pdf-organization">
"""
            for source, source_dir in session_info["source_dirs"].items():
                source_pdfs = list(source_dir.glob("*.pdf"))
                if source_pdfs:
                    pdf_section += f"""
            <h3>{source.replace('_', ' ').title()} ({len(source_pdfs)} papers)</h3>
            <div class="pdf-list">
"""
                    for pdf_file in source_pdfs:
                        pdf_section += f'                <a href="{pdf_file}" target="_blank">{pdf_file.name}</a>\n'
                    pdf_section += "            </div>\n"
            
            pdf_section += """        </div>
    </div>"""
        else:
            # Fallback to simple listing
            pdf_section = """
    <div class="section">
        <h2>Preserved Research Papers</h2>
        <div class="pdf-list">
"""
            for pdf_path in preserved_pdfs:
                pdf_section += f'            <a href="{pdf_path}" target="_blank">{pdf_path.name}</a>\n'
            pdf_section += """        </div>
    </div>"""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Physics Education Research Report</title>
    <style>
        body {{ font-family: 'Georgia', serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
        .metadata {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .pdf-list {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
        .pdf-list a {{ display: block; margin: 5px 0; color: #2980b9; text-decoration: none; }}
        .pdf-list a:hover {{ text-decoration: underline; }}
        .pdf-organization {{ margin: 20px 0; }}
        .pdf-organization h3 {{ color: #27ae60; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>Physics Education Research Report</h1>
    
    <div class="metadata">
        <strong>Research Question:</strong> {state.query.question}<br>
        <strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %I:%M %p")}<br>
        <strong>Papers Analyzed:</strong> {len(state.analyzed_documents) if hasattr(state, 'analyzed_documents') else 0}<br>
        <strong>PDFs Preserved:</strong> {len(preserved_pdfs)}
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <p>{content['executive_summary'].replace('\n', '</p><p>')}</p>
    </div>
    
    <div class="section">
        <h2>Literature Review</h2>
        <p>{content['literature_review'].replace('\n', '</p><p>')}</p>
    </div>
    
    <div class="section">
        <h2>Key Findings</h2>
        <p>{content['key_findings'].replace('\n', '</p><p>')}</p>
    </div>
    
    <div class="section">
        <h2>Recommendations for Physics Educators</h2>
        <p>{content['recommendations'].replace('\n', '</p><p>')}</p>
    </div>
    
    <div class="section">
        <h2>Conclusion</h2>
        <p>{content['conclusion'].replace('\n', '</p><p>')}</p>
    </div>
    
    <div class="section">
        <h2>Bibliography</h2>
        <p>{self._create_bibliography(state).replace('\n', '</p><p>')}</p>
    </div>
    {pdf_section}
    
    <footer style="margin-top: 50px; text-align: center; color: #7f8c8d; font-style: italic;">
        Report generated by PER Agent v1.0 - Physics Education Research Assistant
    </footer>
</body>
</html>"""
        
        return html

    def _create_latex_report(self, state: AgentState, content: Dict[str, str]) -> str:
        """Create LaTeX format report."""
        preserved_pdfs = self._get_preserved_pdfs(state)
        
        # Create organized PDF section for LaTeX
        pdf_section = ""
        if hasattr(state, '_pdf_session_info'):
            session_info = state._pdf_session_info
            pdf_section = "\\section{Research Papers - Organized by Source}\n\n"
            
            for source, source_dir in session_info["source_dirs"].items():
                source_pdfs = list(source_dir.glob("*.pdf"))
                if source_pdfs:
                    source_title = source.replace('_', ' ').title()
                    pdf_section += f"\\subsection{{{source_title} ({len(source_pdfs)} papers)}}\n\n"
                    pdf_section += "\\begin{itemize}\n"
                    for pdf_file in source_pdfs:
                        pdf_section += f"    \\item \\texttt{{{self._escape_latex(pdf_file.name)}}}\n"
                    pdf_section += "\\end{itemize}\n\n"
        else:
            # Fallback to simple listing
            pdf_section = "\\section{Preserved Research Papers}\n\n"
            pdf_section += "The following PDF files have been preserved for reference:\n\n"
            pdf_section += "\\begin{itemize}\n"
            for pdf_path in preserved_pdfs:
                pdf_section += f"    \\item \\texttt{{{self._escape_latex(pdf_path.name)}}}\n"
            pdf_section += "\\end{itemize}\n\n"
        
        latex = f"""\\documentclass[12pt,article]{{memoir}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{lmodern}}
\\usepackage{{microtype}}
\\usepackage{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{booktabs}}
\\usepackage{{graphicx}}

\\geometry{{a4paper,left=1in,right=1in,top=1in,bottom=1in}}
\\hypersetup{{
    colorlinks=true,
    linkcolor=blue,
    urlcolor=blue,
    citecolor=blue
}}

\\title{{Physics Education Research Report}}
\\author{{PER Agent Research System}}
\\date{{{datetime.now().strftime("%B %d, %Y")}}}

\\begin{{document}}

\\maketitle

\\section*{{Research Question}}
{state.query.question}

\\section*{{Analysis Summary}}
\\begin{{itemize}}
    \\item Papers analyzed: {len(state.analyzed_documents) if hasattr(state, 'analyzed_documents') else 0}
    \\item PDFs preserved: {len(preserved_pdfs)}
    \\item Synthesis completed: {'Yes' if hasattr(state, 'content_synthesis') else 'No'}
\\end{{itemize}}

\\section{{Executive Summary}}
{self._escape_latex(content['executive_summary'])}

\\section{{Literature Review}}
{self._escape_latex(content['literature_review'])}

\\section{{Key Findings}}
{self._escape_latex(content['key_findings'])}

\\section{{Recommendations for Physics Educators}}
{self._escape_latex(content['recommendations'])}

\\section{{Conclusion}}
{self._escape_latex(content['conclusion'])}

\\section{{Bibliography}}
{self._escape_latex(self._create_bibliography(state))}

{pdf_section}

\\end{{document}}"""
        
        return latex

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        replacements = {
            '&': '\\&',
            '%': '\\%', 
            '$': '\\$',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '~': '\\textasciitilde{}',
            '\\': '\\textbackslash{}'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text

    async def _generate_citations(self, state: AgentState):
        """Generate citation files (BibTeX, EndNote)."""
        if not hasattr(state, 'analyzed_documents'):
            return
            
        # Generate BibTeX
        bibtex_content = self._create_bibtex(state.analyzed_documents)
        bibtex_path = self.citations_dir / f"references_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bib"
        with open(bibtex_path, 'w', encoding='utf-8') as f:
            f.write(bibtex_content)
        
        # Generate plain text bibliography
        bibliography = self._create_bibliography(state)
        bib_path = self.citations_dir / f"bibliography_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(bib_path, 'w', encoding='utf-8') as f:
            f.write(bibliography)
        
        self.logger.info(f"Generated citations: {bibtex_path}, {bib_path}")

    def _create_bibtex(self, analyzed_docs) -> str:
        """Create BibTeX citation format."""
        bibtex = "% BibTeX Bibliography generated by PER Agent\n\n"
        
        for i, doc in enumerate(analyzed_docs, 1):
            paper = doc.paper
            # Create safe citation key
            first_author = paper.authors[0].split()[-1] if paper.authors else "Unknown"
            year = paper.published_date.year if paper.published_date else "Unknown"
            title_words = paper.title.split()[:2]
            key = f"{first_author}{year}{''.join(title_words)}"
            key = "".join(c for c in key if c.isalnum())
            
            bibtex += f"@article{{{key},\n"
            bibtex += f"  title={{{paper.title}}},\n"
            bibtex += f"  author={{{' and '.join(paper.authors)}}},\n"
            if paper.journal:
                bibtex += f"  journal={{{paper.journal}}},\n"
            if paper.published_date:
                bibtex += f"  year={{{paper.published_date.year}}},\n"
            if paper.doi:
                bibtex += f"  doi={{{paper.doi}}},\n"
            bibtex += f"  url={{{paper.url}}},\n"
            if paper.pdf_url:
                bibtex += f"  note={{PDF available: {paper.pdf_url}}},\n"
            bibtex += "}\n\n"
        
        return bibtex

    def _create_bibliography(self, state: AgentState) -> str:
        """Create formatted bibliography."""
        if not hasattr(state, 'analyzed_documents'):
            return "No papers analyzed."
            
        bibliography = []
        
        for doc in state.analyzed_documents:
            paper = doc.paper
            # Format: Author(s). (Year). Title. Journal. DOI/URL.
            authors = ", ".join(paper.authors) if len(paper.authors) <= 3 else f"{paper.authors[0]} et al."
            year = f"({paper.published_date.year})" if paper.published_date else "(Year unknown)"
            title = paper.title
            
            citation = f"{authors} {year}. {title}."
            
            if paper.journal:
                citation += f" {paper.journal}."
            
            if paper.doi:
                citation += f" DOI: {paper.doi}"
            elif paper.url:
                citation += f" Available: {paper.url}"
            
            bibliography.append(citation)
        
        return "\n\n".join(bibliography)

    def _get_preserved_pdfs(self, state: AgentState = None) -> List[Path]:
        """Get list of preserved PDF files from current session."""
        if state and hasattr(state, '_pdf_session_info'):
            # Get PDFs from current session
            session_dir = state._pdf_session_info["session_dir"]
            preserved_pdfs = []
            for pdf_file in session_dir.rglob("*.pdf"):
                preserved_pdfs.append(pdf_file)
            return preserved_pdfs
        else:
            # Fallback: get all PDFs from pdfs directory
            if not self.pdfs_dir.exists():
                return []
            return list(self.pdfs_dir.rglob("*.pdf"))

    def _calculate_report_quality(self, state: AgentState) -> float:
        """Calculate overall report quality score."""
        score = 0.0
        max_score = 5.0
        
        # Literature coverage (1 point)
        if hasattr(state, 'analyzed_documents') and len(state.analyzed_documents) > 0:
            score += min(1.0, len(state.analyzed_documents) / 5.0)  # Full point for 5+ papers
        
        # Content analysis quality (1 point) 
        if hasattr(state, 'analyzed_documents') and len(state.analyzed_documents) > 0:
            analysis_quality = sum(doc.relevance_score for doc in state.analyzed_documents) / len(state.analyzed_documents) / 10.0
            score += analysis_quality
        
        # Physics validation (1 point)
        if hasattr(state, 'validated_documents') and len(state.validated_documents) > 0:
            validation_quality = sum(v.overall_accuracy for v in state.validated_documents) / len(state.validated_documents)
            score += validation_quality
        
        # Content synthesis (1 point)
        if hasattr(state, 'content_synthesis') and state.content_synthesis:
            synthesis_quality = len(state.content_synthesis.patterns) / 10.0  # Quality based on pattern richness
            score += min(1.0, synthesis_quality)
        
        # Report completeness (1 point)
        completeness = 1.0  # Base score for having a complete report
        score += completeness
        
        return min(1.0, score / max_score)