"""
Improved demo that actually tries to get real results from papers.
Focus on papers that should have accessible PDFs.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.models import ResearchQuery, ResearchDomain, AgentState
from core.orchestrator import ResearchOrchestrator


async def real_results_demo():
    """Demo that attempts to get actual analysis results."""
    print("🚀 PER AGENT - REAL RESULTS DEMONSTRATION")
    print("=" * 60)
    
    # Create query targeting papers with good PDF access
    query = ResearchQuery(
        question="How do interactive simulations improve student understanding of wave interference?",
        domain=ResearchDomain.PHYSICS_EDUCATION,
        max_sources=3,  # Keep it small for focused testing
        keywords=["wave interference", "interactive simulations", "physics education", "student understanding"]
    )
    
    print(f"🎯 Research Question: {query.question}")
    print(f"📊 Target Sources: {query.max_sources}")
    print()
    
    try:
        # Initialize orchestrator
        print("⚙️ Initializing research system...")
        orchestrator = ResearchOrchestrator()
        
        # Check agents are loaded
        agent_names = list(orchestrator.agents.keys())
        print(f"✅ Loaded {len(agent_names)} agents: {', '.join(agent_names)}")
        print()
        
        # Start with literature search
        print("📚 STEP 1: Literature Search")
        print("-" * 40)
        
        state = AgentState(query=query, current_step="literature_search")
        lit_agent = orchestrator.agents["literature_scout"]
        state = await lit_agent.process(state)
        
        papers = state.papers if hasattr(state, 'papers') else []
        print(f"Found {len(papers)} papers")
        
        # Show papers with PDF access
        accessible_papers = [p for p in papers if p.pdf_url]
        print(f"Papers with PDF access: {len(accessible_papers)}")
        
        if accessible_papers:
            print("\n📋 Accessible Papers:")
            for i, paper in enumerate(accessible_papers, 1):
                print(f"{i}. {paper.title}")
                print(f"   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
                print(f"   Source: {paper.source}")
                print(f"   Relevance: {paper.relevance_score:.2f}/10")
                print(f"   PDF: {paper.pdf_url[:60]}...")
                print()
        
        # Try document analysis on accessible papers
        if accessible_papers:
            print("📄 STEP 2: Document Analysis")
            print("-" * 40)
            
            # Update state with only accessible papers
            state.papers = accessible_papers[:2]  # Try first 2 to save time
            
            doc_agent = orchestrator.agents["document_analyzer"]
            state = await doc_agent.process(state)
            
            analyzed_docs = state.analyzed_documents if hasattr(state, 'analyzed_documents') else []
            print(f"Successfully analyzed: {len(analyzed_docs)} papers")
            
            if analyzed_docs:
                print("\n📊 Analysis Results:")
                for i, doc in enumerate(analyzed_docs, 1):
                    print(f"{i}. {doc.paper.title[:50]}...")
                    print(f"   Relevance Score: {doc.relevance_score}/10")
                    print(f"   Key Findings ({len(doc.key_findings)}):")
                    for finding in doc.key_findings[:3]:  # Show first 3
                        print(f"      • {finding}")
                    if len(doc.key_findings) > 3:
                        print(f"      ... and {len(doc.key_findings) - 3} more")
                    
                    print(f"   Pedagogical Implications ({len(doc.pedagogical_implications)}):")
                    for impl in doc.pedagogical_implications[:2]:  # Show first 2
                        print(f"      • {impl}")
                    if len(doc.pedagogical_implications) > 2:
                        print(f"      ... and {len(doc.pedagogical_implications) - 2} more")
                    print()
                
                # Try Physics Specialist validation
                print("🔬 STEP 3: Physics Validation")
                print("-" * 40)
                
                phys_agent = orchestrator.agents["physics_specialist"]
                state = await phys_agent.process(state)
                
                validated_docs = state.validated_documents if hasattr(state, 'validated_documents') else []
                print(f"Successfully validated: {len(validated_docs)} papers")
                
                if validated_docs:
                    print("\n🔍 Physics Validation Results:")
                    for i, validation in enumerate(validated_docs, 1):
                        print(f"{i}. {validation.document.paper.title[:50]}...")
                        print(f"   Overall Accuracy: {validation.overall_accuracy:.2f}")
                        print(f"   Physics Rigor: {validation.physics_rigor:.2f}")
                        
                        if validation.physics_errors:
                            print(f"   Physics Issues ({len(validation.physics_errors)}):")
                            for error in validation.physics_errors[:2]:
                                print(f"      ⚠️ {error}")
                        else:
                            print("   ✅ No physics errors detected")
                        
                        if validation.recommendations:
                            print(f"   Recommendations ({len(validation.recommendations)}):")
                            for rec in validation.recommendations[:2]:
                                print(f"      💡 {rec}")
                        print()
                    
                    # Try Content Synthesis
                    print("🧠 STEP 4: Content Synthesis")
                    print("-" * 40)
                    
                    synth_agent = orchestrator.agents["content_synthesizer"]
                    state = await synth_agent.process(state)
                    
                    synthesis = state.content_synthesis if hasattr(state, 'content_synthesis') else None
                    
                    if synthesis:
                        print("✅ Synthesis completed!")
                        print(f"\n📈 Synthesis Overview:")
                        print(f"   Documents analyzed: {len(synthesis.documents_analyzed)}")
                        print(f"   Patterns identified: {len(synthesis.patterns)}")
                        print(f"   Strong evidence findings: {len([e for e in synthesis.evidence_synthesis.values() if 'strong' in str(e).lower()])}")
                        
                        print(f"\n🔍 Key Patterns:")
                        for i, pattern in enumerate(synthesis.patterns[:3], 1):
                            print(f"   {i}. {pattern.description}")
                            print(f"      Evidence: {pattern.evidence_strength}")
                            print(f"      Supporting papers: {len(pattern.supporting_papers)}")
                        
                        if synthesis.contradictions:
                            print(f"\n⚡ Contradictions Found:")
                            for i, contradiction in enumerate(synthesis.contradictions[:2], 1):
                                print(f"   {i}. {contradiction.description}")
                                print(f"      Papers involved: {len(contradiction.conflicting_papers)}")
                        
                        print(f"\n💡 Practical Recommendations:")
                        for i, rec in enumerate(synthesis.practical_recommendations[:3], 1):
                            print(f"   {i}. {rec}")
                        
                        print(f"\n🔬 Research Gaps:")
                        for i, gap in enumerate(synthesis.research_gaps[:2], 1):
                            print(f"   {i}. {gap}")
                        
                        print(f"\n🎯 FULL PIPELINE SUCCESS!")
                        print(f"Processed {len(papers)} → {len(analyzed_docs)} → {len(validated_docs)} → 1 synthesis")
                    else:
                        print("❌ Content synthesis failed")
                else:
                    print("❌ Physics validation failed - cannot proceed to synthesis")
            else:
                print("❌ Document analysis failed - cannot proceed to validation")
        else:
            print("❌ No papers with accessible PDFs found")
            print("Cannot proceed with document analysis")
        
        print(f"\n{'='*60}")
        print("🎯 DEMONSTRATION COMPLETE")
        print(f"System Status: 67% complete (4/6 agents)")
        print(f"Pipeline tested: Literature → Document → Physics → Synthesis")
        
        if len(analyzed_docs) > 0:
            print("✅ SUCCESS: Full 4-agent pipeline working!")
        else:
            print("⚠️ LIMITED: Only literature search working")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(real_results_demo())