"""
Command Line Interface for PER Agent system.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from core.config import Config
from core.models import ResearchQuery, ResearchDomain, ReportFormat
from core.orchestrator import ResearchOrchestrator


class PERCLI:
    """Command Line Interface for PER Agent."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.config = Config.from_env()
        print(f"🔬 Physics Education Research (PER) Agent v0.1.0")
        print(f"📁 Output directory: {self.config.outputs_dir}")
        print(f"🤖 Ollama host: {self.config.ollama_host}")
        print("-" * 60)
    
    def display_welcome(self):
        """Display welcome message and instructions."""
        print("""
Welcome to the PER Agent System! 🎓

This AI-powered research assistant specializes in physics education research.
It can help you find, analyze, and synthesize academic literature to answer
your research questions.

FEATURES:
✨ Literature search across arXiv, Semantic Scholar, and Google Scholar
📄 Automated PDF analysis and key finding extraction  
🔬 Physics concept validation and mathematical accuracy checking
🧠 Content synthesis with pattern recognition
📊 Professional report generation (Markdown, LaTeX, PDF)
✅ Quality assurance and academic standards compliance

EXAMPLE QUERIES:
- "How effective are interactive simulations in teaching wave physics?"
- "What pedagogical approaches work best for teaching quantum mechanics?"
- "Impact of virtual labs on student understanding in electromagnetism"
- "Best practices for teaching physics problem-solving skills"

Ready to start your research? 🚀
        """)
    
    def get_research_query(self) -> Optional[ResearchQuery]:
        """Get research query from user input."""
        try:
            print("\n" + "="*60)
            print("📝 NEW RESEARCH QUERY")
            print("="*60)
            
            # Get main question
            question = input("\n🔍 Enter your research question: ").strip()
            if not question:
                print("❌ Question cannot be empty.")
                return None
            
            # Get domain (optional)
            print("\n📚 Research Domain:")
            print("1. Physics Education (default)")
            print("2. General Physics") 
            print("3. Education Technology")
            print("4. Pedagogy")
            
            domain_choice = input("\nSelect domain (1-4, or press Enter for default): ").strip()
            domain_map = {
                "1": ResearchDomain.PHYSICS_EDUCATION,
                "2": ResearchDomain.GENERAL_PHYSICS,
                "3": ResearchDomain.EDUCATION_TECHNOLOGY,
                "4": ResearchDomain.PEDAGOGY
            }
            domain = domain_map.get(domain_choice, ResearchDomain.PHYSICS_EDUCATION)
            
            # Get max sources
            max_sources_input = input("\n📊 Maximum sources to analyze (default: 20): ").strip()
            max_sources = int(max_sources_input) if max_sources_input.isdigit() else 20
            max_sources = min(max_sources, 50)  # Cap at 50
            
            # Get keywords (optional)
            keywords_input = input("\n🏷️  Keywords (comma-separated, optional): ").strip()
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()] if keywords_input else []
            
            # Get report format
            print("\n📄 Report Format:")
            print("1. Markdown (default)")
            print("2. LaTeX")
            print("3. PDF")
            print("4. HTML")
            
            format_choice = input("\nSelect format (1-4, or press Enter for default): ").strip()
            format_map = {
                "1": ReportFormat.MARKDOWN,
                "2": ReportFormat.LATEX,
                "3": ReportFormat.PDF,
                "4": ReportFormat.HTML
            }
            report_format = format_map.get(format_choice, ReportFormat.MARKDOWN)
            
            # Create query
            query = ResearchQuery(
                question=question,
                domain=domain,
                max_sources=max_sources,
                keywords=keywords,
                report_format=report_format
            )
            
            # Confirm query
            print(f"\n✅ QUERY SUMMARY:")
            print(f"   Question: {query.question}")
            print(f"   Domain: {query.domain.value}")
            print(f"   Max Sources: {query.max_sources}")
            print(f"   Keywords: {', '.join(query.keywords) if query.keywords else 'None'}")
            print(f"   Format: {query.report_format.value}")
            
            confirm = input(f"\n🚀 Start research? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Research cancelled.")
                return None
                
            return query
            
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user.")
            return None
        except Exception as e:
            print(f"❌ Error creating query: {e}")
            return None
    
    async def run_research(self, query: ResearchQuery):
        """Run the research workflow."""
        try:
            print(f"\n🔄 Starting research workflow...")
            print(f"⏰ This may take several minutes depending on the complexity.")
            print(f"📊 Progress will be shown as agents complete their work.\n")
            
            # Initialize orchestrator
            orchestrator = ResearchOrchestrator(self.config)
            
            # Check system info
            system_info = orchestrator.get_system_info()
            print(f"🖥️  System Info:")
            print(f"   Models configured: {system_info['models_configured']}")
            print(f"   Agents ready: {system_info['agents_initialized']}")
            print(f"   VRAM validation: {'✅' if system_info['vram_validation'] else '❌'}")
            print(f"   Output directory: {system_info['output_directory']}")
            
            if not system_info['vram_validation']:
                print("⚠️  Warning: System may not have enough VRAM for optimal performance.")
                
            print(f"\n{'='*60}")
            print("🚀 RESEARCH WORKFLOW STARTING")
            print(f"{'='*60}")
            
            # Run research
            result = await orchestrator.research(query)
            
            # Display results
            print(f"\n{'='*60}")
            print("✅ RESEARCH COMPLETED")
            print(f"{'='*60}")
            
            print(result.get_summary())
            
            if result.generated_report:
                print(f"\n📊 Report generated successfully!")
                print(f"   Format: {result.generated_report.format.value}")
                print(f"   Word count: {result.generated_report.word_count}")
                
            if result.quality_assessment:
                score = result.quality_assessment.overall_score
                print(f"\n🎯 Quality Score: {score:.1%}")
                if score >= 0.8:
                    print("   ✅ High quality research completed!")
                elif score >= 0.6:
                    print("   ⚠️  Moderate quality - review recommended")
                else:
                    print("   ❌ Low quality - manual review required")
            
            print(f"\n📁 Results saved to: {self.config.outputs_dir / query.session_id}")
            
        except Exception as e:
            print(f"\n❌ Research failed: {e}")
            print("Please check the logs for more details.")
    
    async def main_loop(self):
        """Main CLI loop."""
        self.display_welcome()
        
        while True:
            try:
                print(f"\n{'='*60}")
                print("MAIN MENU")
                print(f"{'='*60}")
                print("1. 🔍 Start New Research")
                print("2. 📊 System Status")
                print("3. 📁 View Recent Results")
                print("4. ❓ Help")
                print("5. 🚪 Exit")
                
                choice = input("\nSelect option (1-5): ").strip()
                
                if choice == "1":
                    query = self.get_research_query()
                    if query:
                        await self.run_research(query)
                        
                elif choice == "2":
                    await self.show_system_status()
                    
                elif choice == "3":
                    self.show_recent_results()
                    
                elif choice == "4":
                    self.show_help()
                    
                elif choice == "5":
                    print("👋 Thank you for using PER Agent! Goodbye!")
                    break
                    
                else:
                    print("❌ Invalid choice. Please select 1-5.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
    
    async def show_system_status(self):
        """Show system status and diagnostics."""
        print(f"\n{'='*60}")
        print("🖥️  SYSTEM STATUS")
        print(f"{'='*60}")
        
        try:
            orchestrator = ResearchOrchestrator(self.config)
            system_info = orchestrator.get_system_info()
            
            print(f"✅ System Version: {system_info['version']}")
            print(f"✅ Models Configured: {system_info['models_configured']}")
            print(f"✅ Agents Initialized: {system_info['agents_initialized']}")
            print(f"✅ VRAM Validation: {'Passed' if system_info['vram_validation'] else 'Failed'}")
            print(f"✅ Ollama Host: {system_info['ollama_host']}")
            print(f"✅ Output Directory: {system_info['output_directory']}")
            
            # TODO: Add model availability check when Ollama integration is complete
            print(f"\n⏳ Note: Full system diagnostics will be available after Ollama integration.")
            
        except Exception as e:
            print(f"❌ Failed to get system status: {e}")
    
    def show_recent_results(self):
        """Show recent research results."""
        print(f"\n{'='*60}")
        print("📁 RECENT RESULTS")
        print(f"{'='*60}")
        
        try:
            results_dir = self.config.outputs_dir
            if not results_dir.exists():
                print("📭 No results found. Complete your first research to see results here.")
                return
            
            result_folders = [d for d in results_dir.iterdir() if d.is_dir()]
            if not result_folders:
                print("📭 No results found.")
                return
            
            # Sort by creation time (newest first)
            result_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            print(f"Found {len(result_folders)} research sessions:\n")
            
            for i, folder in enumerate(result_folders[:5]):  # Show last 5
                print(f"{i+1}. 📂 {folder.name}")
                
                # Try to read summary if available
                result_file = folder / "result.json"
                if result_file.exists():
                    try:
                        import json
                        with open(result_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        question = data.get('query', {}).get('question', 'Unknown')
                        quality_score = data.get('quality_score', 0.0)
                        
                        print(f"   📝 Question: {question[:60]}{'...' if len(question) > 60 else ''}")
                        print(f"   🎯 Quality: {quality_score:.1%}")
                        
                    except Exception:
                        print(f"   📄 Results available (details unavailable)")
                else:
                    print(f"   📄 Session folder created")
                print()
            
            if len(result_folders) > 5:
                print(f"... and {len(result_folders) - 5} more sessions")
                
        except Exception as e:
            print(f"❌ Failed to load recent results: {e}")
    
    def show_help(self):
        """Show help information."""
        print(f"\n{'='*60}")
        print("❓ HELP & DOCUMENTATION")
        print(f"{'='*60}")
        print("""
🔍 RESEARCH QUERIES:
   - Be specific about your physics education topic
   - Include key terms like "teaching", "learning", "simulation", etc.
   - Mention specific physics concepts when relevant
   
📚 DOMAINS:
   - Physics Education: Focus on teaching/learning physics (recommended)
   - General Physics: Broader physics research context
   - Education Technology: Technology in education
   - Pedagogy: General teaching methodologies
   
📊 SOURCES:
   - System searches arXiv, Semantic Scholar, and Google Scholar
   - More sources = better coverage but longer processing time
   - Recommended: 15-25 sources for comprehensive research
   
📄 REPORT FORMATS:
   - Markdown: Easy to read, good for sharing
   - LaTeX: Academic formatting, good for papers
   - PDF: Professional output, ready to print
   - HTML: Web-friendly format
   
🎯 QUALITY SCORES:
   - 80%+: High quality, ready for use
   - 60-79%: Good quality, minor review needed
   - <60%: Requires careful review and validation

📁 OUTPUT LOCATION:
   Results are saved in: {self.config.outputs_dir}
   
🤖 SYSTEM REQUIREMENTS:
   - Ollama server running (for local LLMs)
   - RTX 5070 Ti or equivalent (16GB VRAM recommended)
   - Internet connection (for literature search)
   
🆘 TROUBLESHOOTING:
   - Check Ollama is running: ollama list
   - Verify internet connection for literature search
   - Check output directory permissions
   - Review logs in the logs/ directory
        """)


async def main():
    """Main entry point."""
    cli = PERCLI()
    await cli.main_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)