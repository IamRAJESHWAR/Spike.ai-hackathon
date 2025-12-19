# Contributing Guidelines

## Code Standards

### Python Style Guide
- Follow PEP 8 conventions
- Use type hints for function parameters and returns
- Docstrings for all public functions (Google style)
- Maximum line length: 100 characters

### Code Organization
```python
# 1. Standard library imports
import json
from typing import Dict, Any

# 2. Third-party imports
from fastapi import FastAPI
from google.analytics.data_v1beta import BetaAnalyticsDataClient

# 3. Local imports
import config
from llm_utils import llm_client
```

### Function Documentation
```python
def parse_query(query: str, property_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse natural language query into structured format.
    
    Args:
        query: Natural language question from user
        property_id: Optional GA4 property ID
        
    Returns:
        Dictionary with parsed query components
        
    Raises:
        ValueError: If query is empty or invalid
    """
    pass
```

## Error Handling

### Always Handle Exceptions
```python
try:
    response = api_call()
except APIError as e:
    logger.error(f"API error: {e}")
    return {"error": str(e), "success": False}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### Graceful Degradation
- Empty datasets should return friendly messages, not errors
- API failures should explain what went wrong
- Rate limits should trigger exponential backoff, not crashes

## Testing

### Test Coverage Requirements
- All agents must have test cases
- Test both success and failure scenarios
- Test edge cases (empty data, malformed input)

### Running Tests
```bash
python test_api.py
```

## Git Workflow

### Commit Messages
```
feat: Add new content agent
fix: Handle empty GA4 datasets gracefully
docs: Update architecture diagram
refactor: Simplify orchestrator routing logic
```

### Before Committing
```bash
# Check for sensitive data
git diff

# Ensure credentials.json is gitignored
git status

# Run tests
python test_api.py
```

## Adding New Agents

### 1. Create Agent File
```python
# new_agent.py
class NewAgent:
    def __init__(self):
        """Initialize agent with data source."""
        pass
    
    def handle_query(self, query: str) -> str:
        """
        Handle natural language query.
        
        Args:
            query: User's question
            
        Returns:
            Natural language response
        """
        pass
```

### 2. Update Orchestrator
```python
# orchestrator.py
from new_agent import NewAgent

class Orchestrator:
    def __init__(self):
        self.new_agent = NewAgent()
    
    def detect_intent(self, query: str) -> Dict[str, Any]:
        # Add new intent classification logic
        pass
```

### 3. Update Tests
```python
# test_api.py
test_query(
    query="Test query for new agent",
    test_name="New Agent Test"
)
```

## Performance Guidelines

### LLM Usage
- Cache LLM responses when possible
- Use appropriate temperature (0.3 for factual, 0.7 for creative)
- Limit token count to reduce costs

### API Calls
- Batch requests when possible
- Implement exponential backoff for rate limits
- Cache expensive operations

### Database/Sheet Access
- Load data once and reuse when possible
- Use pagination for large datasets
- Index frequently queried fields

## Security

### Never Commit:
- ❌ `credentials.json`
- ❌ API keys in code
- ❌ `.env` files with secrets
- ❌ `server.log` with sensitive data

### Always:
- ✅ Use environment variables for secrets
- ✅ Load credentials at runtime
- ✅ Validate all user input
- ✅ Sanitize data before logging

## Documentation

### Update When:
- Adding new features
- Changing API endpoints
- Modifying configuration
- Fixing bugs that affect usage

### Files to Update:
- `README.md` - User-facing documentation
- `ARCHITECTURE.md` - Technical details
- `ASSUMPTIONS.md` - Limitations and trade-offs
- `PROJECT_STRUCTURE.md` - Code organization
