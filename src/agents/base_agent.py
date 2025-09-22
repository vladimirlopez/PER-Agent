"""
Base agent class for all PER Agent system agents.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.config import AgentConfig
from core.models import AgentState


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the PER system.
    Provides common functionality for LLM interaction, logging, and error handling.
    """
    
    def __init__(self, config: AgentConfig, ollama_host: str = "http://localhost:11434"):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration containing model and behavior settings
            ollama_host: Ollama server host URL
        """
        self.config = config
        self.ollama_host = ollama_host
        self.logger = self._setup_logging()
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize prompt templates
        self.prompt_templates = self._initialize_prompts()
        
        # Initialize output parser
        self.output_parser = StrOutputParser()
        
        # Performance tracking
        self.execution_count = 0
        self.total_processing_time = 0.0
        self.last_execution_time = None
        
        self.logger.info(f"{self.config.name} agent initialized successfully")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup agent-specific logging."""
        logger_name = f"per_agent.{self.config.name.lower().replace(' ', '_')}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not logger.handlers:
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                f'%(asctime)s - {self.config.name} - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_llm(self) -> OllamaLLM:
        """Initialize the Ollama LLM for this agent with fallback support."""
        try:
            # Try primary model first
            llm = OllamaLLM(
                model=self.config.model.model_id,
                base_url=self.ollama_host,
                temperature=self.config.model.temperature,
                num_predict=self.config.model.max_tokens,
                timeout=self.config.timeout
            )
            
            self.logger.info(f"Initialized LLM: {self.config.model.name}")
            return llm
            
        except Exception as e:
            self.logger.warning(f"Primary model failed to initialize: {e}")
            
            # Try to get alternate model
            from ..core.config import Config
            config = Config()
            alternate_model = config.get_alternate_model_for_agent(
                self.config.name.lower().replace(' ', '_')
            )
            
            if alternate_model:
                try:
                    self.logger.info(f"Trying alternate model: {alternate_model.name}")
                    llm = OllamaLLM(
                        model=alternate_model.model_id,
                        base_url=self.ollama_host,
                        temperature=alternate_model.temperature,
                        num_predict=alternate_model.max_tokens,
                        timeout=self.config.timeout
                    )
                    
                    # Update config to reflect the model we're actually using
                    self.config.model = alternate_model
                    self.logger.info(f"Successfully initialized alternate LLM: {alternate_model.name}")
                    return llm
                    
                except Exception as e2:
                    self.logger.error(f"Alternate model also failed: {e2}")
            
            # If all else fails, raise the original error
            self.logger.error(f"Failed to initialize any LLM for {self.config.name}")
            raise e
    
    @abstractmethod
    def _initialize_prompts(self) -> Dict[str, PromptTemplate]:
        """
        Initialize prompt templates specific to this agent.
        Must be implemented by each concrete agent.
        
        Returns:
            Dictionary of prompt templates keyed by purpose
        """
        pass
    
    @abstractmethod
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Main processing method for the agent.
        Must be implemented by each concrete agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary containing agent-specific results
        """
        pass
    
    async def _execute_llm_chain(self, prompt_key: str, **kwargs) -> str:
        """
        Execute an LLM chain with error handling and retries.
        
        Args:
            prompt_key: Key for the prompt template to use
            **kwargs: Variables to inject into the prompt template
            
        Returns:
            LLM response as string
        """
        if prompt_key not in self.prompt_templates:
            raise ValueError(f"Prompt template '{prompt_key}' not found")
        
        prompt_template = self.prompt_templates[prompt_key]
        
        for attempt in range(self.config.max_retries):
            try:
                start_time = datetime.now()
                
                # Create the chain
                chain = prompt_template | self.llm | self.output_parser
                
                # Execute the chain
                result = await chain.ainvoke(kwargs)
                
                # Track performance
                execution_time = (datetime.now() - start_time).total_seconds()
                self.execution_count += 1
                self.total_processing_time += execution_time
                self.last_execution_time = execution_time
                
                self.logger.debug(f"LLM execution completed in {execution_time:.2f}s")
                return result
                
            except Exception as e:
                self.logger.warning(f"LLM execution attempt {attempt + 1} failed: {e}")
                if attempt == self.config.max_retries - 1:
                    self.logger.error(f"All LLM execution attempts failed")
                    raise
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _validate_input(self, state: AgentState) -> bool:
        """
        Validate input state before processing.
        Can be overridden by concrete agents for specific validation.
        
        Args:
            state: Current workflow state
            
        Returns:
            True if input is valid, False otherwise
        """
        if not state or not state.query:
            self.logger.error("Invalid state: missing query")
            return False
        
        if not state.query.question.strip():
            self.logger.error("Invalid state: empty question")
            return False
        
        return True
    
    def _handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Handle errors consistently across agents.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            Error result dictionary
        """
        error_msg = f"{context}: {str(error)}" if context else str(error)
        self.logger.error(error_msg)
        
        return {
            "success": False,
            "error": error_msg,
            "error_type": type(error).__name__,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this agent."""
        avg_time = (self.total_processing_time / self.execution_count 
                   if self.execution_count > 0 else 0.0)
        
        return {
            "agent_name": self.config.name,
            "execution_count": self.execution_count,
            "total_processing_time": self.total_processing_time,
            "average_execution_time": avg_time,
            "last_execution_time": self.last_execution_time,
            "model_used": self.config.model.name
        }
    
    def _create_system_prompt(self, role_description: str, capabilities: List[str]) -> str:
        """
        Create a standardized system prompt for the agent.
        
        Args:
            role_description: Description of the agent's role
            capabilities: List of agent capabilities
            
        Returns:
            Formatted system prompt
        """
        capabilities_str = "\n".join([f"- {cap}" for cap in capabilities])
        
        return f"""You are a {self.config.name}, an AI agent specialized in physics education research.

ROLE: {role_description}

CAPABILITIES:
{capabilities_str}

GUIDELINES:
- Provide accurate, evidence-based responses
- Focus specifically on physics education contexts
- Be thorough but concise in your analysis
- Always cite sources when available
- Identify limitations and uncertainties in your analysis
- Use proper academic language and formatting
- Consider both theoretical and practical educational implications

RESPONSE FORMAT:
- Structure your responses clearly with appropriate sections
- Use bullet points for lists and key findings
- Include confidence levels for uncertain information
- Provide specific, actionable insights when possible

Remember: Your goal is to contribute valuable, accurate insights to physics education research that will help improve teaching and learning outcomes."""
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the agent.
        
        Returns:
            Health status information
        """
        try:
            # Test LLM connectivity
            test_prompt = PromptTemplate.from_template("Respond with 'OK' if you can read this.")
            chain = test_prompt | self.llm | self.output_parser
            response = await chain.ainvoke({})
            
            is_healthy = "ok" in response.lower()
            
            return {
                "agent_name": self.config.name,
                "status": "healthy" if is_healthy else "unhealthy",
                "llm_model": self.config.model.name,
                "llm_response": response.strip(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "agent_name": self.config.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }