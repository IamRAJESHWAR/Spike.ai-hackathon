# Project Structure

```
spike-ai-backend/
│
├── README.md                  # Main documentation (architecture, setup, usage)
├── ARCHITECTURE.md            # Detailed technical architecture
├── ASSUMPTIONS.md             # Assumptions, limitations, open questions
├── requirements.txt           # Python dependencies
├── deploy.sh                  # Deployment script (creates .venv, installs deps, starts server)
├── .gitignore                 # Git ignore rules
│
├── config.py                  # Central configuration (API keys, endpoints)
├── main.py                    # FastAPI application entry point
├── orchestrator.py            # LangGraph-based intent classification and agent routing
├── analytics_agent.py         # Google Analytics 4 (GA4) agent
├── seo_agent.py               # SEO audit agent (Screaming Frog data)
├── llm_utils.py               # LiteLLM client and utilities
│
├── terminal_query.py          # CLI interface for testing
├── test_api.py                # Comprehensive test suite (15+ test cases)
├── query_cli.py               # Alternative CLI (legacy)
├── streamlit_app.py           # Web UI for demos (optional)
│
├── credentials.json           # Google Cloud service account credentials (not in git)
├── server.log                 # Runtime logs (not in git)
├── server.pid                 # Server process ID (not in git)
└── .venv/                     # Virtual environment (not in git)
```

## Module Responsibilities

### Core Application
- **main.py**: FastAPI server, HTTP endpoints, request/response handling
- **orchestrator.py**: LangGraph ReAct workflow with Thought-Action-Observation loop, iterative reasoning until answer is found
- **config.py**: Environment configuration, API keys, constants

### Agents
- **analytics_agent.py**: 
  - GA4 Data API integration
  - Natural language → GA4 query translation
  - Live metrics and dimensions fetching
  
- **seo_agent.py**: 
  - Google Sheets API integration
  - SEO data filtering, grouping, aggregation
  - Technical audit analysis

### Utilities
- **llm_utils.py**: 
  - LiteLLM client wrapper
  - Exponential backoff for rate limiting
  - Chat completion utilities

### Testing & Tools
- **test_api.py**: Automated test suite (Tier 1, 2, 3 tests)
- **terminal_query.py**: Interactive CLI for queries
- **streamlit_app.py**: Web UI with streaming support

### Deployment
- **deploy.sh**: 
  - Environment setup (.venv creation)
  - Dependency installation (using uv for speed)
  - Background server startup
  - PID tracking

## Key Design Principles

### 1. LangGraph State Management
The system uses LangGraph's StateGraph for workflow orchestration:
- **Nodes**: Individual processing steps (classify_intent, analytics_node, seo_node, etc.)
- **Edges**: Transitions between nodes
- **Conditional Edges**: Dynamic routing based on intent classification
- **State**: Typed dictionary passed through all nodes

### 2. Separation of Concerns
Each module has a single, well-defined responsibility.

### 3. Dependency Injection
Agents are initialized once and reused (singleton pattern in orchestrator).

### 4. Error Handling
Every agent and graph node gracefully handles:
- Empty datasets
- API failures
- Invalid queries
- Rate limiting

### 5. Extensibility
Adding new agents requires:
1. Create new agent file (e.g., `content_agent.py`)
2. Add new node to the LangGraph workflow
3. Add routing logic in conditional edges

### 6. Configuration Management
All environment-specific values in `config.py`:
- No hardcoded API keys in code
- Easy to override with environment variables
- Credentials loaded at runtime

## Data Flow

### Single-Agent Query (LangGraph)
```
Client → FastAPI → Orchestrator.route_query() 
       → LangGraph.invoke(initial_state)
       → classify_intent node
       → route_by_intent (conditional)
       → analytics_node OR seo_node
       → format_output node
       → END
       → return final_response
```

### Multi-Agent Query
```
Client → FastAPI → Orchestrator
                    ├─→ Analytics Agent → GA4 API ─┐
                    └─→ SEO Agent → Google Sheets ─┴─→ Aggregation → FastAPI → Client
```

## Production Readiness Features

- ✅ Health check endpoint
- ✅ Structured logging to file
- ✅ Background process management
- ✅ Graceful error messages
- ✅ Rate limit handling with exponential backoff
- ✅ Input validation (Pydantic models)
- ✅ CORS enabled for web clients
- ✅ Property-agnostic design (evaluator-safe)
