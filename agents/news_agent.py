"""
News Agent - Fetches relevant news articles and information
"""
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from core.base_agent import BaseAgent
from utils.config import Config

class NewsAgent(BaseAgent):
    """Agent for fetching news articles and space-related information"""
    
    def __init__(self):
        super().__init__("NewsAgent")
        self.config = Config()
        self.api_key = self.config.newsapi_key
        self.base_url = "https://newsapi.org/v2"
        self.capabilities = [
            'space_news',
            'launch_news',
            'weather_news',
            'general_news',
            'sentiment_analysis'
        ]
        self.dependencies = ['spacex', 'weather']  # Can use data from previous agents
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request to fetch relevant news
        
        Args:
            data: Input data containing context from previous agents
            
        Returns:
            News data response
        """
        self.log_processing_start(data)
        
        try:
            # Extract context from previous agents
            context = self._extract_context(data)
            
            # Fetch different types of news based on context
            news_data = {
                'space_news': await self._fetch_space_news(context),
                'launch_specific_news': await self._fetch_launch_specific_news(context),
                'weather_related_news': await self._fetch_weather_news(context),
                'context_summary': context,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add sentiment analysis
            news_data['sentiment_analysis'] = self._analyze_news_sentiment(news_data)
            
            self.log_processing_end(True, len(news_data))
            return self.create_success_response(
                news_data,
                f"Successfully fetched news with {len(news_data.get('space_news', []))} space articles"
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching news: {str(e)}")
            return self.create_error_response(f"Failed to fetch news: {str(e)}")
    
    def _extract_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context from previous agents for targeted news search"""
        context = {
            'launch_info': None,
            'weather_info': None,
            'location': None,
            'search_terms': []
        }
        
        # Extract SpaceX data
        spacex_data = self.extract_previous_data(data, 'spacex')
        if spacex_data and isinstance(spacex_data, list) and len(spacex_data) > 0:
            launch = spacex_data[0]
            context['launch_info'] = {
                'name': launch.get('name', ''),
                'rocket': launch.get('rocket', {}).get('name', ''),
                'date': launch.get('date_utc', ''),
                'mission': launch.get('details', '')
            }
            context['search_terms'].extend([
                launch.get('name', ''),
                launch.get('rocket', {}).get('name', ''),
                'spacex'
            ])
        
        # Extract Weather data
        weather_data = self.extract_previous_data(data, 'weather')
        if weather_data:
            context['weather_info'] = {
                'location': weather_data.get('location', {}),
                'conditions': weather_data.get('current_weather', {}).get('weather_description', ''),
                'launch_assessment': weather_data.get('launch_conditions', {}).get('recommendation', '')
            }
            location_name = weather_data.get('location', {}).get('name', '')
            if location_name:
                context['search_terms'].append(location_name)
        
        return context
    
    async def _fetch_space_news(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch general space and SpaceX related news"""
        search_terms = "SpaceX OR space launch OR rocket launch OR NASA"
        
        url = f"{self.base_url}/everything"
        params = {
            'q': search_terms,
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 10,
            'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        }
        
        return await self._make_news_request(url, params, 'space_news')
    
    async def _fetch_launch_specific_news(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch news specific to the launch from context"""
        if not context.get('launch_info'):
            return []
        
        launch_info = context['launch_info']
        search_query = f"{launch_info.get('name', '')} {launch_info.get('rocket', '')}"
        
        if not search_query.strip():
            return []
        
        url = f"{self.base_url}/everything"
        params = {
            'q': search_query,
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 5,
            'from': (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        }
        
        return await self._make_news_request(url, params, 'launch_specific')
    
    async def _fetch_weather_news(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch weather-related news that might affect launches"""
        if not context.get('weather_info'):
            return []
        
        location = context['weather_info'].get('location', {}).get('name', '')
        search_query = f"weather {location} launch delay"
        
        url = f"{self.base_url}/everything"
        params = {
            'q': search_query,
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 5,
            'from': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        }
        
        return await self._make_news_request(url, params, 'weather_related')
    
    async def _make_news_request(self, url: str, params: Dict[str, Any], news_type: str) -> List[Dict[str, Any]]:
        """Make a request to the news API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = []
                        
                        for article in data.get('articles', []):
                            if article.get('title') and article.get('description'):
                                articles.append({
                                    'title': article['title'],
                                    'description': article['description'],
                                    'url': article['url'],
                                    'source': article['source']['name'],
                                    'published_at': article['publishedAt'],
                                    'relevance_score': self._calculate_relevance_score(article, news_type),
                                    'type': news_type
                                })
                        
                        # Sort by relevance score
                        articles.sort(key=lambda x: x['relevance_score'], reverse=True)
                        return articles
                    else:
                        self.logger.warning(f"News API returned status {response.status}")
                        return []
        except Exception as e:
            self.logger.error(f"Error fetching {news_type} news: {str(e)}")
            return []
    
    def _calculate_relevance_score(self, article: Dict[str, Any], news_type: str) -> float:
        """Calculate relevance score for an article"""
        score = 0.0
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = f"{title} {description}"
        
        # Base scoring for different news types
        type_weights = {
            'space_news': 1.0,
            'launch_specific': 1.5,
            'weather_related': 0.8
        }
        
        base_score = type_weights.get(news_type, 1.0)
        
        # Keyword scoring
        high_value_keywords = ['spacex', 'launch', 'rocket', 'delay', 'weather', 'abort', 'scrub']
        medium_value_keywords = ['nasa', 'space', 'mission', 'falcon', 'dragon', 'starship']
        
        for keyword in high_value_keywords:
            if keyword in content:
                score += 2.0
        
        for keyword in medium_value_keywords:
            if keyword in content:
                score += 1.0
        
        # Recency bonus (more recent articles get higher scores)
        try:
            pub_date = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
            days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
            recency_bonus = max(0, 1 - (days_old / 7))  # Bonus decreases over 7 days
            score += recency_bonus
        except:
            pass
        
        return score * base_score
    
    def _analyze_news_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of news articles"""
        all_articles = []
        for news_type in ['space_news', 'launch_specific_news', 'weather_related_news']:
            all_articles.extend(news_data.get(news_type, []))
        
        if not all_articles:
            return {
                'overall_sentiment': 'neutral',
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'sentiment_score': 0.0
            }
        
        positive_keywords = ['successful', 'achievement', 'breakthrough', 'milestone', 'progress', 'innovation']
        negative_keywords = ['delay', 'abort', 'failure', 'problem', 'issue', 'cancel', 'scrub', 'postpone']
        
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for article in all_articles:
            content = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            pos_score = sum(1 for keyword in positive_keywords if keyword in content)
            neg_score = sum(1 for keyword in negative_keywords if keyword in content)
            
            if pos_score > neg_score:
                sentiment_scores.append(1)
                positive_count += 1
            elif neg_score > pos_score:
                sentiment_scores.append(-1)
                negative_count += 1
            else:
                sentiment_scores.append(0)
                neutral_count += 1
        
        overall_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        if overall_score > 0.2:
            overall_sentiment = 'positive'
        elif overall_score < -0.2:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'overall_sentiment': overall_sentiment,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'sentiment_score': overall_score,
            'key_themes': self._extract_key_themes(all_articles)
        }
    
    def _extract_key_themes(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Extract key themes from articles"""
        themes = {}
        theme_keywords = {
            'delays': ['delay', 'postpone', 'reschedule', 'abort', 'scrub'],
            'weather': ['weather', 'storm', 'wind', 'rain', 'cloud'],
            'technical': ['technical', 'engine', 'system', 'malfunction', 'issue'],
            'success': ['successful', 'achievement', 'milestone', 'breakthrough'],
            'safety': ['safety', 'crew', 'astronaut', 'precaution'],
            'innovation': ['innovation', 'technology', 'advancement', 'development']
        }
        
        for article in articles:
            content = f"{article.get('title', '')} {article.get('description', '')}".lower()
            
            for theme, keywords in theme_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        themes[theme] = themes.get(theme, 0) + 1
                        break
        
        # Return top themes
        sorted_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:5]]