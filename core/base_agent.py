"""
Base Agent Class - Abstract base class for all agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from utils.logger import setup_logger

class BaseAgent(ABC):
    """Abstract base class for all agents in the system"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = setup_logger(name)
        self.capabilities = []
        self.dependencies = []
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return enriched output
        
        Args:
            data: Input data dictionary
            
        Returns:
            Processed output dictionary
        """
        pass
    
    def get_capabilities(self) -> list:
        """Return list of agent capabilities"""
        return self.capabilities
    
    def get_dependencies(self) -> list:
        """Return list of agent dependencies"""
        return self.dependencies
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data format
        
        Args:
            data: Input data to validate
            
        Returns:
            Boolean indicating if input is valid
        """
        return isinstance(data, dict)
    
    def create_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Create standardized error response
        
        Args:
            error_message: Error description
            
        Returns:
            Error response dictionary
        """
        return {
            'agent': self.name,
            'status': 'error',
            'error': error_message,
            'data': None
        }
    
    def create_success_response(self, data: Any, message: str = "Processing completed") -> Dict[str, Any]:
        """
        Create standardized success response
        
        Args:
            data: Processed data
            message: Success message
            
        Returns:
            Success response dictionary
        """
        return {
            'agent': self.name,
            'status': 'success',
            'message': message,
            'data': data
        }
    
    def extract_previous_data(self, input_data: Dict[str, Any], agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract data from a previous agent's output
        
        Args:
            input_data: Input data containing previous agent outputs
            agent_name: Name of the agent whose data to extract
            
        Returns:
            Previous agent's data or None if not found
        """
        previous_outputs = input_data.get('previous_outputs', {})
        return previous_outputs.get(agent_name, {}).get('data')
    
    def log_processing_start(self, input_data: Dict[str, Any]):
        """Log the start of processing"""
        self.logger.info(f"{self.name} starting processing")
        self.logger.debug(f"Input keys: {list(input_data.keys())}")
    
    def log_processing_end(self, success: bool, output_size: int = 0):
        """Log the end of processing"""
        status = "successfully" if success else "with errors"
        self.logger.info(f"{self.name} completed processing {status}")
        if success and output_size > 0:
            self.logger.debug(f"Output data size: {output_size} items")