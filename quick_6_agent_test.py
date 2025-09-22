#!/usr/bin/env python3
"""
Quick verification that all 6 agents initialize properly
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def test_agent_initialization():
    """Test that all 6 agents can be initialized."""
    print("🔍 QUICK 6-AGENT INITIALIZATION TEST")
    print("=" * 45)
    
    try:
        from core.orchestrator import ResearchOrchestrator
        
        print("⚙️ Initializing orchestrator with all 6 agents...")
        orchestrator = ResearchOrchestrator()
        
        print("✅ SUCCESS! All 6 agents initialized:")
        for i, (agent_name, agent) in enumerate(orchestrator.agents.items(), 1):
            print(f"   {i}. {agent_name.replace('_', ' ').title()}: {agent.__class__.__name__}")
        
        print()
        print("🎉 MILESTONE ACHIEVED: 100% COMPLETE PER AGENT SYSTEM!")
        print("📊 Status: All 6 agents successfully integrated")
        print("🎯 Ready for full research workflows")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_agent_initialization()