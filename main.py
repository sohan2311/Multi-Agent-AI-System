#!/usr/bin/env python3
"""
Multi-Agent AI System - Main Application
"""
import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime

from core.orchestrator import Orchestrator
from utils.config import Config
from utils.logger import setup_logger

class MultiAgentSystem:
    """Main application class for the multi-agent system"""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger('MultiAgentSystem')
        self.orchestrator = Orchestrator()
    
    async def run(self, user_goal: str) -> Dict[str, Any]:
        """
        Run the multi-agent system with a user goal
        
        Args:
            user_goal: The goal to achieve
            
        Returns:
            Final result from the agent chain
        """
        self.logger.info(f"Starting multi-agent system with goal: {user_goal}")
        
        try:
            # Process the goal through the orchestrator
            result = await self.orchestrator.process_goal(user_goal)
            
            self.logger.info("Multi-agent system completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in multi-agent system: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def display_result(self, result: Dict[str, Any]):
        """Display the final result in a readable format"""
        print("\n" + "="*80)
        print("MULTI-AGENT SYSTEM RESULT")
        print("="*80)
        
        if not result.get('success', False):
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            return
        
        print(f"✅ Goal achieved successfully!")
        print(f"🕒 Completed at: {result.get('timestamp', 'N/A')}")
        
        # Display agent execution chain
        if 'execution_chain' in result:
            print(f"\n📋 Agent Execution Chain:")
            for i, agent in enumerate(result['execution_chain'], 1):
                print(f"  {i}. {agent}")
        
        # Display final summary
        if 'final_summary' in result:
            print(f"\n📊 Final Summary:")
            print(f"  {result['final_summary']}")
        
        # Display key data points
        if 'data' in result:
            data = result['data']
            print(f"\n🔍 Key Information:")
            
            # SpaceX launch info
            if 'spacex' in data:
                spacex_data = data['spacex']
                if isinstance(spacex_data, list) and len(spacex_data) > 0:
                    launch = spacex_data[0]
                    print(f"  🚀 Next SpaceX Launch: {launch.get('name', 'N/A')}")
                    print(f"     📅 Date: {launch.get('date_utc', 'N/A')}")
                    print(f"     🚀 Rocket: {launch.get('rocket', {}).get('name', 'N/A')}")
            
            # Weather info
            if 'weather' in data:
                weather_data = data['weather']
                if 'current' in weather_data:
                    current = weather_data['current']
                    print(f"  🌤️  Weather: {current.get('description', 'N/A')}")
                    print(f"     🌡️  Temperature: {current.get('temp', 'N/A')}°C")
                    print(f"     💨 Wind: {current.get('wind_speed', 'N/A')} m/s")
            
            # News sentiment
            if 'news' in data and 'sentiment_analysis' in data['news']:
                sentiment = data['news']['sentiment_analysis']
                print(f"  📰 News Sentiment: {sentiment.get('overall_sentiment', 'N/A')}")
            
            # Market data
            if 'market' in data:
                market_data = data['market']
                if 'market_sentiment' in market_data:
                    market_sentiment = market_data['market_sentiment']
                    score = market_sentiment.get('overall_score', 0)
                    print(f"  📈 Market Sentiment: {score:.2f} ({self._sentiment_label(score)})")
        
        print("\n" + "="*80)
    
    def _sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.2:
            return "Positive"
        elif score < -0.2:
            return "Negative"
        else:
            return "Neutral"

async def main():
    """Main entry point"""
    print("🤖 Multi-Agent AI System")
    print("=" * 50)
    
    # Initialize the system
    system = MultiAgentSystem()
    
    # Example goals to test
    example_goals = [
        "Find the next SpaceX launch, check weather at that location, then summarize if it may be delayed",
        "Get the latest SpaceX launch info and analyze market impact on space-related assets",
        "Check upcoming SpaceX launches and provide news sentiment analysis",
    ]
    
    print("\nExample goals:")
    for i, goal in enumerate(example_goals, 1):
        print(f"{i}. {goal}")
    
    # Get user input
    print(f"\nEnter your goal (or press Enter for example 1):")
    user_input = input("> ").strip()
    
    if not user_input:
        user_goal = example_goals[0]
        print(f"Using example goal: {user_goal}")
    else:
        user_goal = user_input
    
    # Run the system
    print(f"\n🚀 Processing goal...")
    result = await system.run(user_goal)
    
    # Display results
    system.display_result(result)

if __name__ == "__main__":
    asyncio.run(main())