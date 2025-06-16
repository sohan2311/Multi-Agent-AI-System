"""
Planner Agent - Responsible for creating and refining execution plans
"""

import re
from typing import Dict, List, Any
from core.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """Agent responsible for planning the execution sequence"""
    
    def __init__(self):
        super().__init__("PlannerAgent")
        
        # Define agent capabilities
        self.agent_capabilities = {
            'spacex': ['launch_data', 'rocket_info', 'mission_details'],
            'weather': ['current_weather', 'forecast', 'conditions'],
            'news': ['latest_news', 'search_news', 'trend_analysis'],
            'analysis': ['data_analysis', 'correlation', 'insights'],
            'summary': ['summarization', 'conclusion', 'report_generation']
        }
    
    async def create_plan(self, goal: str) -> Dict[str, Any]:
        """
        Create an execution plan based on the user goal
        
        Args:
            goal: The user's goal statement
            
        Returns:
            Dict containing the execution plan
        """
        self.logger.info(f"Creating plan for goal: {goal}")
        
        # Analyze goal to determine required agents
        required_agents = self._analyze_goal_requirements(goal)
        
        # Determine optimal sequence
        agent_sequence = self._determine_sequence(required_agents, goal)
        
        # Create plan structure
        plan = {
            'goal': goal,
            'agent_sequence': agent_sequence,
            'dependencies': self._create_dependencies(agent_sequence),
            'expected_flow': self._create_expected_flow(agent_sequence, goal)
        }
        
        self.logger.info(f"Created plan with sequence: {agent_sequence}")
        return plan
    
    def _analyze_goal_requirements(self, goal: str) -> List[str]:
        """Analyze goal to determine which agents are needed"""
        goal_lower = goal.lower()
        required_agents = []
        
        # SpaceX related keywords
        if any(keyword in goal_lower for keyword in ['spacex', 'launch', 'rocket', 'falcon', 'dragon']):
            required_agents.append('spacex')
        
        # Weather related keywords
        if any(keyword in goal_lower for keyword in ['weather', 'forecast', 'temperature', 'conditions', 'delay']):
            required_agents.append('weather')
        
        # News related keywords
        if any(keyword in goal_lower for keyword in ['news', 'latest', 'trend', 'market', 'crypto']):
            required_agents.append('news')
        
        # Analysis keywords
        if any(keyword in goal_lower for keyword in ['analyze', 'analysis', 'correlation', 'trend', 'insight']):
            required_agents.append('analysis')
        
        # Summary keywords (almost always needed)
        if any(keyword in goal_lower for keyword in ['summary', 'summarize', 'report', 'conclude']) or len(required_agents) > 1:
            required_agents.append('summary')
        
        # Ensure we have at least 2 agents for meaningful chaining
        if len(required_agents) < 2:
            if 'spacex' in required_agents:
                required_agents.append('weather')
            required_agents.append('summary')
        
        return required_agents
    
    def _determine_sequence(self, required_agents: List[str], goal: str) -> List[str]:
        """Determine the optimal sequence of agent execution"""
        goal_lower = goal.lower()
        
        # Define logical ordering rules
        sequence = []
        
        # Data gathering agents first
        if 'spacex' in required_agents:
            sequence.append('spacex')
        
        # Enrichment agents
        if 'weather' in required_agents and 'spacex' in sequence:
            sequence.append('weather')
        elif 'weather' in required_agents:
            sequence.insert(0, 'weather')
        
        if 'news' in required_agents:
            sequence.append('news')
        
        # Analysis comes after data gathering
        if 'analysis' in required_agents:
            sequence.append('analysis')
        
        # Summary always comes last
        if 'summary' in required_agents:
            sequence.append('summary')
        
        return sequence
    
    def _create_dependencies(self, agent_sequence: List[str]) -> Dict[str, List[str]]:
        """Create dependency mapping between agents"""
        dependencies = {}
        
        for i, agent in enumerate(agent_sequence):
            if i == 0:
                dependencies[agent] = []
            else:
                dependencies[agent] = [agent_sequence[i-1]]
        
        return dependencies
    
    def _create_expected_flow(self, agent_sequence: List[str], goal: str) -> Dict[str, str]:
        """Create expected data flow description"""
        flow_descriptions = {
            'spacex': 'Fetch SpaceX launch data and mission information',
            'weather': 'Get weather conditions for launch location',
            'news': 'Gather relevant news and trend information',
            'analysis': 'Analyze gathered data for insights and correlations',
            'summary': 'Create comprehensive summary and final report'
        }
        
        expected_flow = {}
        for agent in agent_sequence:
            expected_flow[agent] = flow_descriptions.get(agent, f"Process data through {agent}")
        
        return expected_flow
    
    async def refine_plan(self, original_plan: Dict[str, Any], current_result: Dict[str, Any], goal: str) -> Dict[str, Any]:
        """
        Refine the execution plan based on current results
        
        Args:
            original_plan: The original execution plan
            current_result: Current execution result
            goal: The original goal
            
        Returns:
            Refined execution plan
        """
        self.logger.info("Refining execution plan based on current results")
        
        # Analyze what worked and what didn't
        execution_trace = current_result.get('execution_trace', [])
        failed_agents = [step['agent'] for step in execution_trace if 'error' in step]
        
        # Create refined sequence
        original_sequence = original_plan['agent_sequence']
        refined_sequence = []
        
        # Keep successful agents, modify or replace failed ones
        for agent in original_sequence:
            if agent not in failed_agents:
                refined_sequence.append(agent)
            else:
                # Try alternative approach for failed agents
                if agent == 'spacex':
                    # Maybe try getting data differently
                    refined_sequence.append('spacex')
                elif agent == 'weather':
                    refined_sequence.append('weather')
                else:
                    refined_sequence.append(agent)
        
        # Ensure we still have summary at the end
        if 'summary' not in refined_sequence:
            refined_sequence.append('summary')
        
        # Create refined plan
        refined_plan = {
            'goal': goal,
            'agent_sequence': refined_sequence,
            'dependencies': self._create_dependencies(refined_sequence),
            'expected_flow': self._create_expected_flow(refined_sequence, goal),
            'refinement_reason': f"Refined due to issues with: {failed_agents}"
        }
        
        return refined_plan
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process method for base agent compatibility"""
        # Planner doesn't process data in the traditional sense
        return {
            'agent': self.name,
            'status': 'completed',
            'message': 'Planning completed'
        }