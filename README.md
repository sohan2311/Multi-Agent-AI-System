# Multi-Agent AI System

A sophisticated multi-agent system that takes user goals, creates execution plans, and coordinates multiple AI agents to achieve complex objectives. Each agent enriches the output of previous agents, creating a powerful chain of specialized capabilities.

## 🏗️ Project Structure

```
multi-agent-system/
├── main.py                    # Main application entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Your API keys (create this)
├── evaluation.py             # Evaluation and testing scripts
├── README.md                 # This file
│
├── core/                     # Core system components
│   ├── __init__.py
│   ├── base_agent.py         # Base agent class
│   ├── planner_agent.py      # Planning and orchestration logic
│   └── orchestrator.py       # Main coordination logic
│
├── agents/                   # Specialized agents
│   ├── __init__.py
│   ├── spacex_agent.py       # SpaceX launch data
│   ├── weather_agent.py      # Weather information
│   ├── news_agent.py         # News and sentiment analysis
│   └── market_agent.py       # Market and crypto data
│
└── utils/                    # Utility functions
    ├── __init__.py
    ├── config.py             # Configuration management
    ├── logger.py             # Logging setup
    └── helpers.py            # Helper functions
```

## 🚀 Features

- **Intelligent Planning**: AI planner analyzes goals and creates optimal agent execution sequences
- **Agent Chaining**: Each agent builds upon previous agents' outputs for rich, contextual results
- **Multi-API Integration**: Seamlessly integrates SpaceX API, OpenWeatherMap, NewsAPI, and CoinGecko
- **Iterative Refinement**: System can iterate and refine results to better achieve goals
- **Comprehensive Evaluation**: Built-in testing framework to validate agent performance
- **Flexible Architecture**: Easy to add new agents and capabilities

## 🔧 Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Internet connection for API calls

### 2. Installation

```bash
# Clone or download the project
# Navigate to the project directory
cd multi-agent-system

# Install dependencies
pip install -r requirements.txt
```

### 3. API Keys Setup

The system requires API keys for full functionality:

**Required APIs:**
- **OpenWeatherMap**: Get free API key at https://openweathermap.org/api
- **NewsAPI**: Get free API key at https://newsapi.org/

**Optional APIs (work without keys):**
- **SpaceX API**: No key required (public API)
- **CoinGecko**: No key required (public API)

**Setup your environment:**

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your API keys
nano .env  # or use your preferred editor
```

**Example .env file:**
```
OPENWEATHER_API_KEY=your_openweather_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
LOG_LEVEL=INFO
```

### 4. Running the System

**Interactive Mode:**
```bash
python main.py
```

**Evaluation Mode:**
```bash
python evaluation.py
```

## 📋 Usage Examples

### Example Goals You Can Try:

1. **Launch Weather Analysis:**
   ```
   "Find the next SpaceX launch, check weather at that location, then summarize if it may be delayed"
   ```

2. **Market Impact Analysis:**
   ```
   "Get the latest SpaceX launch info and analyze market impact on space-related assets"
   ```

3. **Comprehensive Space Report:**
   ```
   "Check upcoming SpaceX launches and provide news sentiment analysis"
   ```

### Sample Interaction:

```
🤖 Multi-Agent AI System
==================================================

Example goals:
1. Find the next SpaceX launch, check weather at that location, then summarize if it may be delayed
2. Get the latest SpaceX launch info and analyze market impact on space-related assets
3. Check upcoming SpaceX launches and provide news sentiment analysis

Enter your goal (or press Enter for example 1):
> Find the next SpaceX launch and check if weather will cause delays

🚀 Processing goal...

================================================================================
MULTI-AGENT SYSTEM RESULT
================================================================================
✅ Goal achieved successfully!
🕒 Completed at: 2024-06-16T15:30:45.123456

📋 Agent Execution Chain:
  1. spacex
  2. weather
  3. news

🔍 Key Information:
  🚀 Next SpaceX Launch: Starship IFT-4
     📅 Date: 2024-06-20T14:00:00.000Z
     🚀 Rocket: Starship
  🌤️  Weather: Clear sky (22°C, wind: 3.2 m/s)
  📈 Market Sentiment: 0.25 (Positive)

================================================================================
```

## 🧪 Evaluation Framework

The system includes comprehensive evaluation capabilities:

```bash
python evaluation.py
```

**Evaluation Features:**
- **Goal Achievement Testing**: Validates that agents achieve specified objectives
- **Agent Chain Analysis**: Ensures proper data flow between agents
- **Performance Metrics**: Measures execution time and success rates
- **Error Detection**: Identifies and reports system failures
- **Recommendations**: Provides actionable feedback for improvements

**Sample Evaluation Output:**
```
🧪 Multi-Agent System Evaluation
==================================================
Running evaluation tests...

📊 EVALUATION RESULTS
==================================================
✅ Tests Passed: 3/3
📈 Success Rate: 100.0%
⏱️  Average Execution Time: 4.23s

🤖 Agent Performance:
  spacex: 3/3 (100.0%)
  weather: 3/3 (100.0%)
  news: 2/3 (66.7%)
  market: 2/3 (66.7%)

💡 Recommendations:
  • All tests passed successfully - system is functioning well

📄 Detailed results saved to: evaluation_results.json
```

## 🔄 Agent Flow Logic

### 1. Planning Phase
- User provides goal
- PlannerAgent analyzes goal and determines required agents
- Creates optimal execution sequence

### 2. Execution Phase
- Agents execute in planned sequence
- Each agent receives context from previous agents
- Data is enriched and passed along the chain

### 3. Validation Phase
- System evaluates goal achievement
- Can iterate if goal not fully met
- Generates comprehensive final report

### Agent Dependencies:
```
SpaceX Agent → Weather Agent (needs launch location)
SpaceX Agent → News Agent (needs launch context)
News Agent → Market Agent (news sentiment affects market)
Weather Agent → Market Agent (weather affects launch success)
```

## 🔧 Troubleshooting

### Common Issues:

**1. API Key Errors:**
```
Error: Missing API keys: OPENWEATHER_API_KEY, NEWSAPI_KEY
```
- Solution: Add your API keys to the `.env` file

**2. Network Connection Issues:**
```
Error fetching data from [API]
```
- Solution: Check internet connection and API service status

**3. Import Errors:**
```
ModuleNotFoundError: No module named 'aiohttp'
```
- Solution: Run `pip install -r requirements.txt`

### Limited Functionality Mode:
The system can run with limited functionality even without API keys:
- SpaceX data will still work (public API)
- CoinGecko crypto data will still work (public API)
- Weather and News features will be limited

## 🚀 Extending the System

### Adding New Agents:

1. **Create agent file** in `agents/` directory
2. **Inherit from BaseAgent** class
3. **Implement required methods**:
   - `process(data)`: Main processing logic
   - `can_process(data)`: Capability check
   - `get_required_data()`: Dependencies

4. **Register in orchestrator**
5. **Update planner logic** if needed

### Example New Agent Structure:
```python
from core.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyNewAgent")
        self.capabilities = ['my_capability']
        
    async def process(self, data):
        # Your agent logic here
        pass
```

## 📊 Performance Characteristics

- **Average Response Time**: 3-6 seconds per goal
- **Concurrent Agent Support**: Up to 4 agents in parallel
- **API Rate Limiting**: Handled automatically
- **Error Recovery**: Graceful degradation when APIs are unavailable

## 🤝 Contributing

Feel free to extend this system by:
- Adding new agents for different data sources
- Improving the planning algorithm
- Adding more sophisticated goal evaluation
- Implementing caching for better performance

## 📄 License

This project is provided as-is for educational and demonstration purposes.