"""
Test script to demonstrate current PER Agent capabilities (4/6 agents complete).
Shows what the system can produce at 67% completion.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.models import ResearchQuery, ResearchDomain, AgentState
from core.orchestrator import ResearchOrchestrator


async def demonstrate_capabilities():
    """Demonstrate what our 4-agent system can produce."""
    print("🧪 PER AGENT SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("Current Status: 67% Complete (4/6 agents)")
    print("Agents: Literature Scout → Document Analyzer → Physics Specialist → Content Synthesizer")
    print()
    
    # Create test query
    query = ResearchQuery(
        question="How effective are interactive simulations in teaching wave physics to high school students?",
        domain=ResearchDomain.PHYSICS_EDUCATION,
        max_sources=8,  # Smaller number for demo
        keywords=["wave physics", "simulations", "interactive", "high school"]
    )
    
    print(f"📋 TEST QUERY:")
    print(f"   Question: {query.question}")
    print(f"   Domain: {query.domain.value}")
    print(f"   Max Sources: {query.max_sources}")
    print(f"   Keywords: {', '.join(query.keywords)}")
    print()
    
    # Initialize orchestrator
    try:
        orchestrator = ResearchOrchestrator()
        print("✅ System initialized successfully")
        
        # Show system capabilities
        system_info = orchestrator.get_system_info()
        print(f"\n🖥️  SYSTEM STATUS:")
        print(f"   Models configured: {system_info['models_configured']}")
        print(f"   Agents ready: {system_info['agents_initialized']}")
        print(f"   VRAM validation: {'✅' if system_info['vram_validation'] else '❌'}")
        print()
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return
    
    # Run the 4-agent workflow
    print("🚀 RUNNING 4-AGENT WORKFLOW...")
    print("=" * 60)
    
    try:
        # Create initial state
        state = AgentState(query=query, current_step="initialized")
        
        # Step 1: Literature Search
        print("📚 STEP 1: Literature Search")
        print("-" * 30)
        
        lit_agent = orchestrator.agents["literature_scout"]
        state = await lit_agent.process(state)
        
        papers = state.papers if hasattr(state, 'papers') else []
        print(f"✅ Found {len(papers)} relevant papers")
        
        if papers:
            print("\n📄 Top Papers Found:")
            for i, paper in enumerate(papers[:3], 1):
                print(f"   {i}. {paper.title[:60]}...")
                print(f"      Relevance: {paper.relevance_score:.2f}")
                print(f"      Source: {paper.source}")
                print(f"      Citations: {paper.citations}")
                print()
        
        if not papers:
            print("❌ No papers found - stopping demo")
            return
        
        # Step 2: Document Analysis
        print("📄 STEP 2: Document Analysis")
        print("-" * 30)
        
        doc_agent = orchestrator.agents["document_analyzer"]
        state = await doc_agent.process(state)
        
        analyzed_docs = state.analyzed_documents if hasattr(state, 'analyzed_documents') else []
        print(f"✅ Analyzed {len(analyzed_docs)} documents")
        
        if analyzed_docs:
            print("\n📋 Sample Analysis Results:")
            doc = analyzed_docs[0]
            print(f"   Title: {doc.paper.title[:60]}...")
            print(f"   Key Findings ({len(doc.key_findings)}):")
            for finding in doc.key_findings[:2]:
                print(f"     • {finding[:80]}...")
            print(f"   Methodology: {str(doc.methodology)[:100]}...")
            print(f"   Relevance Score: {doc.relevance_score}/10")
            print()
        
        # Step 3: Physics Validation
        print("🔬 STEP 3: Physics Validation")
        print("-" * 30)
        
        physics_agent = orchestrator.agents["physics_specialist"]
        state = await physics_agent.process(state)
        
        validations = state.validation_results if hasattr(state, 'validation_results') else []
        print(f"✅ Validated {len(validations)} documents")
        
        if validations:
            print("\n⚖️  Sample Validation Results:")
            validation = validations[0]
            overall_score = validation.overall_validation.get("total_score", 0)
            physics_score = validation.concept_accuracy.get("score", 0)
            math_score = validation.mathematical_validation.get("score", 0)
            
            print(f"   Document: {validation.document.paper.title[:50]}...")
            print(f"   Overall Score: {overall_score}/10")
            print(f"   Physics Accuracy: {physics_score}/10")
            print(f"   Math Accuracy: {math_score}/10")
            print(f"   Recommendations: {len(validation.recommendations)}")
            if validation.recommendations:
                print(f"     • {validation.recommendations[0][:80]}...")
            print()
        
        # Step 4: Content Synthesis
        print("🧠 STEP 4: Content Synthesis")
        print("-" * 30)
        
        synthesis_agent = orchestrator.agents["content_synthesizer"]
        state = await synthesis_agent.process(state)
        
        insights = state.synthesis_insights if hasattr(state, 'synthesis_insights') else []
        synthesis_content = state.synthesized_content if hasattr(state, 'synthesized_content') else {}
        
        print(f"✅ Generated {len(insights)} synthesis insights")
        
        if synthesis_content and "synthesis_quality_score" in synthesis_content:
            quality_score = synthesis_content["synthesis_quality_score"]
            print(f"✅ Synthesis Quality Score: {quality_score:.2f}/1.0")
        
        if insights:
            print("\n💡 Sample Insights Generated:")
            for i, insight in enumerate(insights[:3], 1):
                print(f"   {i}. Type: {insight.insight_type.title()}")
                print(f"      Description: {insight.description[:80]}...")
                print(f"      Confidence: {insight.confidence:.2f}")
                print(f"      Evidence: {len(insight.supporting_evidence)} items")
                print()
        
        # Show comprehensive output summary
        print("📊 COMPREHENSIVE OUTPUT SUMMARY")
        print("=" * 60)
        
        print(f"🔍 Literature Search Results:")
        print(f"   • Papers found: {len(papers)}")
        print(f"   • Average relevance: {sum(p.relevance_score for p in papers) / len(papers):.2f}" if papers else "   • Average relevance: N/A")
        print(f"   • Sources: {set(p.source for p in papers)}")
        
        print(f"\n📄 Document Analysis Results:")
        print(f"   • Documents analyzed: {len(analyzed_docs)}")
        if analyzed_docs:
            total_findings = sum(len(doc.key_findings) for doc in analyzed_docs)
            print(f"   • Total key findings extracted: {total_findings}")
            print(f"   • Average relevance: {sum(doc.relevance_score for doc in analyzed_docs) / len(analyzed_docs):.1f}/10")
        
        print(f"\n🔬 Physics Validation Results:")
        print(f"   • Documents validated: {len(validations)}")
        if validations:
            avg_overall = sum(v.overall_validation.get("total_score", 0) for v in validations) / len(validations)
            avg_physics = sum(v.concept_accuracy.get("score", 0) for v in validations) / len(validations)
            avg_math = sum(v.mathematical_validation.get("score", 0) for v in validations) / len(validations)
            print(f"   • Average overall score: {avg_overall:.1f}/10")
            print(f"   • Average physics accuracy: {avg_physics:.1f}/10")
            print(f"   • Average math accuracy: {avg_math:.1f}/10")
        
        print(f"\n🧠 Content Synthesis Results:")
        print(f"   • Insights generated: {len(insights)}")
        if insights:
            avg_confidence = sum(i.confidence for i in insights) / len(insights)
            insight_types = set(i.insight_type for i in insights)
            print(f"   • Average confidence: {avg_confidence:.2f}")
            print(f"   • Insight types: {', '.join(insight_types)}")
        
        if synthesis_content:
            print(f"   • Synthesis quality: {synthesis_content.get('synthesis_quality_score', 0):.2f}/1.0")
        
        # What we CAN'T produce yet (missing agents)
        print(f"\n❌ MISSING CAPABILITIES (33% remaining):")
        print(f"   • Professional Report Generation (LaTeX/Markdown/PDF)")
        print(f"   • Quality Control & Final Validation")
        print(f"   • Formatted Citations & Bibliography")
        print(f"   • Executive Summary & Conclusions")
        print(f"   • Recommendations for Practice")
        
        print(f"\n🎯 NEXT MILESTONES:")
        print(f"   • Report Generator Agent → 83% complete")
        print(f"   • Quality Controller Agent → 100% complete")
        
        print(f"\n✅ DEMO COMPLETE - System working at 67% capacity!")
        
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting PER Agent demonstration...")
    print("This will show what the system can produce at 67% completion")
    print()
    
    try:
        asyncio.run(demonstrate_capabilities())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")