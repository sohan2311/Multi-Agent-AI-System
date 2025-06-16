#!/usr/bin/env python3
"""
Evaluation scripts for testing the multi-agent system
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

from main import MultiAgentSystem
from utils.logger import setup_logger

class SystemEvaluator:
    """Evaluator for testing the multi-agent system"""
    
    def __init__(self):
        self.logger = setup_logger('SystemEvaluator')
        self.system = MultiAgentSystem()
    
    async def run_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive evaluation of the system"""
        self.logger.info("Starting system evaluation")
        
        evaluation_results = {
            'test_cases': [],
            'summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Test cases
        test_cases = [
            {
                'name': 'Basic SpaceX Launch Query',
                'goal': 'Find the next SpaceX launch and check weather conditions',
                'expected_agents': ['spacex', 'weather'],
                'success_criteria': ['spacex_data_present', 'weather_data_present']
            },
            {
                'name': 'Complex Multi-Agent Chain',
                'goal': 'Find the next SpaceX launch, check weather at that location, then summarize if it may be delayed',
                'expected_agents': ['spacex', 'weather', 'news'],
                'success_criteria': ['spacex_data_present', 'weather_data_present', 'delay_assessment']
            },
            {
                'name': 'Market Analysis',
                'goal': 'Get the latest SpaceX launch info and analyze market impact on space-related assets',
                'expected_agents': ['spacex', 'market', 'news'],
                'success_criteria': ['spacex_data_present', 'market_data_present']
            }
        ]
        
        # Run each test case
        for test_case in test_cases:
            result = await self._run_test_case(test_case)
            evaluation_results['test_cases'].append(result)
        
        # Generate summary
        evaluation_results['summary'] = self._generate_summary(evaluation_results['test_cases'])
        
        return evaluation_results
    
    async def _run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case"""
        self.logger.info(f"Running test case: {test_case['name']}")
        
        start_time = time.time()
        
        try:
            # Run the system
            result = await self.system.run(test_case['goal'])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Evaluate the result
            evaluation = self._evaluate_result(result, test_case)
            
            return {
                'name': test_case['name'],
                'goal': test_case['goal'],
                'execution_time': execution_time,
                'system_result': result,
                'evaluation': evaluation,
                'success': evaluation['overall_success']
            }
            
        except Exception as e:
            self.logger.error(f"Error in test case {test_case['name']}: {str(e)}")
            return {
                'name': test_case['name'],
                'goal': test_case['goal'],
                'execution_time': time.time() - start_time,
                'system_result': {'success': False, 'error': str(e)},
                'evaluation': {'overall_success': False, 'error': str(e)},
                'success': False
            }
    
    def _evaluate_result(self, result: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a system result against test criteria"""
        evaluation = {
            'overall_success': False,
            'criteria_met': [],
            'criteria_failed': [],
            'agent_execution_analysis': {},
            'data_quality_analysis': {}
        }
        
        if not result.get('success', False):
            evaluation['criteria_failed'].append('system_execution_failed')
            return evaluation
        
        # Check expected agents executed
        executed_agents = result.get('execution_chain', [])
        expected_agents = test_case.get('expected_agents', [])
        
        for agent in expected_agents:
            if agent in executed_agents:
                evaluation['criteria_met'].append(f'{agent}_executed')
            else:
                evaluation['criteria_failed'].append(f'{agent}_not_executed')
        
        # Check success criteria
        success_criteria = test_case.get('success_criteria', [])
        data = result.get('data', {})
        
        for criterion in success_criteria:
            if self._check_success_criterion(criterion, data):
                evaluation['criteria_met'].append(criterion)
            else:
                evaluation['criteria_failed'].append(criterion)
        
        # Analyze agent execution
        agent_details = result.get('agent_details', {})
        for agent_name, agent_result in agent_details.items():
            evaluation['agent_execution_analysis'][agent_name] = {
                'success': agent_result.get('success', False),
                'has_data': bool(agent_result.get('data')),
                'error': agent_result.get('error')
            }
        
        # Overall success determination
        evaluation['overall_success'] = (
            len(evaluation['criteria_failed']) == 0 and 
            len(evaluation['criteria_met']) > 0
        )
        
        return evaluation
    
    def _check_success_criterion(self, criterion: str, data: Dict[str, Any]) -> bool:
        """Check if a specific success criterion is met"""
        if criterion == 'spacex_data_present':
            return 'spacex' in data and len(data.get('spacex', [])) > 0
        
        elif criterion == 'weather_data_present':
            return 'weather' in data and 'current' in data.get('weather', {})
        
        elif criterion == 'market_data_present':
            return 'market' in data and 'cryptocurrency_data' in data.get('market', {})
        
        elif criterion == 'delay_assessment':
            weather_data = data.get('weather', {})
            return 'launch_delay_risk' in weather_data
        
        elif criterion == 'news_data_present':
            return 'news' in data and 'articles' in data.get('news', {})
        
        return False
    
    def _generate_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate evaluation summary"""
        total_tests = len(test_results)
        successful_tests = sum(1 for test in test_results if test['success'])
        
        avg_execution_time = sum(test['execution_time'] for test in test_results) / total_tests
        
        # Agent success rates
        agent_stats = {}
        for test in test_results:
            agent_analysis = test.get('evaluation', {}).get('agent_execution_analysis', {})
            for agent_name, stats in agent_analysis.items():
                if agent_name not in agent_stats:
                    agent_stats[agent_name] = {'total': 0, 'successful': 0}
                agent_stats[agent_name]['total'] += 1
                if stats.get('success', False):
                    agent_stats[agent_name]['successful'] += 1
        
        # Calculate success rates
        for agent_name in agent_stats:
            total = agent_stats[agent_name]['total']
            successful = agent_stats[agent_name]['successful']
            agent_stats[agent_name]['success_rate'] = successful / total if total > 0 else 0
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': successful_tests / total_tests,
            'average_execution_time': avg_execution_time,
            'agent_statistics': agent_stats,
            'recommendations': self._generate_recommendations(test_results)
        }
    
    def _generate_recommendations(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check for common failure patterns
        failed_tests = [test for test in test_results if not test['success']]
        
        if len(failed_tests) > 0:
            recommendations.append("Some tests failed - review error logs and API connectivity")
        
        # Check agent performance
        agent_failures = {}
        for test in test_results:
            agent_analysis = test.get('evaluation', {}).get('agent_execution_analysis', {})
            for agent_name, stats in agent_analysis.items():
                if not stats.get('success', False):
                    agent_failures[agent_name] = agent_failures.get(agent_name, 0) + 1
        
        for agent_name, failure_count in agent_failures.items():
            if failure_count > 1:
                recommendations.append(f"Agent {agent_name} failed multiple times - check API keys and connectivity")
        
        if not recommendations:
            recommendations.append("All tests passed successfully - system is functioning well")
        
        return recommendations

async def main():
    """Main evaluation entry point"""
    print("🧪 Multi-Agent System Evaluation")
    print("=" * 50)
    
    evaluator = SystemEvaluator()
    
    # Run evaluation
    print("Running evaluation tests...")
    results = await evaluator.run_evaluation()
    
    # Display results
    print("\n📊 EVALUATION RESULTS")
    print("=" * 50)
    
    summary = results['summary']
    print(f"✅ Tests Passed: {summary['successful_tests']}/{summary['total_tests']}")
    print(f"📈 Success Rate: {summary['success_rate']:.1%}")
    print(f"⏱️  Average Execution Time: {summary['average_execution_time']:.2f}s")
    
    print(f"\n🤖 Agent Performance:")
    for agent_name, stats in summary['agent_statistics'].items():
        success_rate = stats['success_rate']
        print(f"  {agent_name}: {stats['successful']}/{stats['total']} ({success_rate:.1%})")
    
    print(f"\n💡 Recommendations:")
    for rec in summary['recommendations']:
        print(f"  • {rec}")
    
    # Detailed results
    print(f"\n📋 Detailed Test Results:")
    for test in results['test_cases']:
        status = "✅ PASS" if test['success'] else "❌ FAIL"
        print(f"  {status} {test['name']} ({test['execution_time']:.2f}s)")
        
        if not test['success']:
            evaluation = test['evaluation']
            if 'error' in evaluation:
                print(f"    Error: {evaluation['error']}")
            else:
                failed_criteria = evaluation.get('criteria_failed', [])
                if failed_criteria:
                    print(f"    Failed criteria: {', '.join(failed_criteria)}")
    
    # Save detailed results
    with open('evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: evaluation_results.json")

if __name__ == "__main__":
    asyncio.run(main())