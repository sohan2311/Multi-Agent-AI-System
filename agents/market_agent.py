"""
Market Agent - Fetches market data and financial information
"""
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from core.base_agent import BaseAgent
from utils.config import Config

class MarketAgent(BaseAgent):
    """Agent for fetching market data and cryptocurrency information"""
    
    def __init__(self):
        super().__init__("MarketAgent")
        self.config = Config()
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.capabilities = [
            'crypto_prices',
            'space_stocks',
            'market_sentiment',
            'economic_indicators'
        ]
        self.dependencies = ['spacex', 'news']  # Can analyze based on space news and events
        
        # Space-related stocks and crypto
        self.space_stocks = ['TSLA', 'BA', 'LMT', 'NOC', 'MAXR']  # Tesla, Boeing, Lockheed, Northrop, Maxar
        self.relevant_cryptos = ['bitcoin', 'ethereum', 'dogecoin', 'cardano', 'solana']
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request to fetch market data
        
        Args:
            data: Input data containing context from previous agents
            
        Returns:
            Market data response
        """
        self.log_processing_start(data)
        
        try:
            # Extract context from previous agents
            context = self._extract_context(data)
            
            # Fetch market data
            market_data = {
                'cryptocurrency_data': await self._fetch_crypto_data(),
                'market_sentiment': await self._analyze_market_sentiment(context),
                'space_industry_analysis': self._analyze_space_industry_impact(context),
                'economic_indicators': await self._fetch_economic_indicators(),
                'context': context,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add market correlation analysis
            market_data['correlation_analysis'] = self._analyze_correlations(market_data, context)
            
            self.log_processing_end(True, len(market_data))
            return self.create_success_response(
                market_data,
                f"Successfully fetched market data for {len(self.relevant_cryptos)} cryptocurrencies"
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching market data: {str(e)}")
            return self.create_error_response(f"Failed to fetch market data: {str(e)}")
    
    def _extract_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context from previous agents"""
        context = {
            'launch_info': None,
            'news_sentiment': None,
            'market_triggers': []
        }
        
        # Extract SpaceX data
        spacex_data = self.extract_previous_data(data, 'spacex')
        if spacex_data and isinstance(spacex_data, list) and len(spacex_data) > 0:
            launch = spacex_data[0]
            context['launch_info'] = {
                'name': launch.get('name', ''),
                'rocket': launch.get('rocket', {}).get('name', ''),
                'date': launch.get('date_utc', ''),
                'success': launch.get('success'),
                'upcoming': launch.get('upcoming', True)
            }
            
            # Add market triggers based on launch info
            if 'starship' in launch.get('name', '').lower():
                context['market_triggers'].append('starship_launch')
            if launch.get('success') is True:
                context['market_triggers'].append('successful_launch')
            elif launch.get('success') is False:
                context['market_triggers'].append('failed_launch')
        
        # Extract News sentiment
        news_data = self.extract_previous_data(data, 'news')
        if news_data and 'sentiment_analysis' in news_data:
            context['news_sentiment'] = news_data['sentiment_analysis']
            
            # Add market triggers based on news sentiment
            if news_data['sentiment_analysis'].get('overall_sentiment') == 'negative':
                context['market_triggers'].append('negative_news')
            elif news_data['sentiment_analysis'].get('overall_sentiment') == 'positive':
                context['market_triggers'].append('positive_news')
        
        return context
    
    async def _fetch_crypto_data(self) -> Dict[str, Any]:
        """Fetch cryptocurrency data from CoinGecko API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch current prices
                price_url = f"{self.coingecko_base_url}/simple/price"
                params = {
                    'ids': ','.join(self.relevant_cryptos),
                    'vs_currencies': 'usd',
                    'include_24hr_change': 'true',
                    'include_market_cap': 'true',
                    'include_24hr_vol': 'true'
                }
                
                async with session.get(price_url, params=params) as response:
                    if response.status == 200:
                        prices = await response.json()
                        
                        # Format the data
                        crypto_data = {}
                        for crypto in self.relevant_cryptos:
                            if crypto in prices:
                                crypto_data[crypto] = {
                                    'price_usd': prices[crypto].get('usd', 0),
                                    'change_24h': prices[crypto].get('usd_24h_change', 0),
                                    'market_cap': prices[crypto].get('usd_market_cap', 0),
                                    'volume_24h': prices[crypto].get('usd_24h_vol', 0)
                                }
                        
                        return crypto_data
                    else:
                        self.logger.warning(f"Failed to fetch crypto data: {response.status}")
                        return {}
                        
        except Exception as e:
            self.logger.error(f"Error fetching crypto data: {str(e)}")
            return {}
    
    async def _analyze_market_sentiment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market sentiment based on context"""
        sentiment = {
            'overall_score': 0.0,  # -1 to 1 scale
            'factors': [],
            'recommendations': []
        }
        
        # Analyze launch impact
        if context.get('launch_info'):
            launch = context['launch_info']
            if launch.get('upcoming'):
                sentiment['factors'].append('Upcoming SpaceX launch - potential positive impact')
                sentiment['overall_score'] += 0.1
                
                if 'starship' in launch.get('name', '').lower():
                    sentiment['factors'].append('Starship launch - high market interest')
                    sentiment['overall_score'] += 0.2
                    
            elif launch.get('success') is True:
                sentiment['factors'].append('Recent successful launch - positive sentiment')
                sentiment['overall_score'] += 0.3
            elif launch.get('success') is False:
                sentiment['factors'].append('Recent failed launch - negative sentiment')
                sentiment['overall_score'] -= 0.2
        
        # Analyze news sentiment
        if context.get('news_sentiment'):
            news_sentiment = context['news_sentiment']
            overall_news = news_sentiment.get('overall_sentiment', 'neutral')
            
            if overall_news == 'positive':
                sentiment['factors'].append('Positive news sentiment detected')
                sentiment['overall_score'] += 0.15
            elif overall_news == 'negative':
                sentiment['factors'].append('Negative news sentiment detected')
                sentiment['overall_score'] -= 0.15
        
        # Generate recommendations
        if sentiment['overall_score'] > 0.2:
            sentiment['recommendations'].append('Strong positive indicators - consider space/tech investments')
        elif sentiment['overall_score'] < -0.2:
            sentiment['recommendations'].append('Negative indicators - exercise caution in space/tech sector')
        else:
            sentiment['recommendations'].append('Mixed signals - monitor developments closely')
        
        # Normalize score
        sentiment['overall_score'] = max(-1.0, min(1.0, sentiment['overall_score']))
        
        return sentiment
    
    def _analyze_space_industry_impact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze potential impact on space industry stocks and crypto"""
        analysis = {
            'affected_assets': [],
            'impact_level': 'neutral',  # low, medium, high
            'time_horizon': 'short',    # short, medium, long
            'details': []
        }
        
        # Check for market triggers
        triggers = context.get('market_triggers', [])
        
        if 'starship_launch' in triggers:
            analysis['affected_assets'].extend(['TSLA', 'dogecoin'])
            analysis['impact_level'] = 'high'
            analysis['details'].append('Starship launches typically affect Tesla stock and Dogecoin')
            
        if 'successful_launch' in triggers:
            analysis['affected_assets'].extend(self.space_stocks[:3])  # Top 3 space stocks
            analysis['impact_level'] = 'medium'
            analysis['details'].append('Successful launches boost confidence in space sector')
            
        if 'failed_launch' in triggers:
            analysis['affected_assets'].extend(self.space_stocks)
            analysis['impact_level'] = 'medium'
            analysis['time_horizon'] = 'short'
            analysis['details'].append('Launch failures may cause temporary dip in space stocks')
            
        if 'positive_news' in triggers:
            analysis['affected_assets'].extend(['bitcoin', 'ethereum'])
            analysis['impact_level'] = 'low'
            analysis['details'].append('Positive space news may have spillover effect on tech assets')
        
        return analysis
    
    async def _fetch_economic_indicators(self) -> Dict[str, Any]:
        """Fetch basic economic indicators (mock implementation)"""
        # In a real implementation, you would fetch from APIs like Alpha Vantage, FRED, etc.
        # For this demo, we'll return mock data
        return {
            'market_volatility': 'moderate',
            'risk_appetite': 'neutral',
            'tech_sector_performance': 'stable',
            'note': 'Economic indicators would be fetched from financial APIs in production'
        }
    
    def _analyze_correlations(self, market_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlations between different market factors"""
        correlations = {
            'space_crypto_correlation': 'moderate',
            'launch_market_correlation': 'high',
            'news_price_correlation': 'low',
            'insights': []
        }
        
        # Analyze based on available data
        crypto_data = market_data.get('cryptocurrency_data', {})
        
        # Check if Dogecoin is moving significantly (Elon/SpaceX correlation)
        if 'dogecoin' in crypto_data:
            doge_change = crypto_data['dogecoin'].get('change_24h', 0)
            if abs(doge_change) > 5:  # Significant movement
                correlations['insights'].append(
                    f"Dogecoin showing {doge_change:.2f}% change - potential SpaceX correlation"
                )
        
        # Check Tesla correlation with space events
        if context.get('launch_info'):
            correlations['insights'].append(
                "Active SpaceX events detected - monitor TSLA for correlated movements"
            )
        
        return correlations
    
    def can_process(self, data: Dict[str, Any]) -> bool:
        """Check if this agent can process the given data"""
        # Market agent can always provide general market data
        # But works best with context from other agents
        return True
    
    def get_required_data(self) -> List[str]:
        """Return list of data types this agent requires"""
        return []  # Can work independently but benefits from context