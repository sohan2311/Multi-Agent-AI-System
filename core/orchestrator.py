"""
Orchestrator - Coordinates all agents and manages the execution flow
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.planner_agent import PlannerAgent
from agents.spacex_agent import SpaceXAgent
from agents.weather_agent import WeatherAgent
from agents.news_agent import NewsAgent
from agents.market_agent import MarketAgent
from utils.logger import setup_logger

class Orchestrator:
    """Main orchestrator that coordinates all agents"""
    
    def __init__(self):
        self.logger = setup_logger('Orchestrator')
        self.planner = PlannerAgent()
        
        # Initialize all agents
        self.agents = {
            'spacex': SpaceXAgent(),
            'weather': WeatherAgent(),
            'news': NewsAgent(),
            'market': MarketAgent()
        }
        
        self.max_iterations = 3  # Prevent infinite loops
    
    async def process_goal(self, user_goal: str) -> Dict[str, Any]:
        """
        Process a user goal through the multi-agent system
        
        Args:
            user_goal: The goal to achieve
            
        Returns:
            Final result with all agent data
        """
        self.logger.info(f"Processing goal: {user_goal}")
        
        try:
            # Step 1: Plan the execution
            try:
                plan_result = await self.planner.process({'goal': user_goal})
                self.logger.info(f"Planner result: {plan_result}")
            except Exception as e:
                self.logger.error(f"Error in planner: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                # Continue with default plan instead of failing
                plan_result = None
            
            # Handle different planner result formats
            execution_plan = None
            if isinstance(plan_result, dict):
                # Check for the expected success format
                if plan_result.get('success', False) and 'data' in plan_result:
                    execution_plan = plan_result['data']
                # Check for alternative formats
                elif 'agent_sequence' in plan_result:
                    execution_plan = plan_result
                elif plan_result.get('status') == 'completed':
                    # Planner completed but didn't return execution plan - create default
                    execution_plan = self._create_default_plan(user_goal)
                    self.logger.info("Using default execution plan")
                else:
                    error_details = plan_result.get('error', plan_result.get('message', 'Unknown planning error'))
                    self.logger.warning(f"Planning returned incomplete result: {error_details}")
                    execution_plan = self._create_default_plan(user_goal)
            else:
                # Unexpected result format or planner failed - create default plan
                execution_plan = self._create_default_plan(user_goal)
                self.logger.warning("Unexpected planner result format or planner failed, using default plan")
            
            agent_sequence = execution_plan.get('agent_sequence', [])
            
            # Ensure we have a valid agent sequence
            if not agent_sequence:
                agent_sequence = self._infer_agent_sequence(user_goal)
                self.logger.info(f"Inferred agent sequence: {agent_sequence}")
            
            self.logger.info(f"Execution plan created: {agent_sequence}")
            
            # Step 2: Execute the plan
            execution_result = await self._execute_plan(agent_sequence, user_goal)
            
            # Step 3: Check if goal is achieved and iterate if needed
            final_result = await self._check_and_iterate(
                user_goal, execution_result, execution_plan
            )
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error in orchestrator: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_default_plan(self, user_goal: str) -> Dict[str, Any]:
        """Create a default execution plan when planner fails or returns incomplete data"""
        agent_sequence = self._infer_agent_sequence(user_goal)
        return {
            'agent_sequence': agent_sequence,
            'plan_type': 'default',
            'reasoning': 'Default plan created due to planner issues'
        }
    
    def _infer_agent_sequence(self, user_goal: str) -> List[str]:
        """Infer which agents to use based on the goal keywords"""
        goal_lower = user_goal.lower()
        agents_to_use = []
        
        # Check for SpaceX related keywords
        if any(keyword in goal_lower for keyword in ['spacex', 'launch', 'rocket', 'falcon', 'dragon']):
            agents_to_use.append('spacex')
        
        # Check for weather related keywords
        if any(keyword in goal_lower for keyword in ['weather', 'delay', 'conditions', 'wind', 'rain']):
            agents_to_use.append('weather')
        
        # Check for news related keywords
        if any(keyword in goal_lower for keyword in ['news', 'sentiment', 'analysis', 'media']):
            agents_to_use.append('news')
        
        # Check for market related keywords
        if any(keyword in goal_lower for keyword in ['market', 'stock', 'trading', 'investment', 'assets']):
            agents_to_use.append('market')
        
        # If no specific agents identified, use spacex as default
        if not agents_to_use:
            agents_to_use = ['spacex']
        
        return agents_to_use
    
    async def _execute_plan(self, agent_sequence: List[str], user_goal: str) -> Dict[str, Any]:
        """
        Execute the planned sequence of agents
        
        Args:
            agent_sequence: List of agent names to execute in order
            user_goal: Original user goal
            
        Returns:
            Combined result from all agents
        """
        accumulated_data = {
            'goal': user_goal,
            'agents_executed': [],
            'agent_results': {},
            'successful_agents': [],
            'failed_agents': []
        }
        
        for agent_name in agent_sequence:
            if agent_name not in self.agents:
                self.logger.warning(f"Unknown agent: {agent_name}, skipping...")
                continue
            
            self.logger.info(f"Executing agent: {agent_name}")
            
            try:
                # Prepare input data for the agent
                agent_input = {
                    'goal': user_goal,
                    'previous_results': accumulated_data['agent_results'].copy(),
                    'context': accumulated_data
                }
                
                # Execute the agent
                agent = self.agents[agent_name]
                result = await agent.process(agent_input)
                
                # Ensure result is a dictionary
                if not isinstance(result, dict):
                    result = {
                        'success': False,
                        'error': f'Agent {agent_name} returned invalid result format',
                        'raw_result': str(result)
                    }
                
                # Store the result
                accumulated_data['agents_executed'].append(agent_name)
                accumulated_data['agent_results'][agent_name] = result
                
                # Track success/failure
                if result.get('success', False):
                    accumulated_data['successful_agents'].append(agent_name)
                    self.logger.info(f"Agent {agent_name} completed successfully")
                else:
                    accumulated_data['failed_agents'].append(agent_name)
                    error_msg = result.get('error', 'Unknown error')
                    self.logger.warning(f"Agent {agent_name} failed: {error_msg}")
                
            except Exception as e:
                self.logger.error(f"Error executing agent {agent_name}: {str(e)}")
                import traceback
                self.logger.error(traceback.format_exc())
                
                accumulated_data['agents_executed'].append(agent_name)
                accumulated_data['failed_agents'].append(agent_name)
                accumulated_data['agent_results'][agent_name] = {
                    'success': False,
                    'error': str(e),
                    'agent': agent_name
                }
        
        return accumulated_data
    
    async def _check_and_iterate(self, user_goal: str, execution_result: Dict[str, Any], 
                                execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the goal is achieved and iterate if needed
        
        Args:
            user_goal: Original user goal
            execution_result: Result from executing the agent sequence
            execution_plan: Original execution plan
            
        Returns:
            Final result
        """
        # Check if goal is achieved
        goal_achieved = self._assess_goal_achievement(user_goal, execution_result)
        
        if goal_achieved:
            self.logger.info("Goal achieved successfully")
            return self._create_final_result(user_goal, execution_result, True)
        else:
            self.logger.warning("Goal not achieved - all agents failed or insufficient data")
            return self._create_final_result(user_goal, execution_result, False)
    
    def _assess_goal_achievement(self, user_goal: str, execution_result: Dict[str, Any]) -> bool:
        """
        Assess if the goal has been achieved based on successful agent execution
        
        Args:
            user_goal: Original user goal
            execution_result: Result from agent execution
            
        Returns:
            True if goal is achieved, False otherwise
        """
        successful_agents = execution_result.get('successful_agents', [])
        failed_agents = execution_result.get('failed_agents', [])
        total_agents = len(execution_result.get('agents_executed', []))
        
        # Log assessment details
        self.logger.info(f"Goal assessment - Successful: {len(successful_agents)}, Failed: {len(failed_agents)}, Total: {total_agents}")
        
        # Goal is achieved if:
        # 1. At least 50% of agents succeeded, AND
        # 2. At least one agent succeeded
        if total_agents == 0:
            return False
        
        success_rate = len(successful_agents) / total_agents
        has_minimum_success = len(successful_agents) >= 1
        
        # For critical goals requiring specific agents, check if key agents succeeded
        goal_lower = user_goal.lower()
        
        # If goal specifically asks for SpaceX info, SpaceX agent must succeed
        if 'spacex' in goal_lower and 'spacex' not in successful_agents:
            self.logger.info("Goal requires SpaceX data but SpaceX agent failed")
            return False
        
        # If goal specifically asks for market info, market agent must succeed
        if 'market' in goal_lower and 'market' not in successful_agents:
            self.logger.info("Goal requires market data but market agent failed")
            return False
        
        # General success criteria
        goal_achieved = success_rate >= 0.5 and has_minimum_success
        
        self.logger.info(f"Goal achieved: {goal_achieved} (success rate: {success_rate:.2f})")
        return goal_achieved
    
    def _create_final_result(self, user_goal: str, execution_result: Dict[str, Any], 
                           goal_achieved: bool) -> Dict[str, Any]:
        """
        Create the final result summary
        
        Args:
            user_goal: Original user goal
            execution_result: Result from agent execution
            goal_achieved: Whether the goal was achieved
            
        Returns:
            Final formatted result
        """
        agent_results = execution_result.get('agent_results', {})
        successful_agents = execution_result.get('successful_agents', [])
        failed_agents = execution_result.get('failed_agents', [])
        
        # Extract data from successful agents
        final_data = {}
        error_summary = {}
        
        for agent_name, result in agent_results.items():
            if result.get('success', False):
                final_data[agent_name] = result.get('data', {})
            else:
                # Include failed agents with error info
                error_summary[agent_name] = result.get('error', 'Unknown error')
        
        # Create summary
        summary = self._create_summary(user_goal, final_data, error_summary, successful_agents, failed_agents)
        
        return {
            'success': goal_achieved,
            'goal': user_goal,
            'execution_chain': execution_result.get('agents_executed', []),
            'successful_agents': successful_agents,
            'failed_agents': failed_agents,
            'data': final_data,
            'errors': error_summary,
            'final_summary': summary,
            'agent_details': agent_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_summary(self, user_goal: str, final_data: Dict[str, Any], 
                       error_summary: Dict[str, Any], successful_agents: List[str],
                       failed_agents: List[str]) -> str:
        """Create a human-readable summary of the results"""
        summary_parts = []
        
        # Add success/failure overview
        if successful_agents:
            summary_parts.append(f"Successfully executed: {', '.join(successful_agents)}")
        
        if failed_agents:
            summary_parts.append(f"Failed agents: {', '.join(failed_agents)}")
        
        # SpaceX information
        if 'spacex' in final_data:
            spacex_data = final_data['spacex']
            if isinstance(spacex_data, dict):
                if isinstance(spacex_data, list) and len(spacex_data) > 0:
                    launch = spacex_data[0]
                    summary_parts.append(
                        f"Next SpaceX Launch: {launch.get('name', 'Unknown')} "
                        f"on {launch.get('date_utc', 'Unknown date')} "
                        f"using {launch.get('rocket', {}).get('name', 'Unknown rocket')}"
                    )
                elif 'launches' in spacex_data:
                    launches = spacex_data['launches']
                    if launches and len(launches) > 0:
                        launch = launches[0]
                        summary_parts.append(
                            f"Next SpaceX Launch: {launch.get('name', 'Unknown')} "
                            f"on {launch.get('date_utc', 'Unknown date')}"
                        )
                else:
                    summary_parts.append("SpaceX data retrieved successfully")
        elif 'spacex' in error_summary:
            summary_parts.append(f"SpaceX data error: {error_summary['spacex']}")
        
        # Weather information
        if 'weather' in final_data:
            weather_data = final_data['weather']
            if isinstance(weather_data, dict):
                if 'current' in weather_data:
                    weather = weather_data['current']
                    summary_parts.append(
                        f"Weather conditions: {weather.get('description', 'Unknown')} "
                        f"({weather.get('temp', 'N/A')}°C, "
                        f"wind: {weather.get('wind_speed', 'N/A')} m/s)"
                    )
                    
                    # Launch delay assessment
                    if 'launch_delay_risk' in weather_data:
                        risk = weather_data['launch_delay_risk']
                        summary_parts.append(f"Launch delay risk: {risk.get('level', 'Unknown')}")
                else:
                    summary_parts.append("Weather data retrieved successfully")
        elif 'weather' in error_summary:
            summary_parts.append(f"Weather data error: {error_summary['weather']}")
        
        # News information
        if 'news' in final_data:
            news_data = final_data['news']
            if isinstance(news_data, dict):
                if 'sentiment_analysis' in news_data:
                    sentiment = news_data['sentiment_analysis'].get('overall_sentiment', 'Unknown')
                    summary_parts.append(f"News sentiment: {sentiment}")
                else:
                    summary_parts.append("News data retrieved successfully")
        elif 'news' in error_summary:
            summary_parts.append(f"News data error: {error_summary['news']}")
        
        # Market information
        if 'market' in final_data:
            market_data = final_data['market']
            if isinstance(market_data, dict):
                if 'market_sentiment' in market_data:
                    market_sentiment = market_data['market_sentiment']
                    score = market_sentiment.get('overall_score', 0)
                    summary_parts.append(f"Market sentiment score: {score:.2f}")
                else:
                    summary_parts.append("Market data retrieved successfully")
        elif 'market' in error_summary:
            summary_parts.append(f"Market data error: {error_summary['market']}")
        
        if summary_parts:
            return " | ".join(summary_parts)
        else:
            return "All agents failed to retrieve data. Please check network connectivity and API configurations."