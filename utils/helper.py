"""
Helper utilities for the multi-agent system.
Contains common functions used across agents and components.
"""

import json
import re
import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse
import hashlib
import time


class DataFormatter:
    """Utility class for formatting data."""
    
    @staticmethod
    def format_datetime(dt: Union[str, datetime]) -> str:
        """Format datetime for display."""
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                return dt
        
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    @staticmethod
    def format_temperature(temp: float, unit: str = "C") -> str:
        """Format temperature with unit."""
        if unit.upper() == "F":
            return f"{temp:.1f}°F"
        else:
            return f"{temp:.1f}°C"
    
    @staticmethod
    def format_wind_speed(speed: float, unit: str = "m/s") -> str:
        """Format wind speed with unit."""
        return f"{speed:.1f} {unit}"
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """Format percentage."""
        return f"{value:.1f}%"
    
    @staticmethod
    def format_currency(amount: float, currency: str = "USD") -> str:
        """Format currency amount."""
        return f"{amount:,.2f} {currency}"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text to specified length."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."


class APIHelper:
    """Helper class for API operations."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get(self, url: str, headers: Dict[str, str] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make GET request."""
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from API")
    
    async def post(self, url: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Make POST request."""
        try:
            async with self.session.post(url, json=data, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON response from API")


class TextProcessor:
    """Utility class for text processing."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML tags (basic)
        text = re.sub(r'<[^>]+>', '', text)
        
        return text
    
    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text (simple implementation)."""
        if not text:
            return []
        
        # Simple keyword extraction - in production, use proper NLP
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'this', 'that', 'these',
            'those', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'must', 'shall'
        }
        
        keywords = [word for word in words if word not in stop_words]
        
        # Count frequency and return top keywords
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, _ in word_counts.most_common(max_keywords)]
    
    @staticmethod
    def generate_summary(text: str, max_sentences: int = 3) -> str:
        """Generate a simple summary of text."""
        if not text:
            return ""
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= max_sentences:
            return text
        
        # Simple scoring based on sentence length and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = len(sentence.split())  # Word count
            if i < len(sentences) * 0.3:  # Early sentences get bonus
                score *= 1.2
            scored_sentences.append((score, sentence))
        
        # Sort by score and take top sentences
        scored_sentences.sort(reverse=True)
        top_sentences = [sentence for _, sentence in scored_sentences[:max_sentences]]
        
        return '. '.join(top_sentences) + '.'


class ValidationHelper:
    """Helper class for data validation."""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email is valid."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_coordinates(lat: float, lon: float) -> bool:
        """Check if coordinates are valid."""
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe filesystem usage."""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip('. ')
        return filename or 'unnamed_file'


class CacheHelper:
    """Simple in-memory cache helper."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
    
    def cache_result(self, ttl: Optional[int] = None):
        """Decorator to cache function results."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                key = self._generate_key(func.__name__, *args, **kwargs)
                result = self.get(key)
                if result is not None:
                    return result
                
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                self.set(key, result, ttl)
                return result
            return wrapper
        return decorator


class PerformanceTracker:
    """Track performance metrics."""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timer(self, name: str) -> None:
        """Start timing an operation."""
        self.metrics[name] = {'start': time.time()}
    
    def end_timer(self, name: str) -> float:
        """End timing and return duration."""
        if name in self.metrics and 'start' in self.metrics[name]:
            duration = time.time() - self.metrics[name]['start']
            self.metrics[name]['duration'] = duration
            return duration
        return 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self.metrics.copy()
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()


# Global instances
global_cache = CacheHelper()
performance_tracker = PerformanceTracker()


# Utility functions
def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value using dot notation."""
    keys = path.split('.')
    current = data
    
    try:
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    except (KeyError, TypeError):
        return default


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def parse_agent_goal(goal: str) -> Dict[str, Any]:
    """Parse natural language goal into structured format."""
    # Simple goal parsing - in production, use proper NLP
    goal_lower = goal.lower()
    
    parsed = {
        'original': goal,
        'keywords': TextProcessor.extract_keywords(goal),
        'requires_spacex': any(word in goal_lower for word in ['spacex', 'launch', 'rocket', 'falcon', 'starship']),
        'requires_weather': any(word in goal_lower for word in ['weather', 'temperature', 'rain', 'wind', 'forecast']),
        'requires_news': any(word in goal_lower for word in ['news', 'article', 'report', 'story', 'headline']),
        'requires_market': any(word in goal_lower for word in ['stock', 'market', 'price', 'trading', 'financial']),
    }
    
    return parsed


if __name__ == "__main__":
    # Test the helpers
    print("Testing DataFormatter...")
    formatter = DataFormatter()
    print(f"DateTime: {formatter.format_datetime(datetime.now())}")
    print(f"Temperature: {formatter.format_temperature(25.6)}")
    print(f"Currency: {formatter.format_currency(1234.56)}")
    
    print("\nTesting TextProcessor...")
    processor = TextProcessor()
    text = "This is a sample text for testing. It has multiple sentences. We want to extract keywords and generate a summary."
    print(f"Keywords: {processor.extract_keywords(text)}")
    print(f"Summary: {processor.generate_summary(text, 2)}")
    
    print("\nTesting ValidationHelper...")
    validator = ValidationHelper()
    print(f"Valid URL: {validator.is_valid_url('https://example.com')}")
    print(f"Valid Email: {validator.is_valid_email('test@example.com')}")
    print(f"Valid Coordinates: {validator.is_valid_coordinates(40.7128, -74.0060)}")
    
    print("\nTesting utility functions...")
    data = {'user': {'name': 'John', 'address': {'city': 'NYC'}}}
    print(f"Safe get: {safe_get(data, 'user.address.city')}")
    print(f"Flattened: {flatten_dict(data)}")
    
    goal = "Find the next SpaceX launch and check the weather"
    print(f"Parsed goal: {parse_agent_goal(goal)}")