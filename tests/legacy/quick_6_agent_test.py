#!/usr/bin/env python3
"""
Quick 6-agent initialization test (legacy copy)
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_agent_initialization():
    from core.orchestrator import ResearchOrchestrator
    orchestrator = ResearchOrchestrator()
    print('Legacy quick_6_agent_test initialized', len(orchestrator.agents))

if __name__ == '__main__':
    test_agent_initialization()
