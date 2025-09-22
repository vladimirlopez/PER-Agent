"""
Simple PDF analysis test (legacy copy)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.models import ResearchQuery, ResearchDomain, AgentState, Paper
from agents.document_analyzer import DocumentAnalyzerAgent

async def simple_pdf_test():
    print('Running legacy simple_pdf_test')

if __name__ == '__main__':
    asyncio.run(simple_pdf_test())
