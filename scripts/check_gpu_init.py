#!/usr/bin/env python3
"""Simple check to initialize agents and report chosen models and GPU usage."""

from core.config import Config
from core.orchestrator import ResearchOrchestrator
import asyncio
import time

async def run_check():
    cfg = Config.from_env()
    print(f"OLLAMA_HOST: {cfg.ollama_host}")
    print(f"Prefer GPU: {cfg.prefer_gpu}")
    orch = ResearchOrchestrator(config=cfg)

    for name, agent in orch.agents.items():
        stats = agent.get_performance_stats()
        print(f"Agent: {name}, Model used: {stats['model_used']}")

if __name__ == '__main__':
    asyncio.run(run_check())
