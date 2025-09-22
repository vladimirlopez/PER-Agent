"""
Simple test to focus on just getting PDF analysis working.
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.models import ResearchQuery, ResearchDomain, AgentState, Paper
from agents.document_analyzer import DocumentAnalyzerAgent
from agents.literature_scout import LiteratureScoutAgent


async def simple_pdf_test():
    """Simple test focusing just on PDF analysis."""
    print("🔍 SIMPLE PDF ANALYSIS TEST")
    print("=" * 40)
    
    try:
        # Create a simple paper object with a known arXiv PDF
        test_paper = Paper(
            title="Interactive simulation for teaching wave physics concepts",
            authors=["Test Author"],
            abstract="A study on interactive simulations for wave physics education",
            url="https://arxiv.org/abs/1509.07740",  # Known arXiv paper
            pdf_url="https://arxiv.org/pdf/1509.07740.pdf",  # Direct PDF URL
            published_date=None,
            source="arxiv",
            doi="",
            relevance_score=8.5
        )
        
        print(f"📄 Testing paper: {test_paper.title}")
        print(f"🔗 PDF URL: {test_paper.pdf_url}")
        print()
        
        # Initialize Document Analyzer
        print("⚙️ Initializing Document Analyzer...")
        
        # Import the config classes
        from core.config import AgentConfig, ModelConfig
        
        # Create proper config
        model_config = ModelConfig(
            name="Qwen2.5-Coder-14B",
            model_id="qwen2.5-coder:14b",
            vram_usage=9,
            context_length=32000,
            quantization="Q4_K_M",
            temperature=0.1,
            max_tokens=4096
        )
        
        agent_config = AgentConfig(
            name="Document Analyzer",
            model=model_config,
            role="Document analyzer and content extractor",
            capabilities=["pdf_processing", "text_extraction", "content_analysis"],
            max_retries=3,
            timeout=300
        )
        
        doc_analyzer = DocumentAnalyzerAgent(agent_config)
        
        print("✅ Document Analyzer initialized")
        print()
        
        # Create state with just this one paper
        query = ResearchQuery(
            question="Test PDF processing",
            domain=ResearchDomain.PHYSICS_EDUCATION,
            max_sources=1,
            keywords=["test"]
        )
        
        state = AgentState(query=query, current_step="document_analysis")
        state.papers = [test_paper]
        
        print("📥 Starting PDF download and analysis...")
        print("This may take a few minutes...")
        print()
        
        # Process the paper
        result_state = await doc_analyzer.process(state)
        
        analyzed_docs = result_state.analyzed_documents if hasattr(result_state, 'analyzed_documents') else []
        
        print(f"✅ Analysis complete!")
        print(f"📊 Successfully analyzed: {len(analyzed_docs)} papers")
        print()
        
        if analyzed_docs:
            doc = analyzed_docs[0]
            print("📋 ANALYSIS RESULTS:")
            print("-" * 20)
            print(f"Paper: {doc.paper.title}")
            print(f"Relevance Score: {doc.relevance_score}/10")
            print(f"Text Length: {len(doc.full_text)} characters")
            print()
            
            print("🔍 Key Findings:")
            for i, finding in enumerate(doc.key_findings[:5], 1):
                print(f"  {i}. {finding}")
            print()
            
            print("📚 Methodology:")
            methodology = doc.methodology
            if isinstance(methodology, dict):
                methods = methodology.get('methods', [])
                print(f"  Methods: {', '.join(methods) if methods else 'Not specified'}")
                sample_size = methodology.get('sample_size', 'Not specified')
                print(f"  Sample Size: {sample_size}")
            else:
                print(f"  {methodology}")
            print()
            
            print("💡 Pedagogical Implications:")
            for i, impl in enumerate(doc.pedagogical_implications[:3], 1):
                print(f"  {i}. {impl}")
            print()
            
            print("📄 Summary:")
            print(f"  {doc.summary}")
            print()
            
            print("✅ SUCCESS: PDF analysis pipeline working!")
            
        else:
            print("❌ No papers were successfully analyzed")
            print("Check the logs above for error details")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simple_pdf_test())