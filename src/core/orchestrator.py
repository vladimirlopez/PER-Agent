"""
Main orchestrator for the PER Agent system using LangGraph.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from .config import Config
from .models import ResearchQuery, ResearchResult, AgentState

# Import implemented agents
from agents.literature_scout import LiteratureScoutAgent
from agents.document_analyzer import DocumentAnalyzerAgent
from agents.physics_specialist import PhysicsSpecialistAgent
from agents.content_synthesizer import ContentSynthesizerAgent
from agents.report_generator import ReportGeneratorAgent
from agents.quality_controller import QualityControllerAgent

class ResearchOrchestrator:
    """
    Main orchestrator that coordinates all agents using LangGraph workflow.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the research orchestrator."""
        self.config = config or Config.from_env()
        self.logger = self._setup_logging()
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Initialize LangGraph workflow
        self.workflow = self._build_workflow()
        self.memory = MemorySaver()
        
        # Compile the workflow with checkpointing
        self.app = self.workflow.compile(checkpointer=self.memory)
        
        self.logger.info("ResearchOrchestrator initialized successfully")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("per_agent")
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.config.logs_dir / f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agents with their configurations."""
        agents = {}
        
        try:
            # Initialize implemented agents
            agents["literature_scout"] = LiteratureScoutAgent(
                config=self.config.get_agent_config("literature_scout"),
                ollama_host=self.config.ollama_host
            )
            
            agents["document_analyzer"] = DocumentAnalyzerAgent(
                config=self.config.get_agent_config("document_analyzer"),
                ollama_host=self.config.ollama_host
            )
            
            agents["physics_specialist"] = PhysicsSpecialistAgent(
                config=self.config.get_agent_config("physics_specialist"),
                ollama_host=self.config.ollama_host
            )
            
            agents["content_synthesizer"] = ContentSynthesizerAgent(
                config=self.config.get_agent_config("content_synthesizer"),
                ollama_host=self.config.ollama_host
            )
            
            agents["report_generator"] = ReportGeneratorAgent(
                config=self.config.get_agent_config("report_generator"),
                ollama_host=self.config.ollama_host
            )
            
            agents["quality_controller"] = QualityControllerAgent(
                config=self.config.get_agent_config("quality_controller"),
                ollama_host=self.config.ollama_host
            )
            
            self.logger.info(f"Initialized {len(agents)} agents successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
        
        return agents
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for the research process."""
        workflow = StateGraph(AgentState)
        
        # Add nodes for implemented agents only
        workflow.add_node("literature_search", self._literature_search_node)
        workflow.add_node("document_analysis", self._document_analysis_node)
        workflow.add_node("physics_validation", self._physics_validation_node)
        workflow.add_node("content_synthesis", self._content_synthesis_node)
        workflow.add_node("report_generation", self._report_generation_node)
        workflow.add_node("quality_control", self._quality_control_node)
        
        # Define the workflow edges - connect implemented agents
        workflow.set_entry_point("literature_search")
        
        # Connect literature search to document analysis
        workflow.add_edge("literature_search", "document_analysis")
        
        # Connect document analysis to physics validation
        workflow.add_edge("document_analysis", "physics_validation")
        
        # Connect physics validation to content synthesis
        workflow.add_edge("physics_validation", "content_synthesis")
        
        # Connect content synthesis to report generation
        workflow.add_edge("content_synthesis", "report_generation")
        
        # Connect report generation to quality control
        workflow.add_edge("report_generation", "quality_control")
        
        # Quality control leads to END (final step)
        workflow.add_edge("quality_control", END)
        #         "revision_needed": "content_synthesis"
        #     }
        # )
        
        return workflow
    
    async def _literature_search_node(self, state: AgentState) -> AgentState:
        """Literature search node execution."""
        self.logger.info("Starting literature search...")
        
        try:
            result_state = await self.agents["literature_scout"].process(state)
            # The agent returns the updated state directly
            state = result_state
            state.current_step = "literature_search_complete"
            
            self.logger.info(f"Found {len(state.papers)} papers")
            
        except Exception as e:
            self.logger.error(f"Literature search failed: {e}")
            state.errors.append(f"Literature search error: {e}")
        
        return state
    
    async def _document_analysis_node(self, state: AgentState) -> AgentState:
        """Document analysis node execution."""
        self.logger.info("Starting document analysis...")
        
        try:
            # Set papers from literature search results
            state.papers = state.literature_results
            
            # Process through Document Analyzer Agent
            result = await self.agents["document_analyzer"].process(state)
            state.analyzed_documents = result.analyzed_documents
            state.current_step = "document_analysis_complete"
            
            self.logger.info(f"Analyzed {len(state.analyzed_documents)} documents")
            
        except Exception as e:
            self.logger.error(f"Document analysis failed: {e}")
            state.errors.append(f"Document analysis error: {e}")
        
        return state
    
    async def _physics_validation_node(self, state: AgentState) -> AgentState:
        """Physics validation node execution."""
        self.logger.info("Starting physics validation...")
        
        try:
            # Process through Physics Specialist Agent
            result_state = await self.agents["physics_specialist"].process(state)
            state = result_state
            state.current_step = "physics_validation_complete"
            
            validation_count = len(state.validation_results) if hasattr(state, 'validation_results') and state.validation_results else 0
            self.logger.info(f"Physics validation completed for {validation_count} documents")
            
        except Exception as e:
            self.logger.error(f"Physics validation failed: {e}")
            state.errors.append(f"Physics validation error: {e}")
        
        return state
    
    async def _content_synthesis_node(self, state: AgentState) -> AgentState:
        """Content synthesis node execution."""
        self.logger.info("Starting content synthesis...")
        
        try:
            # Process through Content Synthesizer Agent
            result_state = await self.agents["content_synthesizer"].process(state)
            state = result_state
            state.current_step = "content_synthesis_complete"
            
            insights_count = len(state.synthesis_insights) if hasattr(state, 'synthesis_insights') and state.synthesis_insights else 0
            self.logger.info(f"Content synthesis completed with {insights_count} insights generated")
            
        except Exception as e:
            self.logger.error(f"Content synthesis failed: {e}")
            state.errors.append(f"Content synthesis error: {e}")
        
        return state
    
    async def _report_generation_node(self, state: AgentState) -> AgentState:
        """Report generation node execution."""
        self.logger.info("Starting report generation...")
        
        try:
            # Process through Report Generator Agent
            result_state = await self.agents["report_generator"].process(state)
            state = result_state
            state.current_step = "report_generation_complete"
            
            # Log report generation results
            if hasattr(state, 'research_report') and state.research_report:
                report = state.research_report
                formats = list(report.file_paths.keys())
                pdfs_preserved = report.metadata.get('pdfs_preserved', 0)
                quality_score = report.quality_score
                
                self.logger.info(f"Report generation completed successfully")
                self.logger.info(f"Generated formats: {', '.join(formats)}")
                self.logger.info(f"PDFs preserved: {pdfs_preserved}")
                self.logger.info(f"Report quality score: {quality_score:.2f}")
            else:
                self.logger.warning("Report generation completed but no report object created")
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            state.errors.append(f"Report generation error: {e}")
        
        return state
    
    async def _quality_control_node(self, state: AgentState) -> AgentState:
        """Quality control node execution."""
        self.logger.info("Starting quality control...")
        
        try:
            # Process through Quality Controller Agent
            result_state = await self.agents["quality_controller"].process(state)
            state = result_state
            state.current_step = "quality_control_complete"
            
            quality_score = state.quality_assessment.overall_score if state.quality_assessment else 0.0
            quality_level = state.quality_assessment.quality_level if state.quality_assessment else "UNKNOWN"
            
            self.logger.info(f"Quality control completed. Score: {quality_score:.2f}/10.0, Level: {quality_level}")
            self.logger.info(f"Quality certified: {state.quality_certified}")
            
        except Exception as e:
            self.logger.error(f"Quality control failed: {e}")
            state.errors.append(f"Quality control error: {e}")
        
        return state
    
    def _quality_decision(self, state: AgentState) -> str:
        """Decide whether the research quality is acceptable."""
        if not state.quality_assessment:
            return "revision_needed"
        
        quality_score = state.quality_assessment.get("score", 0.0)
        revision_count = state.revision_count
        
        # Check if quality meets threshold and hasn't exceeded max revisions
        if quality_score >= self.config.min_quality_score:
            return "approved"
        elif revision_count < self.config.max_workflow_retries:
            state.revision_count += 1
            return "revision_needed"
        else:
            # Force approval if max revisions reached
            self.logger.warning(f"Max revisions reached. Approving with score: {quality_score}")
            return "approved"
    
    async def research(self, query: ResearchQuery) -> ResearchResult:
        """
        Execute a complete research workflow.
        
        Args:
            query: The research query to process
            
        Returns:
            ResearchResult containing all findings and generated reports
        """
        self.logger.info(f"Starting research for query: {query.question}")
        
        # Initialize state
        initial_state = AgentState(
            query=query,
            current_step="initialized",
            errors=[],
            revision_count=0
        )
        
        try:
            # Create a unique thread ID for this research session
            thread_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            config = {"configurable": {"thread_id": thread_id}}
            
            # Execute the workflow
            final_state = await self.app.ainvoke(initial_state, config=config)
            
            # Build result
            result = ResearchResult(
                query=query,
                literature_sources=final_state.get('literature_results', []) if isinstance(final_state, dict) else (final_state.literature_results if hasattr(final_state, 'literature_results') else []),
                analysis_summary=final_state.get('synthesized_content', {}) if isinstance(final_state, dict) else (final_state.synthesized_content if hasattr(final_state, 'synthesized_content') else {}),
                report=final_state.get('generated_report', {}) if isinstance(final_state, dict) else (final_state.generated_report if hasattr(final_state, 'generated_report') else {}),
                quality_score=final_state.get('quality_assessment', {}).get("score", 0.0) if isinstance(final_state, dict) else (final_state.quality_assessment.get("score", 0.0) if hasattr(final_state, 'quality_assessment') else 0.0),
                processing_time=datetime.now() - query.timestamp,
                errors=final_state.get('errors', []) if isinstance(final_state, dict) else (final_state.errors if hasattr(final_state, 'errors') else [])
            )
            
            # Save result to disk
            self._save_result(result, thread_id)
            
            self.logger.info(f"Research completed successfully. Quality score: {result.quality_score}")
            return result
            
        except Exception as e:
            self.logger.error(f"Research workflow failed: {e}")
            raise
    
    def _save_result(self, result: ResearchResult, thread_id: str):
        """Save research result to disk."""
        try:
            output_dir = self.config.outputs_dir / thread_id
            output_dir.mkdir(exist_ok=True)
            
            # Save as JSON
            import json
            result_file = output_dir / "result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False, default=str)
            
            # Save report if available
            if result.report and "content" in result.report:
                report_file = output_dir / "report.md"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(result.report["content"])
            
            self.logger.info(f"Results saved to {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    async def get_workflow_status(self, thread_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow execution."""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = await self.app.aget_state(config)
            
            return {
                "current_step": state.values.get("current_step", "unknown"),
                "errors": state.values.get("errors", []),
                "revision_count": state.values.get("revision_count", 0),
                "quality_score": state.values.get("quality_assessment", {}).get("score", 0.0)
            }
        except Exception as e:
            self.logger.error(f"Failed to get workflow status: {e}")
            return {"error": str(e)}
    
    def list_available_models(self) -> List[str]:
        """List all available models in the configuration."""
        return list(self.config.models.keys())
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information and status."""
        return {
            "version": "0.1.0",
            "models_configured": len(self.config.models),
            "agents_initialized": len(self.agents),
            "vram_validation": self.config.validate_system_requirements(),
            "ollama_host": self.config.ollama_host,
            "output_directory": str(self.config.outputs_dir)
        }