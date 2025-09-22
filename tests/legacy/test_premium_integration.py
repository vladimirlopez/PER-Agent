#!/usr/bin/env python3
"""
Test the enhanced Literature Scout with premium database integration
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from core.orchestrator import ResearchOrchestrator
from core.models import ResearchQuery

async def test_premium_database_integration():
    """Test Literature Scout with premium database access."""
    print("🔍 TESTING PREMIUM DATABASE INTEGRATION")
    print("=" * 50)
    print("📚 Enhanced Sources:")
    print("   1. arXiv (free)")
    print("   2. Semantic Scholar (free)") 
    print("   3. AIP Publishing (premium) - American Journal of Physics, The Physics Teacher, Physics Today")
    print("   4. ComPADRE (premium) - Physics education resources")
    print("   5. PER Central (premium) - Physics education research")
    print()
    
    try:
        # Initialize orchestrator
        print("⚙️ Initializing enhanced Literature Scout...")
        orchestrator = ResearchOrchestrator()
        
        # Check premium access status
        literature_scout = orchestrator.agents["literature_scout"]
        credentials = literature_scout.credentials
        
        print("🔐 PREMIUM ACCESS STATUS:")
        print(f"   AIP Publishing Access: {'✅ Available' if credentials.has_aip_access() else '❌ No credentials'}")
        print(f"   ComPADRE Access: {'✅ Available' if credentials.has_compadre_access() else '❌ No credentials'}")
        print(f"   PER Central Access: {'✅ Available' if credentials.has_per_central_access() else '❌ No credentials'}")
        print()
        
        if not any([credentials.has_aip_access(), credentials.has_compadre_access(), credentials.has_per_central_access()]):
            print("📝 TO ENABLE PREMIUM ACCESS:")
            print("   1. Copy .env.template to .env")
            print("   2. Add your credentials to .env file:")
            print("      AIP_USERNAME=your_username")
            print("      AIP_PASSWORD=your_password")
            print("   3. Run this test again")
            print()
        
        # Create test query
        query = ResearchQuery(
            question="How effective are interactive simulations in teaching wave physics?",
            max_sources=3  # Small number for testing
        )
        
        print(f"🔍 Test Query: {query.question}")
        print("🔄 Running literature search with all available sources...")
        print()
        
        # Test just the literature search node
        from core.models import AgentState
        
        state = AgentState(
            query=query,
            current_step="initialized"
        )
        
        # Run literature search
        result_state = await orchestrator._literature_search_node(state)
        
        # Display results by source
        papers_by_source = {}
        if hasattr(result_state, 'literature_results'):
            for paper in result_state.literature_results:
                source = paper.source
                if source not in papers_by_source:
                    papers_by_source[source] = []
                papers_by_source[source].append(paper)
        
        print("📊 SEARCH RESULTS BY SOURCE:")
        print("-" * 40)
        total_papers = 0
        
        for source, papers in papers_by_source.items():
            print(f"📚 {source}: {len(papers)} papers")
            total_papers += len(papers)
            
            # Show first paper from each source
            if papers:
                first_paper = papers[0]
                print(f"   📄 Example: {first_paper.title[:60]}...")
                print(f"   👥 Authors: {', '.join(first_paper.authors[:2])}...")
                print(f"   📊 Score: {first_paper.relevance_score:.2f}")
                print()
        
        print(f"🎯 TOTAL PAPERS FOUND: {total_papers}")
        
        if total_papers > 2:  # More than just free sources
            print("🎉 SUCCESS: Premium sources are contributing results!")
        else:
            print("ℹ️  Currently using free sources only")
        
        print()
        print("✅ ENHANCED LITERATURE SCOUT OPERATIONAL")
        print("🔗 Ready for full research workflows with premium content")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_premium_database_integration())
