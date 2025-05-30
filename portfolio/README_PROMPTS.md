# Prompt Management Architecture

This document describes the modular prompt management system for AI-powered financial analysis.

## Overview

The prompt management system provides a centralized, modular way to manage AI prompts with dynamic data injection capabilities. This architecture ensures:

- **Modularity**: Easy to add, modify, and maintain prompts
- **Reusability**: Prompts can be used across different functions
- **Type Safety**: Structured prompt templates with validation
- **Data Injection**: Dynamic content insertion with formatting
- **Consistency**: Standardized prompt structure and parameters

## Architecture Components

### 1. PromptTemplate Class (`prompts.py`)
```python
@dataclass
class PromptTemplate:
    system_message: str      # System role definition
    user_template: str       # User message template with placeholders
    max_tokens: int = 1000   # Maximum response tokens
    temperature: float = 0.7 # Response creativity level
```

### 2. PromptManager Class (`prompts.py`)
Central registry for all prompt templates:
- `PORTFOLIO_ANALYSIS` - Portfolio analysis and insights
- `RISK_ASSESSMENT` - Risk analysis and management
- `INVESTMENT_RECOMMENDATION` - Investment suggestions

### 3. AIAnalyzer Class (`ai_utils.py`)
Helper class for executing AI analysis with prompts:
```python
analyzer = AIAnalyzer()
result = analyzer.analyze_with_prompt('PORTFOLIO_ANALYSIS', portfolio_summary=data)
```

## Usage Examples

### Basic Usage in Views
```python
from .prompts import get_portfolio_analysis_prompt

# Get formatted prompt with data injection
prompt_config = get_portfolio_analysis_prompt(
    portfolio_data, total_value, asset_count, asset_types
)

# Use with OpenAI API
response = client.chat.completions.create(
    model=os.getenv('OPENAI_MODEL', 'gpt-4o'),
    messages=prompt_config['messages'],
    max_tokens=prompt_config['max_tokens'],
    temperature=prompt_config['temperature']
)
```

### Using AIAnalyzer Utility
```python
from .ai_utils import AIAnalyzer

analyzer = AIAnalyzer()
analysis = analyzer.analyze_with_prompt(
    'PORTFOLIO_ANALYSIS',
    portfolio_summary=formatted_data
)
```

### Adding New Prompts

1. **Define the prompt template** in `PromptManager`:
```python
NEW_ANALYSIS = PromptTemplate(
    system_message="You are a specialist in...",
    user_template="Analyze the following: {data}",
    max_tokens=800,
    temperature=0.6
)
```

2. **Create a helper function** (optional):
```python
def get_new_analysis_prompt(data):
    prompt_template = PromptManager.get_prompt('NEW_ANALYSIS')
    return {
        'messages': prompt_template.get_messages(data=data),
        'max_tokens': prompt_template.max_tokens,
        'temperature': prompt_template.temperature
    }
```

3. **Use in your views**:
```python
prompt_config = get_new_analysis_prompt(your_data)
# Use with OpenAI API...
```

## Benefits

- **Maintainability**: All prompts in one place
- **Consistency**: Standardized prompt structure
- **Flexibility**: Easy data injection and formatting
- **Extensibility**: Simple to add new prompt types
- **Testability**: Prompts can be tested independently
- **Configuration**: Model parameters centrally managed

## File Structure

```
portfolio/
├── prompts.py          # Prompt templates and management
├── ai_utils.py         # AI analysis utilities
├── views.py            # Django views using prompts
└── README_PROMPTS.md   # This documentation
```

## Future Enhancements

- Prompt versioning system
- A/B testing for prompt effectiveness
- Dynamic prompt loading from configuration
- Prompt performance metrics
- Multi-language prompt support
