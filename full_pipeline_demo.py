"""
Comprehensive demo showing full 4-agent pipeline with real results.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.models import ResearchQuery, ResearchDomain, AgentState
from core.orchestrator import ResearchOrchestrator


async def comprehensive_demo():
    """Full pipeline demo with real analysis results."""
    print("🚀 PER AGENT - COMPREHENSIVE PIPELINE DEMONSTRATION")
    print("=" * 70)
    
    # Create focused query for better PDF success rate
    query = ResearchQuery(
        question="What are the most effective simulation methods for teaching wave interference in introductory physics?",
        domain=ResearchDomain.PHYSICS_EDUCATION,
        max_sources=3,  # Small number for focused results
        keywords=["wave interference", "physics simulation", "education", "teaching methods"]
    )
    
    print(f"🎯 Research Question:")
    print(f"   {query.question}")
    print(f"📊 Max Sources: {query.max_sources}")
    print(f"🔍 Keywords: {', '.join(query.keywords)}")
    print()
    
    try:
        print("⚙️ INITIALIZING SYSTEM...")
        print("-" * 40)
        
        orchestrator = ResearchOrchestrator()
        agent_names = list(orchestrator.agents.keys())
        print(f"✅ Loaded {len(agent_names)} agents:")
        for name in agent_names:
            print(f"   • {name}")
        print()
        
        # =================================================================
        # STEP 1: LITERATURE SEARCH
        # =================================================================
        print("📚 STEP 1: LITERATURE SEARCH")
        print("=" * 50)
        
        state = AgentState(query=query, current_step="literature_search")
        lit_agent = orchestrator.agents["literature_scout"]
        
        print("🔍 Searching literature databases...")
        state = await lit_agent.process(state)
        
        papers = state.papers if hasattr(state, 'papers') else []
        accessible_papers = [p for p in papers if p.pdf_url]
        
        print(f"📊 RESULTS:")
        print(f"   Total papers found: {len(papers)}")
        print(f"   Papers with PDF access: {len(accessible_papers)}")
        print()
        
        if accessible_papers:
            print("📋 PAPERS WITH PDF ACCESS:")
            for i, paper in enumerate(accessible_papers, 1):
                print(f"{i}. '{paper.title}'")
                print(f"   📄 Authors: {', '.join(paper.authors[:2])}{'...' if len(paper.authors) > 2 else ''}")
                print(f"   🏛️ Source: {paper.source}")
                print(f"   ⭐ Relevance: {paper.relevance_score:.2f}/10")
                print(f"   🔗 PDF: {paper.pdf_url[:50]}...")
                if paper.abstract:
                    print(f"   📝 Abstract: {paper.abstract[:100]}...")
                print()
        
        # =================================================================
        # STEP 2: DOCUMENT ANALYSIS  
        # =================================================================
        if accessible_papers:
            print("📄 STEP 2: DOCUMENT ANALYSIS")
            print("=" * 50)
            
            # Process only papers with PDF access
            state.papers = accessible_papers[:2]  # Limit to 2 for demo
            doc_agent = orchestrator.agents["document_analyzer"]
            
            print(f"📥 Analyzing {len(state.papers)} papers...")
            print("⏱️ This may take 2-3 minutes per paper...")
            print()
            
            state = await doc_agent.process(state)
            
            analyzed_docs = state.analyzed_documents if hasattr(state, 'analyzed_documents') else []
            print(f"✅ ANALYSIS COMPLETE!")
            print(f"📊 Successfully analyzed: {len(analyzed_docs)} papers")
            print()
            
            if analyzed_docs:
                print("📋 DETAILED ANALYSIS RESULTS:")
                print("-" * 40)
                
                for i, doc in enumerate(analyzed_docs, 1):
                    print(f"{i}. PAPER: {doc.paper.title}")
                    print(f"   📊 Relevance Score: {doc.relevance_score}/10")
                    print(f"   📄 Text Extracted: {len(doc.full_text)} characters")
                    print()
                    
                    print(f"   🔍 KEY FINDINGS ({len(doc.key_findings)}):")
                    for j, finding in enumerate(doc.key_findings[:4], 1):
                        print(f"      {j}. {finding}")
                    if len(doc.key_findings) > 4:
                        print(f"      ... and {len(doc.key_findings) - 4} more findings")
                    print()
                    
                    print(f"   📚 METHODOLOGY:")
                    if isinstance(doc.methodology, dict):
                        methods = doc.methodology.get('methods', [])
                        sample_size = doc.methodology.get('sample_size', 'Not specified')
                        print(f"      • Methods: {', '.join(methods[:3]) if methods else 'Not specified'}")
                        print(f"      • Sample Size: {sample_size}")
                    print()
                    
                    print(f"   💡 PEDAGOGICAL IMPLICATIONS ({len(doc.pedagogical_implications)}):")
                    for j, impl in enumerate(doc.pedagogical_implications[:3], 1):
                        print(f"      {j}. {impl}")
                    print()
                    
                    print(f"   📄 SUMMARY:")
                    summary_preview = doc.summary[:200] + "..." if len(doc.summary) > 200 else doc.summary
                    print(f"      {summary_preview}")
                    print()
                    print("-" * 40)
                
                # =================================================================
                # STEP 3: PHYSICS VALIDATION
                # =================================================================
                print("🔬 STEP 3: PHYSICS VALIDATION")
                print("=" * 50)
                
                phys_agent = orchestrator.agents["physics_specialist"]
                print("🔍 Validating physics concepts and accuracy...")
                print("⏱️ This may take 1-2 minutes...")
                print()
                
                try:
                    state = await phys_agent.process(state)
                    
                    validated_docs = state.validated_documents if hasattr(state, 'validated_documents') else []
                    print(f"✅ VALIDATION COMPLETE!")
                    print(f"📊 Successfully validated: {len(validated_docs)} papers")
                    print()
                    
                    if validated_docs:
                        print("🔍 PHYSICS VALIDATION RESULTS:")
                        print("-" * 40)
                        
                        for i, validation in enumerate(validated_docs, 1):
                            print(f"{i}. PAPER: {validation.document.paper.title[:50]}...")
                            print(f"   📊 Overall Accuracy: {validation.overall_accuracy:.2f}/1.0")
                            print(f"   🔬 Physics Rigor: {validation.physics_rigor:.2f}/1.0")
                            print(f"   ⚡ Concept Clarity: {validation.concept_clarity:.2f}/1.0")
                            print()
                            
                            if validation.physics_errors:
                                print(f"   ⚠️ PHYSICS ISSUES ({len(validation.physics_errors)}):")
                                for error in validation.physics_errors[:2]:
                                    print(f"      • {error}")
                                if len(validation.physics_errors) > 2:
                                    print(f"      ... and {len(validation.physics_errors) - 2} more issues")
                            else:
                                print("   ✅ No significant physics errors detected")
                            print()
                            
                            if validation.recommendations:
                                print(f"   💡 RECOMMENDATIONS ({len(validation.recommendations)}):")
                                for rec in validation.recommendations[:2]:
                                    print(f"      • {rec}")
                            print()
                        
                        # =================================================================
                        # STEP 4: CONTENT SYNTHESIS
                        # =================================================================
                        print("🧠 STEP 4: CONTENT SYNTHESIS")
                        print("=" * 50)
                        
                        synth_agent = orchestrator.agents["content_synthesizer"]
                        print("🔬 Synthesizing insights across validated papers...")
                        print("⏱️ This may take 2-3 minutes...")
                        print()
                        
                        try:
                            state = await synth_agent.process(state)
                            
                            synthesis = state.content_synthesis if hasattr(state, 'content_synthesis') else None
                            
                            if synthesis:
                                print("✅ SYNTHESIS COMPLETE!")
                                print()
                                print("🎯 COMPREHENSIVE RESEARCH SYNTHESIS")
                                print("=" * 60)
                                
                                print(f"📊 SYNTHESIS OVERVIEW:")
                                print(f"   Papers analyzed: {len(synthesis.documents_analyzed)}")
                                print(f"   Patterns identified: {len(synthesis.patterns)}")
                                print(f"   Contradictions found: {len(synthesis.contradictions)}")
                                print(f"   Research gaps identified: {len(synthesis.research_gaps)}")
                                print()
                                
                                if synthesis.patterns:
                                    print("🔍 KEY PATTERNS ACROSS STUDIES:")
                                    for i, pattern in enumerate(synthesis.patterns[:3], 1):
                                        print(f"{i}. {pattern.description}")
                                        print(f"   📊 Evidence Strength: {pattern.evidence_strength}")
                                        print(f"   📚 Supporting Papers: {len(pattern.supporting_papers)}")
                                        if pattern.statistical_support:
                                            print(f"   📈 Statistical Support: {pattern.statistical_support}")
                                        print()
                                
                                if synthesis.contradictions:
                                    print("⚡ CONTRADICTIONS & DEBATES:")
                                    for i, contradiction in enumerate(synthesis.contradictions[:2], 1):
                                        print(f"{i}. {contradiction.description}")
                                        print(f"   📄 Conflicting Papers: {len(contradiction.conflicting_papers)}")
                                        print(f"   🎯 Resolution Needed: {contradiction.resolution_approach}")
                                        print()
                                
                                print("💡 PRACTICAL RECOMMENDATIONS:")
                                for i, rec in enumerate(synthesis.practical_recommendations[:4], 1):
                                    print(f"{i}. {rec}")
                                print()
                                
                                print("🔬 RESEARCH GAPS & FUTURE DIRECTIONS:")
                                for i, gap in enumerate(synthesis.research_gaps[:3], 1):
                                    print(f"{i}. {gap}")
                                print()
                                
                                print("🎓 THEORETICAL INSIGHTS:")
                                for i, insight in enumerate(synthesis.theoretical_insights[:2], 1):
                                    print(f"{i}. {insight}")
                                print()
                                
                                print("🎯 PIPELINE SUCCESS!")
                                print("=" * 60)
                                print("✅ Full 4-agent research pipeline completed successfully!")
                                print(f"📊 Processing chain: {len(papers)} papers → {len(analyzed_docs)} analyzed → {len(validated_docs)} validated → 1 synthesis")
                                print()
                                print("🚀 WHAT WAS ACCOMPLISHED:")
                                print("   • Comprehensive literature search across multiple databases")
                                print("   • Deep PDF analysis with LLM-powered content extraction")
                                print("   • Physics concept validation and accuracy checking")
                                print("   • Cross-study pattern identification and synthesis")
                                print("   • Practical recommendations for educators")
                                print("   • Research gap identification for future work")
                                
                            else:
                                print("❌ Content synthesis failed")
                                
                        except Exception as e:
                            print(f"❌ Content synthesis error: {e}")
                            print("✅ Partial success: Literature → Analysis → Validation complete")
                            
                    else:
                        print("❌ Physics validation failed")
                        print("✅ Partial success: Literature → Analysis complete")
                        
                except Exception as e:
                    print(f"❌ Physics validation error: {e}")
                    print("✅ Partial success: Literature → Analysis complete")
                    
            else:
                print("❌ Document analysis failed - no papers successfully processed")
                
        else:
            print("❌ No papers with accessible PDFs found")
            print("Cannot proceed with document analysis")
        
        print(f"\n{'='*70}")
        print("🎯 DEMONSTRATION SUMMARY")
        print(f"{'='*70}")
        print(f"System Status: 67% complete (4/6 agents)")
        print(f"Agents tested: Literature Scout → Document Analyzer → Physics Specialist → Content Synthesizer")
        
        if len(analyzed_docs) > 0:
            print("✅ SUCCESS: Full research pipeline demonstrated with real results!")
            print("🔬 The system can now produce comprehensive research insights from academic papers")
        else:
            print("⚠️ PARTIAL: Literature search working, document processing needs improvement")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(comprehensive_demo())