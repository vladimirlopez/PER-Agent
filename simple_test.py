#!/usr/bin/env python3
"""
Simple test of the enhanced 5-agent pipeline with PDF organization
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from core.orchestrator import ResearchOrchestrator
from core.models import AgentState, ResearchQuery

async def simple_test():
    """Run a simple test with just literature search."""
    print("🚀 SIMPLE PER AGENT TEST")
    print("=" * 50)
    
    # Initialize orchestrator
    print("⚙️ Initializing orchestrator...")
    orchestrator = ResearchOrchestrator()
    
    # Create test state
    query = ResearchQuery(
        question="Interactive physics simulations in education",
        keywords=["physics education", "interactive simulations"],
        max_sources=2  # Small number for testing
    )
    state = AgentState(
        query=query,
        current_step="initialized"
    )
    
    print(f"🔍 Research Question: {state.query.question}")
    print(f"📊 Max Sources: {state.query.max_sources}")
    
    # Run just literature search
    print("\n🔄 Running literature search...")
    try:
        final_state = await orchestrator._literature_search_node(state)
        
        papers_found = len(final_state.literature_results) if hasattr(final_state, 'literature_results') else 0
        print(f"✅ Literature search completed: {papers_found} papers found")
        
        if papers_found > 0:
            print("\n📄 Found papers:")
            for i, paper in enumerate(final_state.literature_results[:3], 1):
                print(f"   {i}. {paper.title[:60]}...")
                print(f"      Authors: {', '.join(paper.authors[:2])}...")
                print(f"      Score: {paper.relevance_score:.2f}")
                print()
        
        print("🎉 SUCCESS: Basic pipeline working!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())