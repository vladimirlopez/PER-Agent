"""
Debug script to identify the document processing issue.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.models import ResearchQuery, ResearchDomain, AgentState
from core.orchestrator import ResearchOrchestrator


async def debug_pipeline():
    """Debug the research pipeline step by step."""
    print("🔍 DEBUGGING PER AGENT PIPELINE")
    print("=" * 50)
    
    # Create test query
    query = ResearchQuery(
        question="How effective are simulations in teaching wave physics?",
        domain=ResearchDomain.PHYSICS_EDUCATION,
        max_sources=5
    )
    
    print(f"Query: {query.question}")
    print(f"Max Sources: {query.max_sources}")
    print()
    
    # Initialize orchestrator
    orchestrator = ResearchOrchestrator()
    state = AgentState(query=query, current_step="initialized")
    
    # Step 1: Test Literature Scout
    print("📚 STEP 1: Literature Search")
    print("-" * 30)
    
    try:
        lit_result = await orchestrator.agents["literature_scout"].process(state)
        papers = lit_result.papers if hasattr(lit_result, 'papers') else []
        
        print(f"✅ Found {len(papers)} papers")
        
        for i, paper in enumerate(papers[:3], 1):
            print(f"{i}. {paper.title[:60]}...")
            print(f"   Authors: {', '.join(paper.authors[:2])}")
            print(f"   Source: {paper.source}")
            print(f"   URL: {paper.url}")
            print(f"   PDF URL: {getattr(paper, 'pdf_url', 'None')}")
            print()
            
    except Exception as e:
        print(f"❌ Literature search failed: {e}")
        return
    
    if not papers:
        print("❌ No papers found - cannot test document analysis")
        return
    
    # Step 2: Test Document Analysis
    print("📄 STEP 2: Document Analysis")
    print("-" * 30)
    
    # Update state with papers
    state.papers = papers
    
    try:
        doc_analyzer = orchestrator.agents["document_analyzer"]
        
        # Test PDF download for first paper
        test_paper = papers[0]
        print(f"Testing PDF download for: {test_paper.title[:50]}...")
        
        pdf_text = await doc_analyzer._download_and_parse_pdf(test_paper)
        
        if pdf_text:
            print(f"✅ Successfully extracted {len(pdf_text)} characters")
            print(f"   First 200 chars: {pdf_text[:200]}...")
        else:
            print("❌ Failed to extract PDF text")
            print("   Possible causes:")
            print("   - No PDF URL available")
            print("   - PDF download failed")
            print("   - PDF parsing failed")
            
        # Test full document analysis
        print("\nTesting full document analysis...")
        doc_result = await doc_analyzer.process(state)
        
        analyzed_docs = doc_result.analyzed_documents if hasattr(doc_result, 'analyzed_documents') else []
        print(f"✅ Analyzed {len(analyzed_docs)} documents")
        
        if analyzed_docs:
            doc = analyzed_docs[0]
            print(f"   Sample findings: {doc.key_findings[:2]}")
        
    except Exception as e:
        print(f"❌ Document analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎯 PIPELINE DEBUG COMPLETE")
    print(f"   Papers Found: {len(papers)}")
    print(f"   Documents Analyzed: {len(analyzed_docs) if 'analyzed_docs' in locals() else 0}")


if __name__ == "__main__":
    asyncio.run(debug_pipeline())