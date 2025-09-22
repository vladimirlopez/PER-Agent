#!/usr/bin/env python3
"""
Simple test of the enhanced 5-agent pipeline with PDF organization (legacy copy)
"""

import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.orchestrator import ResearchOrchestrator
from core.models import AgentState, ResearchQuery

async def simple_test():
    orchestrator = ResearchOrchestrator()
    query = ResearchQuery(question="Interactive physics simulations in education", max_sources=2)
    state = AgentState(query=query, current_step='initialized')
    final_state = await orchestrator._literature_search_node(state)
    print(f"Found {len(final_state.literature_results)} papers (legacy copy)")

if __name__ == '__main__':
    asyncio.run(simple_test())
