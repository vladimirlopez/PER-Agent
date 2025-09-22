#!/usr/bin/env python3
"""
🎉 COMPLETE 6-AGENT PER AGENT SYSTEM TEST - copy in legacy tests
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from core.orchestrator import ResearchOrchestrator
from core.models import ResearchQuery

async def test_complete_6_agent_system():
    print("🎉 TESTING COMPLETE 6-AGENT PER AGENT SYSTEM")
    print("=" * 60)
    try:
        orchestrator = ResearchOrchestrator()
        query = ResearchQuery(
            question="What are the effectiveness metrics for interactive physics simulations in undergraduate education?",
            max_sources=2
        )
        result = await orchestrator.research(query)
        print("Complete test executed (legacy copy)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_complete_6_agent_system())
