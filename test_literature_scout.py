"""
Test script for Literature Scout Agent - can be run without Ollama for API testing.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.core.config import Config
from src.core.models import ResearchQuery, ResearchDomain, AgentState
from src.agents.literature_scout import LiteratureScoutAgent


async def test_literature_scout_basic():
    """Test basic Literature Scout functionality without LLM calls."""
    print("🔬 Testing Literature Scout Agent - Basic Functionality")
    print("=" * 60)
    
    try:
        # Initialize configuration
        config = Config()
        agent_config = config.get_agent_config("literature_scout")
        
        # Create agent (this will fail at LLM init, but we can test other parts)
        print("📊 Configuration loaded successfully")
        print(f"   Agent: {agent_config.name}")
        print(f"   Model: {agent_config.model.name}")
        print(f"   Capabilities: {', '.join(agent_config.capabilities)}")
        
        # Test query creation
        query = ResearchQuery(
            question="How effective are interactive simulations in teaching wave physics?",
            domain=ResearchDomain.PHYSICS_EDUCATION,
            max_sources=10,
            keywords=["wave physics", "simulations", "interactive learning"]
        )
        
        print(f"\n🔍 Test Query Created:")
        print(f"   Question: {query.question}")
        print(f"   Domain: {query.domain.value}")
        print(f"   Max Sources: {query.max_sources}")
        print(f"   Keywords: {', '.join(query.keywords)}")
        
        # Test arXiv search (without LLM ranking)
        print(f"\n📚 Testing arXiv API Integration...")
        
        # Create a mock agent to test search functionality
        class MockLiteratureScout:
            def __init__(self):
                import arxiv
                self.arxiv_client = arxiv.Client()
                self.max_arxiv_results = 5
                
            async def test_arxiv_search(self, query_text: str):
                """Test arXiv search without LLM processing."""
                try:
                    import arxiv
                    search = arxiv.Search(
                        query=f'"{query_text}"',
                        max_results=self.max_arxiv_results,
                        sort_by=arxiv.SortCriterion.Relevance
                    )
                    
                    papers = []
                    for result in self.arxiv_client.results(search):
                        papers.append({
                            "title": result.title,
                            "authors": [str(author) for author in result.authors[:2]],
                            "published": result.published.strftime("%Y-%m-%d"),
                            "url": result.entry_id
                        })
                        if len(papers) >= 3:  # Limit for testing
                            break
                    
                    return papers
                except Exception as e:
                    print(f"   ❌ arXiv API Error: {e}")
                    return []
        
        mock_agent = MockLiteratureScout()
        arxiv_results = await mock_agent.test_arxiv_search("wave physics education")
        
        if arxiv_results:
            print(f"   ✅ arXiv API Working - Found {len(arxiv_results)} papers")
            for i, paper in enumerate(arxiv_results, 1):
                print(f"      {i}. {paper['title'][:60]}...")
                print(f"         Authors: {', '.join(paper['authors'])}")
                print(f"         Published: {paper['published']}")
        else:
            print("   ⚠️ No results from arXiv (may be network or query issue)")
        
        # Test Semantic Scholar search
        print(f"\n🔬 Testing Semantic Scholar API Integration...")
        
        try:
            import requests
            
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": "physics education wave simulations",
                "limit": 3,
                "fields": "paperId,title,authors,year,citationCount"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("data", [])
            
            if results:
                print(f"   ✅ Semantic Scholar API Working - Found {len(results)} papers")
                for i, paper in enumerate(results, 1):
                    authors = [a.get("name", "Unknown") for a in paper.get("authors", [])[:2]]
                    print(f"      {i}. {paper.get('title', 'Untitled')[:60]}...")
                    print(f"         Authors: {', '.join(authors)}")
                    print(f"         Year: {paper.get('year', 'Unknown')}, Citations: {paper.get('citationCount', 0)}")
            else:
                print("   ⚠️ No results from Semantic Scholar")
                
        except Exception as e:
            print(f"   ❌ Semantic Scholar API Error: {e}")
        
        print(f"\n✅ Basic Literature Scout Test Completed")
        print(f"📊 Summary:")
        print(f"   - Configuration: ✅ Working")
        print(f"   - Query Creation: ✅ Working") 
        print(f"   - arXiv API: {'✅ Working' if arxiv_results else '⚠️ Issues'}")
        print(f"   - Semantic Scholar API: Testing above")
        print(f"\n💡 Next Step: Test with Ollama running for full LLM integration")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_with_ollama():
    """Test full Literature Scout with Ollama LLM integration."""
    print("\n" + "=" * 60)
    print("🤖 Testing Literature Scout Agent - Full LLM Integration")
    print("=" * 60)
    
    try:
        # Check if Ollama is running
        import requests
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"✅ Ollama is running with {len(models)} models")
                for model in models[:3]:  # Show first 3 models
                    print(f"   - {model['name']}")
            else:
                print("❌ Ollama is not responding properly")
                return
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            print("💡 Please start Ollama with: ollama serve")
            return
        
        # Initialize full agent
        config = Config()
        agent = LiteratureScoutAgent(
            config=config.get_agent_config("literature_scout"),
            ollama_host=config.ollama_host
        )
        
        print("✅ Literature Scout Agent initialized successfully")
        
        # Test health check
        health = await agent.health_check()
        print(f"🏥 Health Check: {health['status']}")
        if health['status'] == 'unhealthy':
            print(f"❌ Agent unhealthy: {health.get('error', 'Unknown error')}")
            return
        
        # Create test query
        query = ResearchQuery(
            question="How do interactive simulations help students understand wave physics?",
            domain=ResearchDomain.PHYSICS_EDUCATION,
            max_sources=8,
            keywords=["wave physics", "simulations", "student understanding"]
        )
        
        # Create agent state
        state = AgentState(query=query, current_step="literature_search")
        
        print(f"\n🔍 Running full literature search...")
        print(f"   Query: {query.question}")
        print(f"   Max Sources: {query.max_sources}")
        
        # Run the agent
        result = await agent.process(state)
        
        if result.get("success"):
            papers = result.get("papers", [])
            print(f"✅ Literature search completed successfully!")
            print(f"📊 Results:")
            print(f"   - Total found: {result.get('total_found', 0)}")
            print(f"   - Unique papers: {result.get('unique_count', 0)}")
            print(f"   - Final selection: {len(papers)}")
            print(f"   - Enhanced keywords: {len(result.get('enhanced_keywords', []))}")
            
            if papers:
                print(f"\n📑 Top 3 Papers:")
                for i, paper in enumerate(papers[:3], 1):
                    print(f"   {i}. {paper.title[:60]}...")
                    print(f"      Score: {paper.relevance_score:.2f}")
                    print(f"      Authors: {', '.join(paper.authors[:2])}")
                    print(f"      Source: {paper.source}")
                    if paper.published_date:
                        print(f"      Year: {paper.published_date.year}")
                    print()
            
            print("🎉 Full Literature Scout Agent test successful!")
            
        else:
            print(f"❌ Literature search failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Full test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🧪 PER Agent - Literature Scout Test Suite")
    print("=" * 60)
    
    # Always run basic test
    await test_literature_scout_basic()
    
    # Ask user if they want to test with Ollama
    try:
        user_input = input(f"\n🤖 Test with Ollama LLM integration? (y/N): ").strip().lower()
        if user_input == 'y':
            await test_with_ollama()
        else:
            print("⏭️ Skipping Ollama test. Run 'ollama serve' and rerun for full testing.")
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Test interrupted by user")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Testing stopped by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)