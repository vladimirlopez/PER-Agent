#!/usr/bin/env python3
"""
Quick premium test (legacy copy)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from agents.literature_scout import LiteratureScoutAgent
from core.models import ResearchQuery, AgentState

async def quick_premium_test():
    scout = LiteratureScoutAgent()
    papers = await scout._search_aip_publications(ResearchQuery(question='test'), ['simulation'])
    print('Legacy quick premium test found', len(papers))

if __name__ == '__main__':
    asyncio.run(quick_premium_test())
