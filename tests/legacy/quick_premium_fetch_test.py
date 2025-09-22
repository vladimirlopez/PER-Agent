"""
Quick test script to run the premium fetch methods from LiteratureScoutAgent.
This script runs minimal authenticated attempts without revealing credentials in logs.

Run:
    .venv\Scripts\Activate.ps1; python quick_premium_fetch_test.py

Note: ensure your `.env` has AIP/COMPADRE/PER_CENTRAL creds if you want authenticated attempts.
"""

import asyncio
import pathlib
import sys

# Ensure src is on path
sys.path.insert(0, str(pathlib.Path('.').resolve() / 'src'))

from agents.literature_scout import LiteratureScoutAgent
from core.config import Config
from core.models import AgentState, ResearchQuery, ResearchDomain

async def main():
    cfg = Config.from_env()
    agent_cfg = cfg.get_agent_config('literature_scout')
    agent = LiteratureScoutAgent(agent_cfg)

    query = ResearchQuery(
        question="How does interactive simulation affect conceptual understanding in introductory physics?",
        keywords=["interactive simulation", "conceptual understanding", "introductory physics"],
        domain=ResearchDomain.PHYSICS_EDUCATION,
        max_sources=10,
        min_sources=3
    )

    state = AgentState(query=query, current_step='search')

    result_state = await agent.process(state)

    print("Found papers:")
    for p in result_state.papers:
        print('-', p.title, '|', p.source, '|', p.url)

if __name__ == '__main__':
    asyncio.run(main())
