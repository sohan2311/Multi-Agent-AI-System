# utils/config.py
import os
from dotenv import load_dotenv
from typing import Optional

class Config:
    """Configuration class for managing environment variables and settings"""
    
    def __init__(self):
        load_dotenv()
        
        # API Keys
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.newsapi_key = os.getenv('NEWSAPI_KEY')
        
        # API URLs
        self.spacex_api_url = "https://api.spacexdata.com/v4"
        self.openweather_api_url = "https://api.openweathermap.org/data/2.5"
        self.newsapi_url = "https://newsapi.org/v2"
        self.coingecko_api_url = "https://api.coingecko.com/api/v3"
        
        # Default settings
        self.default_location = "Cape Canaveral"  # Default SpaceX launch location
        self.default_coordinates = {"lat": 28.5618, "lon": -80.577}
        
        # Logging settings
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        missing_keys = []
        
        if not self.openweather_api_key:
            missing_keys.append('OPENWEATHER_API_KEY')
        
        if not self.newsapi_key:
            missing_keys.append('NEWSAPI_KEY')
        
        if missing_keys:
            print(f"Warning: Missing API keys: {', '.join(missing_keys)}")
            print("Some features may not work properly.")
            return False
        
        return True

# utils/logger.py
import logging
import sys
from typing import Optional

def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Set up a logger with consistent formatting
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
    
    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger

# utils/helpers.py
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json

def parse_iso_datetime(date_string: str) -> Optional[datetime]:
    """
    Parse ISO datetime string to datetime object
    
    Args:
        date_string: ISO formatted datetime string
        
    Returns:
        datetime object or None if parsing fails
    """
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

def format_datetime_for_display(dt: datetime) -> str:
    """
    Format datetime for human-readable display
    
    Args:
        dt: datetime object
        
    Returns:
        Formatted string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary
    
    Args:
        data: Dictionary to get value from
        key: Key to look for
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    return data.get(key, default) if isinstance(data, dict) else default

def calculate_time_until(target_datetime: datetime) -> Dict[str, int]:
    """
    Calculate time until a target datetime
    
    Args:
        target_datetime: Target datetime
        
    Returns:
        Dictionary with days, hours, minutes
    """
    now = datetime.now(timezone.utc)
    if target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)
    
    delta = target_datetime - now
    
    if delta.total_seconds() < 0:
        return {'days': 0, 'hours': 0, 'minutes': 0, 'past': True}
    
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    return {'days': days, 'hours': hours, 'minutes': minutes, 'past': False}

def pretty_print_json(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Pretty print JSON data
    
    Args:
        data: Data to print
        indent: Indentation level
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent, default=str)