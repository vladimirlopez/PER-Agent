"""
Complete pipeline test (placeholder moved from repository root).

This placeholder preserves the file in `tests/legacy/`. For full testing, use the
original test harness or run the orchestrator directly.
"""

def main():
    print("complete_pipeline_test placeholder")


if __name__ == '__main__':
    main()
"""
Legacy copy - complete pipeline test
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.orchestrator import ResearchOrchestrator

async def complete_pipeline_test():
    orchestrator = ResearchOrchestrator()
    print('Legacy complete pipeline test - orchestrator initialized')

if __name__ == '__main__':
    asyncio.run(complete_pipeline_test())
