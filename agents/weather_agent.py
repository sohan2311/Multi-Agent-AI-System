"""
Weather Agent - Fetches weather data and forecasts
"""
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from core.base_agent import BaseAgent
from utils.config import Config

class WeatherAgent(BaseAgent):
    """Agent for fetching weather data and forecasts"""
    
    def __init__(self):
        super().__init__("WeatherAgent")
        self.config = Config()
        # Check if API key is available
        try:
            self.api_key = self.config.openweather_api_key
            if not self.api_key or self.api_key == "your_openweather_api_key_here":
                self.logger.warning("OpenWeather API key not configured properly")
                self.api_key = None
        except AttributeError:
            self.logger.warning("OpenWeather API key not found in config")
            self.api_key = None
            
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.capabilities = [
            'current_weather',
            'weather_forecast',
            'weather_conditions',
            'launch_weather_assessment'
        ]
        self.dependencies = ['spacex']  # Often dependent on location from SpaceX data
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request to fetch weather data
        
        Args:
            data: Input data containing location and previous agent outputs
            
        Returns:
            Weather data response
        """
        self.log_processing_start(data)
        
        try:
            # Check if API key is available
            if not self.api_key:
                return self.create_error_response("OpenWeather API key not configured. Please set OPENWEATHER_API_KEY in your environment variables.")
            
            # Extract location information from previous agents or direct input
            location = self._extract_location(data)
            
            if not location:
                return self.create_error_response("No location information available for weather lookup")
            
            # Fetch current weather and forecast
            current_weather = await self._fetch_current_weather(location)
            forecast = await self._fetch_forecast(location)
            
            # Create weather assessment
            weather_data = {
                'location': location,
                'current_weather': current_weather,
                'forecast': forecast,
                'launch_conditions': self._assess_launch_conditions(current_weather, forecast),
                'timestamp': datetime.now().isoformat()
            }
            
            self.log_processing_end(True, len(weather_data))
            return self.create_success_response(
                weather_data, 
                f"Successfully fetched weather data for {location.get('name', 'location')}"
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching weather data: {str(e)}")
            return self.create_error_response(f"Failed to fetch weather data: {str(e)}")
    
    def _extract_location(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract location information from input data"""
        
        # Check if location is directly provided
        if 'location' in data:
            return data['location']
        
        # Extract from SpaceX agent data - check multiple possible formats
        spacex_data = self.extract_previous_data(data, 'spacex')
        if spacex_data:
            # Handle different SpaceX data formats
            if isinstance(spacex_data, list) and len(spacex_data) > 0:
                launch = spacex_data[0]
            elif isinstance(spacex_data, dict):
                # Check if it's wrapped in a 'data' key
                if 'data' in spacex_data and isinstance(spacex_data['data'], list):
                    if len(spacex_data['data']) > 0:
                        launch = spacex_data['data'][0]
                    else:
                        launch = None
                else:
                    launch = spacex_data
            else:
                launch = None
            
            if launch:
                launch_site = launch.get('launch_site', {})
                
                if launch_site.get('latitude') and launch_site.get('longitude'):
                    return {
                        'name': launch_site.get('name', 'Launch Site'),
                        'latitude': launch_site.get('latitude'),
                        'longitude': launch_site.get('longitude'),
                        'location': launch_site.get('location', 'Unknown')
                    }
        
        # Default locations for common launch sites
        default_locations = {
            'kennedy_space_center': {
                'name': 'Kennedy Space Center',
                'latitude': 28.5721,
                'longitude': -80.648,
                'location': 'Cape Canaveral, FL'
            },
            'vandenberg': {
                'name': 'Vandenberg Space Force Base',
                'latitude': 34.7420,
                'longitude': -120.5724,
                'location': 'California'
            },
            'boca_chica': {
                'name': 'Starbase',
                'latitude': 25.9972,
                'longitude': -97.1560,
                'location': 'Boca Chica, Texas'
            }
        }
        
        # Try to match launch site from spacex data
        if spacex_data:
            try:
                launch = None
                if isinstance(spacex_data, list) and len(spacex_data) > 0:
                    launch = spacex_data[0]
                elif isinstance(spacex_data, dict) and 'data' in spacex_data:
                    if isinstance(spacex_data['data'], list) and len(spacex_data['data']) > 0:
                        launch = spacex_data['data'][0]
                
                if launch:
                    site_name = launch.get('launch_site', {}).get('name', '').lower()
                    for key, location_data in default_locations.items():
                        if key in site_name or location_data['name'].lower() in site_name:
                            return location_data
            except Exception as e:
                self.logger.warning(f"Error parsing SpaceX data for location: {str(e)}")
        
        # Default to Kennedy Space Center
        return default_locations['kennedy_space_center']
    
    async def _fetch_current_weather(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch current weather for given location"""
        url = f"{self.base_url}/weather"
        params = {
            'lat': location['latitude'],
            'lon': location['longitude'],
            'appid': self.api_key,
            'units': 'metric'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'temperature': data['main']['temp'],
                        'feels_like': data['main']['feels_like'],
                        'humidity': data['main']['humidity'],
                        'pressure': data['main']['pressure'],
                        'wind_speed': data['wind']['speed'],
                        'wind_direction': data['wind'].get('deg', 0),
                        'visibility': data.get('visibility', 0) / 1000,  # Convert to km
                        'weather_main': data['weather'][0]['main'],
                        'weather_description': data['weather'][0]['description'],
                        'clouds': data['clouds']['all'],
                        'timestamp': datetime.fromtimestamp(data['dt']).isoformat()
                    }
                elif response.status == 401:
                    raise Exception("Invalid API key. Please check your OpenWeather API key configuration.")
                elif response.status == 404:
                    raise Exception(f"Location not found: {location}")
                else:
                    raise Exception(f"Weather API error: {response.status}")
    
    async def _fetch_forecast(self, location: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch 5-day weather forecast for given location"""
        url = f"{self.base_url}/forecast"
        params = {
            'lat': location['latitude'],
            'lon': location['longitude'],
            'appid': self.api_key,
            'units': 'metric'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    forecast_list = []
                    
                    for item in data['list'][:12]:  # Next 12 entries (3-4 days)
                        forecast_list.append({
                            'datetime': datetime.fromtimestamp(item['dt']).isoformat(),
                            'temperature': item['main']['temp'],
                            'humidity': item['main']['humidity'],
                            'pressure': item['main']['pressure'],
                            'wind_speed': item['wind']['speed'],
                            'wind_direction': item['wind'].get('deg', 0),
                            'weather_main': item['weather'][0]['main'],
                            'weather_description': item['weather'][0]['description'],
                            'clouds': item['clouds']['all'],
                            'precipitation_probability': item.get('pop', 0) * 100
                        })
                    
                    return forecast_list
                elif response.status == 401:
                    raise Exception("Invalid API key. Please check your OpenWeather API key configuration.")
                elif response.status == 404:
                    raise Exception(f"Location not found: {location}")
                else:
                    raise Exception(f"Forecast API error: {response.status}")
    
    def _assess_launch_conditions(self, current: Dict[str, Any], forecast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess weather conditions for rocket launch"""
        
        # Launch weather criteria (simplified)
        criteria = {
            'wind_speed_max': 15,  # m/s
            'precipitation': ['Rain', 'Snow', 'Thunderstorm'],
            'visibility_min': 5,  # km
            'cloud_cover_max': 80,  # %
            'temperature_range': [-10, 45]  # Celsius
        }
        
        current_assessment = {
            'suitable': True,
            'issues': [],
            'score': 100
        }
        
        # Check current conditions
        if current['wind_speed'] > criteria['wind_speed_max']:
            current_assessment['suitable'] = False
            current_assessment['issues'].append(f"High wind speed: {current['wind_speed']} m/s")
            current_assessment['score'] -= 30
        
        if current['weather_main'] in criteria['precipitation']:
            current_assessment['suitable'] = False
            current_assessment['issues'].append(f"Precipitation: {current['weather_description']}")
            current_assessment['score'] -= 40
        
        if current['visibility'] < criteria['visibility_min']:
            current_assessment['suitable'] = False
            current_assessment['issues'].append(f"Low visibility: {current['visibility']} km")
            current_assessment['score'] -= 25
        
        if current['clouds'] > criteria['cloud_cover_max']:
            current_assessment['issues'].append(f"High cloud cover: {current['clouds']}%")
            current_assessment['score'] -= 15
        
        if not (criteria['temperature_range'][0] <= current['temperature'] <= criteria['temperature_range'][1]):
            current_assessment['issues'].append(f"Temperature out of range: {current['temperature']}°C")
            current_assessment['score'] -= 20
        
        # Forecast assessment
        forecast_suitable_hours = 0
        total_forecast_hours = len(forecast)
        
        for item in forecast:
            is_suitable = True
            if item['wind_speed'] > criteria['wind_speed_max']:
                is_suitable = False
            if item['weather_main'] in criteria['precipitation']:
                is_suitable = False
            if item['precipitation_probability'] > 70:
                is_suitable = False
            
            if is_suitable:
                forecast_suitable_hours += 1
        
        forecast_suitability = (forecast_suitable_hours / total_forecast_hours) * 100 if total_forecast_hours > 0 else 0
        
        return {
            'current_conditions': current_assessment,
            'forecast_suitability_percentage': forecast_suitability,
            'recommendation': self._get_launch_recommendation(current_assessment, forecast_suitability),
            'best_launch_windows': self._find_best_launch_windows(forecast),
            'assessment_time': datetime.now().isoformat()
        }
    
    def _get_launch_recommendation(self, current: Dict[str, Any], forecast_percentage: float) -> str:
        """Generate launch recommendation based on weather conditions"""
        if current['suitable'] and forecast_percentage > 70:
            return "GO - Excellent weather conditions for launch"
        elif current['suitable'] and forecast_percentage > 50:
            return "CAUTION - Current conditions good, but weather may deteriorate"
        elif not current['suitable'] and forecast_percentage > 70:
            return "HOLD - Current conditions unfavorable, but improving forecast"
        else:
            return "NO-GO - Poor current and forecast conditions"
    
    def _find_best_launch_windows(self, forecast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find the best launch windows in the forecast"""
        windows = []
        
        for item in forecast:
            score = 100
            issues = []
            
            if item['wind_speed'] > 15:
                score -= 30
                issues.append("High winds")
            if item['weather_main'] in ['Rain', 'Snow', 'Thunderstorm']:
                score -= 40
                issues.append("Precipitation")
            if item['precipitation_probability'] > 50:
                score -= 20
                issues.append("High precipitation probability")
            if item['clouds'] > 80:
                score -= 15
                issues.append("Heavy cloud cover")
            
            windows.append({
                'datetime': item['datetime'],
                'score': max(score, 0),
                'suitable': score > 60,
                'issues': issues,
                'conditions_summary': f"{item['weather_description']}, {item['temperature']}°C, {item['wind_speed']} m/s wind"
            })
        
        # Sort by score (best first)
        windows.sort(key=lambda x: x['score'], reverse=True)
        return windows[:5]  # Return top 5 windows