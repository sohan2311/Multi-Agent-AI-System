"""
SpaceX Agent - Fetches SpaceX launch data and mission information
"""

import aiohttp
import ssl
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.base_agent import BaseAgent

class SpaceXAgent(BaseAgent):
    """Agent for fetching SpaceX launch and mission data"""
    
    def __init__(self):
        super().__init__("SpaceXAgent")
        self.base_url = "https://api.spacexdata.com/v4"
        self.capabilities = [
            'launch_data',
            'rocket_info',
            'mission_details',
            'launch_sites',
            'upcoming_launches'
        ]
        
        # Create SSL context that handles certificate issues
        self.ssl_context = ssl.create_default_context()
        # For development only - remove in production
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request to fetch SpaceX data
        
        Args:
            data: Input data containing request parameters
            
        Returns:
            SpaceX data response
        """
        self.log_processing_start(data)
        
        try:
            # Determine what SpaceX data to fetch based on goal or previous data
            goal = data.get('goal', '').lower()
            request_type = self._determine_request_type(goal, data)
            
            if request_type == 'upcoming_launches':
                result = await self._fetch_upcoming_launches()
            elif request_type == 'recent_launches':
                result = await self._fetch_recent_launches()
            elif request_type == 'specific_launch':
                launch_id = data.get('launch_id')
                result = await self._fetch_launch_details(launch_id)
            else:
                # Default to upcoming launches
                result = await self._fetch_upcoming_launches()
            
            # Enrich the data with additional details
            enriched_data = await self._enrich_launch_data(result)
            
            self.log_processing_end(True, len(enriched_data))
            return self.create_success_response(
                enriched_data, 
                f"Successfully fetched SpaceX {request_type} data"
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching SpaceX data: {str(e)}")
            return self.create_error_response(f"Failed to fetch SpaceX data: {str(e)}")
    
    def _determine_request_type(self, goal: str, data: Dict[str, Any]) -> str:
        """Determine what type of SpaceX data to fetch"""
        if 'upcoming' in goal or 'next' in goal or 'future' in goal:
            return 'upcoming_launches'
        elif 'recent' in goal or 'latest' in goal or 'past' in goal:
            return 'recent_launches'
        elif 'launch_id' in data:
            return 'specific_launch'
        else:
            return 'upcoming_launches'
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with SSL context"""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        return aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def _fetch_upcoming_launches(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch upcoming SpaceX launches"""
        try:
            session = await self._create_session()
            try:
                # Fetch upcoming launches
                async with session.get(f"{self.base_url}/launches/upcoming") as response:
                    if response.status == 200:
                        launches = await response.json()
                        return launches[:limit]
                    else:
                        raise Exception(f"API request failed with status {response.status}")
            finally:
                await session.close()
        except Exception as e:
            self.logger.error(f"Error fetching upcoming launches: {str(e)}")
            raise
    
    async def _fetch_recent_launches(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch recent SpaceX launches"""
        try:
            session = await self._create_session()
            try:
                # Fetch past launches
                async with session.get(f"{self.base_url}/launches/past") as response:
                    if response.status == 200:
                        launches = await response.json()
                        # Return the most recent launches
                        return sorted(launches, key=lambda x: x.get('date_utc', ''), reverse=True)[:limit]
                    else:
                        raise Exception(f"API request failed with status {response.status}")
            finally:
                await session.close()
        except Exception as e:
            self.logger.error(f"Error fetching recent launches: {str(e)}")
            raise
    
    async def _fetch_launch_details(self, launch_id: str) -> List[Dict[str, Any]]:
        """Fetch specific launch details"""
        try:
            session = await self._create_session()
            try:
                async with session.get(f"{self.base_url}/launches/{launch_id}") as response:
                    if response.status == 200:
                        launch = await response.json()
                        return [launch]
                    else:
                        raise Exception(f"Launch not found: {launch_id}")
            finally:
                await session.close()
        except Exception as e:
            self.logger.error(f"Error fetching launch details: {str(e)}")
            raise
    
    async def _enrich_launch_data(self, launches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich launch data with additional information"""
        enriched_launches = []
        
        for launch in launches:
            try:
                enriched_launch = launch.copy()
                
                # Add formatted date information
                if launch.get('date_utc'):
                    utc_date = datetime.fromisoformat(launch['date_utc'].replace('Z', '+00:00'))
                    enriched_launch['formatted_date'] = utc_date.strftime('%Y-%m-%d %H:%M:%S UTC')
                    enriched_launch['days_from_now'] = (utc_date - datetime.now(timezone.utc)).days
                
                # Extract launch site information
                launchpad_id = launch.get('launchpad')
                if launchpad_id:
                    launchpad_info = await self._fetch_launchpad_info(launchpad_id)
                    enriched_launch['launch_site'] = launchpad_info
                
                # Extract rocket information
                rocket_id = launch.get('rocket')
                if rocket_id:
                    rocket_info = await self._fetch_rocket_info(rocket_id)
                    enriched_launch['rocket_details'] = rocket_info
                
                # Add mission success information
                enriched_launch['mission_success'] = launch.get('success', None)
                enriched_launch['mission_name'] = launch.get('name', 'Unknown Mission')
                
                enriched_launches.append(enriched_launch)
                
            except Exception as e:
                self.logger.warning(f"Error enriching launch data: {str(e)}")
                enriched_launches.append(launch)
        
        return enriched_launches
    
    async def _fetch_launchpad_info(self, launchpad_id: str) -> Dict[str, Any]:
        """Fetch launchpad information"""
        try:
            session = await self._create_session()
            try:
                async with session.get(f"{self.base_url}/launchpads/{launchpad_id}") as response:
                    if response.status == 200:
                        launchpad = await response.json()
                        return {
                            'name': launchpad.get('full_name', 'Unknown'),
                            'location': launchpad.get('locality', 'Unknown'),
                            'region': launchpad.get('region', 'Unknown'),
                            'latitude': launchpad.get('latitude'),
                            'longitude': launchpad.get('longitude'),
                            'timezone': launchpad.get('timezone', 'UTC')
                        }
            finally:
                await session.close()
        except Exception as e:
            self.logger.warning(f"Error fetching launchpad info: {str(e)}")
            return {'name': 'Unknown', 'location': 'Unknown'}
    
    async def _fetch_rocket_info(self, rocket_id: str) -> Dict[str, Any]:
        """Fetch rocket information"""
        try:
            session = await self._create_session()
            try:
                async with session.get(f"{self.base_url}/rockets/{rocket_id}") as response:
                    if response.status == 200:
                        rocket = await response.json()
                        return {
                            'name': rocket.get('name', 'Unknown'),
                            'type': rocket.get('type', 'Unknown'),
                            'description': rocket.get('description', 'No description available'),
                            'height': rocket.get('height', {}).get('meters', 0),
                            'mass': rocket.get('mass', {}).get('kg', 0),
                            'stages': rocket.get('stages', 0)
                        }
            finally:
                await session.close()
        except Exception as e:
            self.logger.warning(f"Error fetching rocket info: {str(e)}")
            return {'name': 'Unknown', 'type': 'Unknown'}
    
    def get_next_launch_location(self, launches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract location information for the next launch"""
        if not launches:
            return None
        
        next_launch = launches[0]
        launch_site = next_launch.get('launch_site', {})
        
        return {
            'name': launch_site.get('name', 'Unknown'),
            'location': launch_site.get('location', 'Unknown'),
            'latitude': launch_site.get('latitude'),
            'longitude': launch_site.get('longitude'),
            'launch_date': next_launch.get('formatted_date', 'Unknown')
        }