"""
Literature Scout Agent - Searches and ranks academic papers.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

import arxiv
import requests
from langchain_core.prompts import PromptTemplate

from .base_agent import BaseAgent
from core.models import AgentState, Paper, ResearchDomain
from core.credentials import PremiumCredentials


class LiteratureScoutAgent(BaseAgent):
    """
    Agent responsible for searching academic literature across multiple sources.
    
    Capabilities:
    - arXiv API integration
    - Semantic Scholar API integration  
    - Google Scholar scraping (optional)
    - Paper ranking and relevance scoring
    - Metadata extraction and normalization
    """
    
    def __init__(self, config, ollama_host: str = "http://localhost:11434"):
        """Initialize the Literature Scout Agent with premium database access."""
        super().__init__(config, ollama_host)
        
        # Initialize premium credentials
        self.credentials = PremiumCredentials()
        
        # API configurations
        self.arxiv_client = arxiv.Client()
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
        self.max_retries = 3
        self.rate_limit_delay = 1.0  # seconds between requests
        
        # Search result limits
        self.max_arxiv_results = 50
        self.max_semantic_scholar_results = 50
        
        # Log available premium access
        premium_sources = []
        if self.credentials.has_aip_access():
            premium_sources.append("AIP Publishing")
        if self.credentials.has_compadre_access():
            premium_sources.append("ComPADRE")
        if self.credentials.has_per_central_access():
            premium_sources.append("PER Central")
        
        if premium_sources:
            self.logger.info(f"Premium access available: {', '.join(premium_sources)}")
        else:
            self.logger.info("Using free sources only (add credentials to .env for premium access)")
        
        self.logger.info("Literature Scout Agent initialized successfully")
    
    def _initialize_prompts(self) -> Dict[str, PromptTemplate]:
        """Initialize prompt templates for the Literature Scout Agent."""
        
        system_prompt = self._create_system_prompt(
            role_description="You search and evaluate academic literature for physics education research",
            capabilities=[
                "Search academic databases (arXiv, Semantic Scholar)",
                "Evaluate paper relevance to research questions",
                "Extract and normalize paper metadata",
                "Rank papers by educational impact and quality",
                "Filter papers by domain and keywords"
            ]
        )
        
        ranking_prompt = PromptTemplate.from_template(f"""
{system_prompt}

TASK: Rank and score academic papers for relevance to a physics education research question.

RESEARCH QUESTION: {{question}}
RESEARCH DOMAIN: {{domain}}
KEYWORDS: {{keywords}}

PAPERS TO EVALUATE:
{{papers_data}}

For each paper, provide a relevance score (0.0-1.0) and brief justification.

SCORING CRITERIA:
- Direct relevance to research question (40%)
- Physics education focus vs general physics (30%) 
- Research quality and methodology (20%)
- Recent publication and citations (10%)

RESPONSE FORMAT:
For each paper, respond with:
Paper ID: [id]
Score: [0.0-1.0]
Justification: [2-3 sentences explaining the score]
Key Physics Concepts: [list of main physics topics]
Educational Methods: [teaching/learning approaches mentioned]

---

Begin evaluation:
""")
        
        keyword_extraction_prompt = PromptTemplate.from_template(f"""
{system_prompt}

TASK: Extract and suggest relevant search keywords for physics education research.

RESEARCH QUESTION: {{question}}
DOMAIN: {{domain}}
USER KEYWORDS: {{user_keywords}}

Generate optimized search keywords for academic databases:

1. CORE PHYSICS CONCEPTS: List specific physics topics/concepts
2. EDUCATIONAL TERMS: Teaching, learning, pedagogy terms  
3. METHODOLOGY TERMS: Research methods, assessment, evaluation
4. TECHNOLOGY TERMS: Tools, simulations, digital resources
5. AUDIENCE TERMS: Student level, demographics, context

Provide 15-20 total keywords optimized for academic search engines.
Focus on terms that would appear in titles, abstracts, and keywords.

KEYWORDS:
""")
        
        return {
            "ranking": ranking_prompt,
            "keyword_extraction": keyword_extraction_prompt
        }
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Main processing method for literature search and ranking.
        
        Args:
            state: Current workflow state with research query
            
        Returns:
            Dictionary containing search results and metadata
        """
        if not self._validate_input(state):
            return self._handle_error(ValueError("Invalid input state"), "Literature search validation")
        
        try:
            self.logger.info(f"Starting literature search for: {state.query.question[:100]}...")
            
            # Step 1: Enhance keywords using LLM
            enhanced_keywords = await self._enhance_keywords(state.query)
            
            # Step 2: Search multiple sources (including premium databases)
            search_tasks = [
                self._search_arxiv(state.query, enhanced_keywords),
                self._search_semantic_scholar(state.query, enhanced_keywords),
                self._search_aip_publications(state.query, enhanced_keywords),
                self._search_compadre(state.query, enhanced_keywords),
                self._search_per_central(state.query, enhanced_keywords)
            ]
            
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            all_papers = []
            for i, result in enumerate(search_results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Search source {i} failed: {result}")
                    continue
                all_papers.extend(result)
            
            self.logger.info(f"Found {len(all_papers)} papers from all sources")
            
            # Step 3: Remove duplicates and rank papers
            unique_papers = self._deduplicate_papers(all_papers)
            self.logger.info(f"After deduplication: {len(unique_papers)} unique papers")
            
            # Step 4: Rank papers using LLM
            ranked_papers = await self._rank_papers(state.query, unique_papers)
            
            # Step 5: Apply filters and limits
            filtered_papers = self._apply_filters(ranked_papers, state.query)
            
            self.logger.info(f"Final selection: {len(filtered_papers)} papers")
            
            # Update the state with the results
            state.papers = filtered_papers
            state.search_metadata = {
                "success": True,
                "total_found": len(all_papers),
                "unique_count": len(unique_papers),
                "final_count": len(filtered_papers),
                "enhanced_keywords": enhanced_keywords,
                "arxiv_results": len(search_results[0]) if not isinstance(search_results[0], Exception) else 0,
                "semantic_scholar_results": len(search_results[1]) if not isinstance(search_results[1], Exception) else 0,
            }
            
            return state
            
        except Exception as e:
            self.logger.error(f"Literature search processing failed: {e}")
            state.errors.append(f"Literature search error: {e}")
            return state
    
    async def _enhance_keywords(self, query) -> List[str]:
        """Use LLM to enhance and expand search keywords."""
        try:
            user_keywords = ", ".join(query.keywords) if query.keywords else "None provided"
            
            enhanced = await self._execute_llm_chain(
                "keyword_extraction",
                question=query.question,
                domain=query.domain.value,
                user_keywords=user_keywords
            )
            
            # Parse keywords from LLM response
            keywords = []
            for line in enhanced.split('\n'):
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    # Extract keywords after colon
                    keyword_part = line.split(':', 1)[1].strip()
                    # Split by commas and clean
                    line_keywords = [k.strip().strip('"\'') for k in keyword_part.split(',')]
                    keywords.extend([k for k in line_keywords if k and len(k) > 2])
            
            # Add original user keywords
            if query.keywords:
                keywords.extend(query.keywords)
            
            # Remove duplicates and limit
            unique_keywords = list(dict.fromkeys(keywords))[:25]
            
            self.logger.info(f"Enhanced keywords: {len(unique_keywords)} total")
            return unique_keywords
            
        except Exception as e:
            self.logger.warning(f"Keyword enhancement failed: {e}, using original keywords")
            return query.keywords or []
    
    async def _search_arxiv(self, query, keywords: List[str]) -> List[Paper]:
        """Search arXiv for relevant papers."""
        try:
            # Build arXiv search query
            search_terms = []
            
            # Add main question terms
            question_terms = re.findall(r'\b\w{4,}\b', query.question.lower())
            search_terms.extend(question_terms[:5])  # Limit to avoid too complex queries
            
            # Add selected keywords
            search_terms.extend(keywords[:10])
            
            # Create search string
            search_query = " OR ".join(f'"{term}"' for term in search_terms[:15])
            
            self.logger.info(f"arXiv search query: {search_query[:100]}...")
            
            # Execute search
            search = arxiv.Search(
                query=search_query,
                max_results=min(self.max_arxiv_results, query.max_sources),
                sort_by=arxiv.SortCriterion.Relevance,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            async def fetch_arxiv_papers():
                for result in self.arxiv_client.results(search):
                    try:
                        paper = Paper(
                            title=result.title,
                            authors=[str(author) for author in result.authors],
                            abstract=result.summary,
                            url=result.entry_id,
                            arxiv_id=result.get_short_id(),
                            doi=result.doi,
                            published_date=result.published,
                            journal=result.journal_ref,
                            source="arxiv",
                            keywords=[],  # Will be enhanced later
                            pdf_url=result.pdf_url if hasattr(result, 'pdf_url') else f"https://arxiv.org/pdf/{result.get_short_id()}.pdf"
                        )
                        papers.append(paper)
                        
                        # Rate limiting
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing arXiv result: {e}")
                        continue
            
            await fetch_arxiv_papers()
            
            self.logger.info(f"arXiv search completed: {len(papers)} papers")
            return papers
            
        except Exception as e:
            self.logger.error(f"arXiv search failed: {e}")
            return []
    
    async def _search_semantic_scholar(self, query, keywords: List[str]) -> List[Paper]:
        """Search Semantic Scholar for relevant papers."""
        try:
            # Build search query
            search_terms = []
            
            # Add question terms
            question_terms = re.findall(r'\b\w{4,}\b', query.question.lower())
            search_terms.extend(question_terms[:3])
            
            # Add domain-specific terms
            if query.domain == ResearchDomain.PHYSICS_EDUCATION:
                search_terms.extend(["physics education", "teaching physics", "learning physics"])
            
            # Add selected keywords
            search_terms.extend(keywords[:5])
            
            search_query = " ".join(search_terms[:10])
            
            self.logger.info(f"Semantic Scholar search query: {search_query[:100]}...")
            
            # Execute search
            url = f"{self.semantic_scholar_base}/paper/search"
            params = {
                "query": search_query,
                "limit": min(self.max_semantic_scholar_results, query.max_sources),
                "fields": "paperId,title,abstract,authors,venue,year,citationCount,url,openAccessPdf"
            }
            
            async def fetch_semantic_scholar():
                await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                return data.get("data", [])
            
            results = await fetch_semantic_scholar()
            
            papers = []
            for result in results:
                try:
                    # Extract author names
                    authors = []
                    if result.get("authors"):
                        authors = [author.get("name", "Unknown") for author in result["authors"]]
                    
                    # Determine URL and PDF URL
                    paper_url = result.get("url") or f"https://semanticscholar.org/paper/{result['paperId']}"
                    pdf_url = None
                    if result.get("openAccessPdf") and result["openAccessPdf"].get("url"):
                        pdf_url = result["openAccessPdf"]["url"]
                    
                    paper = Paper(
                        title=result.get("title", "Untitled"),
                        authors=authors,
                        abstract=result.get("abstract", ""),
                        url=paper_url,
                        published_date=self._parse_year_to_date(result.get("year")),
                        journal=result.get("venue", ""),
                        citations=result.get("citationCount", 0),
                        source="semantic_scholar",
                        keywords=[],
                        pdf_url=pdf_url
                    )
                    papers.append(paper)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing Semantic Scholar result: {e}")
                    continue
            
            self.logger.info(f"Semantic Scholar search completed: {len(papers)} papers")
            return papers
            
        except Exception as e:
            self.logger.error(f"Semantic Scholar search failed: {e}")
            return []
    
    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers based on title similarity and DOI."""
        if not papers:
            return papers
        
        unique_papers = []
        seen_titles = set()
        seen_dois = set()
        
        for paper in papers:
            # Check DOI first (most reliable)
            if paper.doi and paper.doi in seen_dois:
                continue
                
            # Check title similarity (normalized)
            normalized_title = re.sub(r'[^\w\s]', '', paper.title.lower()).strip()
            normalized_title = ' '.join(normalized_title.split())  # Normalize whitespace
            
            if normalized_title in seen_titles:
                continue
            
            # Add to unique collection
            unique_papers.append(paper)
            seen_titles.add(normalized_title)
            if paper.doi:
                seen_dois.add(paper.doi)
        
        return unique_papers
    
    async def _rank_papers(self, query, papers: List[Paper]) -> List[Paper]:
        """Use LLM to rank papers by relevance."""
        if not papers:
            return papers
        # Lightweight heuristic scoring used for pre-filtering and fallback
        def heuristic_score(p: Paper) -> float:
            citation_score = min((p.citations or 0) / 100.0, 0.5)
            year_score = 0.3 if p.published_date and p.published_date.year >= 2020 else 0.1
            return citation_score + year_score + 0.2

        try:
            # Pre-filter: pick top candidates by heuristic to reduce LLM workload
            TOP_K_FOR_LLM = min(6, len(papers))  # limit to at most 6 candidates
            papers_sorted_by_heuristic = sorted(papers, key=lambda p: heuristic_score(p), reverse=True)
            llm_candidates = papers_sorted_by_heuristic[:TOP_K_FOR_LLM]

            # Prepare a compact representation for the LLM (truncate abstract heavily)
            papers_data = []
            for i, paper in enumerate(llm_candidates):
                authors = ', '.join(paper.authors[:3]) + ('...' if len(paper.authors) > 3 else '')
                abstract_snip = (paper.abstract or '')[:200]
                if len(paper.abstract or '') > 200:
                    abstract_snip += '...'
                papers_data.append(f"""
Paper {i+1}:
Title: {paper.title}
Authors: {authors}
Abstract: {abstract_snip}
Journal: {paper.journal or 'N/A'}
Citations: {paper.citations}
Year: {paper.published_date.year if paper.published_date else 'Unknown'}
Source: {paper.source}
""")

            papers_text = "\n".join(papers_data)
            keywords_text = ", ".join(query.keywords) if query.keywords else "None specified"

            # Ask LLM to rank only the compact candidate set, with a per-call timeout to avoid hangs
            LLm_TIMEOUT_SECONDS = getattr(self, 'ranking_llm_timeout', 12)
            ranking_result = await self._execute_llm_chain(
                "ranking",
                question=query.question,
                domain=query.domain.value,
                keywords=keywords_text,
                papers_data=papers_text,
                llm_timeout=LLm_TIMEOUT_SECONDS,
            )

            # Parse ranking results for the candidate set
            scores = self._parse_ranking_results(ranking_result, len(llm_candidates))

            # Apply LLM scores to the candidate set
            for i, paper in enumerate(llm_candidates):
                if i < len(scores):
                    paper.relevance_score = scores[i].get("score", heuristic_score(paper))
                    if "physics_concepts" in scores[i]:
                        paper.keywords.extend(scores[i]["physics_concepts"])
                else:
                    paper.relevance_score = heuristic_score(paper)

            # For remaining papers not sent to LLM, use heuristic scores
            remaining = [p for p in papers if p not in llm_candidates]
            for p in remaining:
                p.relevance_score = heuristic_score(p)

            # Combine and sort all papers by final relevance_score
            ranked_papers = sorted(papers, key=lambda p: p.relevance_score, reverse=True)
            self.logger.info(f"Ranked {len(ranked_papers)} papers (LLM used on {len(llm_candidates)}), top score: {ranked_papers[0].relevance_score:.2f}")
            return ranked_papers

        except asyncio.TimeoutError:
            self.logger.warning("LLM ranking timed out; falling back to heuristic scoring")
            for paper in papers:
                paper.relevance_score = heuristic_score(paper)
            return sorted(papers, key=lambda p: p.relevance_score, reverse=True)

        except Exception as e:
            self.logger.warning(f"Paper ranking failed: {e}, using default scoring")
            for paper in papers:
                paper.relevance_score = heuristic_score(paper)
            return sorted(papers, key=lambda p: p.relevance_score, reverse=True)
    
    def _parse_ranking_results(self, ranking_text: str, num_papers: int) -> List[Dict[str, Any]]:
        """Parse LLM ranking results."""
        scores = []
        current_paper = {}
        
        for line in ranking_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Paper ID:') or line.startswith('Paper '):
                if current_paper:
                    scores.append(current_paper)
                current_paper = {}
                
            elif line.startswith('Score:'):
                try:
                    score_text = line.split(':', 1)[1].strip()
                    score = float(re.search(r'[\d.]+', score_text).group())
                    current_paper["score"] = min(max(score, 0.0), 1.0)  # Clamp to 0-1
                except (ValueError, AttributeError):
                    current_paper["score"] = 0.5
                    
            elif line.startswith('Key Physics Concepts:'):
                concepts = line.split(':', 1)[1].strip()
                current_paper["physics_concepts"] = [c.strip() for c in concepts.split(',')]
        
        # Add last paper if exists
        if current_paper:
            scores.append(current_paper)
        
        # Ensure we have scores for all papers
        while len(scores) < num_papers:
            scores.append({"score": 0.5, "physics_concepts": []})
        
        return scores[:num_papers]
    
    def _apply_filters(self, papers: List[Paper], query) -> List[Paper]:
        """Apply final filters and limits to paper selection."""
        filtered_papers = []
        
        for paper in papers:
            # Skip papers with very low relevance scores
            if paper.relevance_score < 0.2:
                continue
                
            # Apply year filter if specified
            if query.preferred_years:
                start_year, end_year = query.preferred_years
                if paper.published_date:
                    paper_year = paper.published_date.year
                    if paper_year < start_year or paper_year > end_year:
                        continue
            
            # Filter by exclude keywords
            if query.exclude_keywords:
                title_abstract = (paper.title + " " + paper.abstract).lower()
                if any(keyword.lower() in title_abstract for keyword in query.exclude_keywords):
                    continue
            
            filtered_papers.append(paper)
            
            # Apply max sources limit
            if len(filtered_papers) >= query.max_sources:
                break
        
        # Ensure minimum sources if possible
        if len(filtered_papers) < query.min_sources and len(papers) >= query.min_sources:
            # Add more papers even with lower scores
            remaining_papers = [p for p in papers if p not in filtered_papers]
            needed = query.min_sources - len(filtered_papers)
            filtered_papers.extend(remaining_papers[:needed])
        
        return filtered_papers
    
    def _parse_year_to_date(self, year: Optional[int]) -> Optional[datetime]:
        """Convert year to datetime object."""
        if year and isinstance(year, (int, str)):
            try:
                return datetime(int(year), 1, 1)
            except (ValueError, TypeError):
                return None
        return None
    
    async def _search_aip_publications(self, query, keywords: List[str]) -> List[Paper]:
        """
        Search AIP Publishing journals including American Journal of Physics, 
        The Physics Teacher, Physics Today, and other premium content.
        Requires valid AIP credentials for access to pubs.aip.org.
        """
        papers = []
        # Best-effort: try authenticated session to pubs.aip.org, otherwise fall back to CrossRef
        import httpx
        from bs4 import BeautifulSoup
        from core.credentials import PremiumCredentials

        creds = PremiumCredentials()
        client = httpx.AsyncClient(timeout=20.0)

            # Try Playwright-based login helper to get cookies if available
        try:
            from core.premium_auth import synchronous_get_cookies_loop, httpx_cookie_dict_to_header
            aip_cookies = None
            if creds.has_aip_access():
                ac = creds.get_aip_credentials()
                try:
                    aip_cookies = synchronous_get_cookies_loop('aip', ac['username'], ac['password'])
                    if aip_cookies:
                        client.headers.update({'Cookie': httpx_cookie_dict_to_header(aip_cookies)})
                        self.logger.info('Applied Playwright-derived cookies for AIP session')
                except Exception:
                    self.logger.debug('Playwright AIP cookie helper failed; continuing with httpx flows')
        except Exception:
            # premium_auth or playwright not available; continue
            aip_cookies = None

        try:
            self.logger.info("Searching AIP publications (authenticated when possible)...")

            # Build a conservative search string
            search_query = f"{query.question} physics education"

            # If we have AIP credentials, try to login and hit search pages
            if creds.has_aip_access():
                self.logger.info("Attempting authenticated AIP session")
                aip_creds = creds.get_aip_credentials()
                try:
                    # Pseudo-login flow: fetch login page to get any CSRF tokens, then post
                    login_page = await client.get("https://pubs.aip.org/login")
                    soup = BeautifulSoup(login_page.text, "html.parser")
                    # Try to find csrf token or hidden inputs
                    token_input = soup.find('input', {'name': 'authenticity_token'})
                    token = token_input.get('value') if token_input else None

                    login_payload = {
                        'username': aip_creds['username'],
                        'password': aip_creds['password']
                    }
                    if token:
                        login_payload['authenticity_token'] = token

                    post = await client.post("https://pubs.aip.org/login", data=login_payload)
                    if post.status_code not in (200, 302):
                        self.logger.warning(f"AIP login attempt returned {post.status_code}")
                    else:
                        self.logger.info("AIP login attempt finished; attempting search as authenticated user")

                    # Search URL pattern — try simple query param
                    resp = await client.get("https://pubs.aip.org/search", params={"q": search_query})
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        # Attempt to parse search result items conservatively
                        results = soup.select('.search-result, .article-list-item')
                        for item in results[:10]:
                            title_tag = item.find('h2') or item.find('a')
                            title = title_tag.get_text(strip=True) if title_tag else None
                            link = title_tag.get('href') if title_tag and title_tag.has_attr('href') else None
                            abstract_tag = item.select_one('.abstract')
                            abstract = abstract_tag.get_text(strip=True) if abstract_tag else ''
                            meta = item.get_text(separator=' | ')
                            # Basic filter by keywords
                            if title and any(k.lower() in (title + abstract + meta).lower() for k in keywords + [query.question]):
                                paper = Paper(
                                    title=title,
                                    authors=[],
                                    abstract=abstract,
                                    published_date=None,
                                    doi=None,
                                    url=(link if link and link.startswith('http') else ("https://pubs.aip.org" + link if link else None)),
                                    pdf_url=None,
                                    journal=None,
                                    source="AIP",
                                    keywords=keywords
                                )
                                papers.append(paper)

                except Exception as e:
                    self.logger.warning(f"AIP authenticated search failed: {e}; falling back to CrossRef/plain search")

            # Fallback: Use CrossRef API to find DOIs for the query and then fetch metadata
            if not papers:
                try:
                    self.logger.info("Falling back to CrossRef metadata search for AIP-related content")
                    cr = await client.get("https://api.crossref.org/works", params={"query": search_query, "rows": 10})
                    if cr.status_code == 200:
                        j = cr.json()
                        items = j.get('message', {}).get('items', [])
                        for item in items:
                            title = item.get('title', [None])[0]
                            abstract = item.get('abstract') or ''
                            doi = item.get('DOI')
                            pub_date = None
                            if item.get('issued') and item['issued'].get('date-parts'):
                                yp = item['issued']['date-parts'][0]
                                if yp:
                                    pub_date = self._parse_year_to_date(yp[0])

                            if title and any(k.lower() in (title + (abstract or '')).lower() for k in keywords + [query.question]):
                                paper = Paper(
                                    title=title,
                                    authors=[a.get('family', '') for a in item.get('author', [])] or [],
                                    abstract=(abstract or '').replace('<jats:p>', '').replace('</jats:p>', ''),
                                    published_date=pub_date,
                                    doi=doi,
                                    url=item.get('URL'),
                                    pdf_url=None,
                                    journal=item.get('container-title', [None])[0],
                                    source="CrossRef",
                                    keywords=keywords
                                )
                                papers.append(paper)

                except Exception as e:
                    self.logger.warning(f"CrossRef fallback failed: {e}")

        except Exception as e:
            self.logger.error(f"AIP search failed unexpectedly: {e}")
        finally:
            await client.aclose()

        self.logger.info(f"AIP search completed: {len(papers)} papers/resources discovered")
        return papers
    
    async def _search_compadre(self, query, keywords: List[str]) -> List[Paper]:
        """
        Search ComPADRE (Community for Physics and Astronomy Digital Resources Exchange).
        Access physics education resources, simulations, and teaching materials.
        """
        papers = []
        import httpx
        from bs4 import BeautifulSoup
        from core.credentials import PremiumCredentials

        papers = []
        client = httpx.AsyncClient(timeout=20.0)
        creds = PremiumCredentials()

        try:
            self.logger.info("Searching ComPADRE (attempting authenticated access when configured)")
            search_query = " ".join((keywords or [])[:5]) + f" {query.question}"

            # Simple public search on ComPADRE (no official public API documented for search)
            try:
                resp = await client.get("https://www.compadre.org/search/", params={"q": search_query})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    items = soup.select('.result, .search-result')
                    for it in items[:10]:
                        title_tag = it.find('a') or it.find('h3')
                        title = title_tag.get_text(strip=True) if title_tag else None
                        link = title_tag.get('href') if title_tag and title_tag.has_attr('href') else None
                        desc = it.get_text(strip=True)
                        if title and any(k.lower() in (title + desc).lower() for k in keywords + [query.question]):
                            paper = Paper(
                                title=title,
                                authors=[],
                                abstract=desc,
                                published_date=None,
                                url=(link if link and link.startswith('http') else ("https://www.compadre.org" + link if link else None)),
                                journal='ComPADRE',
                                source='ComPADRE',
                                keywords=keywords
                            )
                            papers.append(paper)

            except Exception as e:
                self.logger.warning(f"ComPADRE basic search failed: {e}")

            # If ComPADRE credentials are available, attempt a Playwright login helper first
            if creds.has_compadre_access():
                try:
                    from core.premium_auth import synchronous_get_cookies_loop, httpx_cookie_dict_to_header
                    comp_creds = creds.get_compadre_credentials()
                    comp_cookies = synchronous_get_cookies_loop('compadre', comp_creds['username'], comp_creds['password'])
                    if comp_cookies:
                        client.headers.update({'Cookie': httpx_cookie_dict_to_header(comp_cookies)})
                        self.logger.info('Applied Playwright-derived cookies for ComPADRE session')
                    else:
                        # Try simple POST login fallback
                        login_page = await client.get('https://www.compadre.org/login')
                        soup = BeautifulSoup(login_page.text, 'html.parser')
                        token_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
                        token = token_input.get('value') if token_input else None
                        payload = {'username': comp_creds['username'], 'password': comp_creds['password']}
                        if token:
                            payload['csrfmiddlewaretoken'] = token
                        post = await client.post('https://www.compadre.org/accounts/login/', data=payload)
                        self.logger.info(f"ComPADRE login attempt status: {post.status_code}")

                except Exception as e:
                    self.logger.warning(f"ComPADRE authenticated attempt failed: {e}")

        except Exception as e:
            self.logger.error(f"ComPADRE search failed: {e}")
        finally:
            await client.aclose()

        self.logger.info(f"ComPADRE search completed: {len(papers)} resources")
        return papers
    
    async def _search_per_central(self, query, keywords: List[str]) -> List[Paper]:
        """
        Search PER Central for physics education research papers and resources.
        Specialized database for physics education research (PER) content.
        """
        papers = []
        import httpx
        from bs4 import BeautifulSoup
        from core.credentials import PremiumCredentials

        papers = []
        client = httpx.AsyncClient(timeout=20.0)
        creds = PremiumCredentials()

        try:
            self.logger.info("Searching PER Central (authenticated when available)")
            search_query = f"{query.question} physics education"

            # PER-Central provides a web interface; attempt a search page scrape
            try:
                resp = await client.get('https://per-central.org/search', params={'q': search_query})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    items = soup.select('.search-result, .result-item')
                    for it in items[:10]:
                        title_tag = it.find('a') or it.find('h3')
                        title = title_tag.get_text(strip=True) if title_tag else None
                        link = title_tag.get('href') if title_tag and title_tag.has_attr('href') else None
                        desc = it.get_text(strip=True)
                        if title and any(k.lower() in (title + desc).lower() for k in keywords + [query.question]):
                            paper = Paper(
                                title=title,
                                authors=[],
                                abstract=desc,
                                published_date=None,
                                url=(link if link and link.startswith('http') else ("https://per-central.org" + link if link else None)),
                                journal='PER-Central',
                                source='PER-Central',
                                keywords=keywords
                            )
                            papers.append(paper)

            except Exception as e:
                self.logger.warning(f"PER Central basic search failed: {e}")

            # If PER-Central credentials are available, a login attempt can be made (best-effort)
            if creds.has_per_central_access():
                try:
                    per_creds = creds.get_per_central_credentials()
                    login_page = await client.get('https://per-central.org/login')
                    soup = BeautifulSoup(login_page.text, 'html.parser')
                    token_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
                    token = token_input.get('value') if token_input else None
                    payload = {'username': per_creds['username'], 'password': per_creds['password']}
                    if token:
                        payload['csrfmiddlewaretoken'] = token
                    post = await client.post('https://per-central.org/accounts/login/', data=payload)
                    self.logger.info(f"PER-Central login attempt status: {post.status_code}")
                except Exception as e:
                    self.logger.warning(f"PER Central authenticated attempt failed: {e}")

        except Exception as e:
            self.logger.error(f"PER Central search failed: {e}")
        finally:
            await client.aclose()

        self.logger.info(f"PER Central search completed: {len(papers)} papers/resources")
        return papers