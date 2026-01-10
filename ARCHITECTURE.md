# Architecture Documentation

## System Design

The Spike AI Backend implements a **LangGraph-based multi-agent architecture** using the **ReAct (Thought-Action-Observation)** pattern. The system iteratively reasons about queries, takes actions by calling specialized agents, observes results, and continues until it has enough information to answer comprehensively.

## ReAct (Thought-Action-Observation) Loop

The core of the system is a ReAct loop that allows the AI to:
1. **Think** - Reason about what information is needed
2. **Act** - Call the appropriate tool (analytics, SEO, or final answer)
3. **Observe** - Process the results and decide what to do next
4. **Repeat** - Loop back to Think if more information is needed

```
                ┌──────────────────┐
                │      START       │
                └────────┬─────────┘
                         │
                ┌────────▼─────────┐
        ┌──────►│      THINK       │  "What information do I need?"
        │       │   (LLM Reasoning)│  Plan next action based on context
        │       └────────┬─────────┘
        │                │
        │       ┌────────▼─────────┐
        │       │      ACTION      │  Execute one of:
        │       │   (Call Tool)    │  • analytics_query - GA4 data
        │       │                  │  • seo_query - SEO audit data
        │       │                  │  • final_answer - Synthesize response
        │       └────────┬─────────┘
        │                │
        │       ┌────────▼─────────┐
        │       │     OBSERVE      │  "What did I learn?"
        │       │ (Process Result) │  Store observation for context
        │       └────────┬─────────┘
        │                │
        │       ┌────────▼─────────┐
        │  No   │    COMPLETE?     │  • final_answer called?
        └───────┤                  │  • Max iterations (5) reached?
                └────────┬─────────┘
                         │ Yes
                ┌────────▼─────────┐
                │   FINAL ANSWER   │  Synthesize comprehensive response
                └────────┬─────────┘  from all observations
                         │
                ┌────────▼─────────┐
                │       END        │
                └──────────────────┘
```

### Key Features

- **Iterative Reasoning**: The system doesn't just make one pass - it can gather information from multiple sources
- **Intelligent Tool Selection**: LLM decides which tool to call based on the query and current context
- **Context Accumulation**: Each observation is added to the context for subsequent reasoning
- **Safety Limits**: Maximum 5 iterations prevents infinite loops
- **Graceful Completion**: System synthesizes all gathered information into a coherent final answer

## Core Components

### 1. API Layer (main.py)

**Technology:** FastAPI 0.109.0

**Responsibilities:**

- HTTP endpoint management (`/query`, `/health`)
- Request validation via Pydantic models
- CORS configuration for cross-origin access
- Error handling and logging

**Endpoints:**

```python
POST /query
  Request: QueryRequest(propertyId?: str, query: str)
  Response: QueryResponse(response: str)
  Timeout: 120s

GET /health
  Response: {"status": "ok"}
```

**Configuration:**

- Port: 8080
- CORS: Enabled for all origins
- Logging: INFO level to stdout
- Timeout: 120 seconds for complex queries

### 2. LangGraph ReAct Orchestrator (orchestrator.py)

The orchestrator implements the **ReAct pattern** using LangGraph's StateGraph.

#### State Schema (AgentState)

```python
class AgentState(TypedDict):
    # Input fields
    query: str
    property_id: Optional[str]
    
    # ReAct loop state
    thoughts: List[str]        # Reasoning history
    actions: List[str]         # Actions taken (tool calls)
    observations: List[str]    # Results from tool calls
    
    # Loop control
    iteration: int             # Current iteration (max 5)
    is_complete: bool          # Whether to exit the loop
    
    # Final output
    final_response: Optional[str]
    error: Optional[str]
```

#### Available Tools

The LLM can choose from these tools during the ACTION phase:

1. **analytics_query** - Query Google Analytics 4 for traffic, metrics, user behavior
2. **seo_query** - Query SEO audit data for technical issues, page analysis
3. **final_answer** - Synthesize all observations into a comprehensive response

#### ReAct Prompt Strategy

```
You are an AI assistant with access to tools. Your goal is to answer the user's question.

Current iteration: {iteration}/5

**Observations so far:**
{observations}

**User's question:** {query}

Think step by step:
1. What information do I already have?
2. What additional information do I need?
3. Which tool should I call next?

Respond with a JSON action:
- {"tool": "analytics_query", "input": "your specific analytics question"}
- {"tool": "seo_query", "input": "your specific SEO question"}  
- {"tool": "final_answer", "input": "your comprehensive answer"}
```
    analytics_response: Optional[str]
    seo_response: Optional[str]
    
    # Final output
    final_response: Optional[str]
    
    # Metadata
    error: Optional[str]
    steps_completed: List[str]
```

#### Graph Nodes

| Node | Purpose |
|------|---------|
| `classify_intent` | LLM-based intent classification |
| `analytics_node` | Execute GA4 queries |
| `seo_node` | Execute SEO data queries |
| `decompose_query` | Split multi-agent queries |
| `parallel_agents` | Execute both agents |
| `aggregate_results` | Combine multi-agent responses |
| `format_output` | Format final response |
| `error_node` | Handle errors gracefully |

#### Conditional Routing

```python
workflow.add_conditional_edges(
    "classify_intent",
    self._route_by_intent,
    {
        "analytics": "analytics_node",
        "seo": "seo_node",
        "multi_agent": "decompose_query",
        "error": "error_node"
    }
)
```

#### Intent Classification Rules

```python
Classification Rules:
1. Analytics: User metrics, sessions, traffic patterns, GA4 data
   Keywords: users, sessions, page views, bounce rate, device, traffic source

2. SEO: Technical issues, accessibility, status codes, crawl data
   Keywords: accessibility, status codes, broken links, WCAG, technical SEO

3. Multi-Agent: Queries requiring both analytics AND SEO data
   Keywords: AND, analyze both, combined, overall performance
```

### 3. Agent Layer

#### Analytics Agent (analytics_agent.py)

**Data Source:** Google Analytics 4 Data API v1beta

**Capabilities:**

- Metric analysis: users, sessions, page views, bounce rate, session duration
- Dimension breakdowns: device category, traffic source, page path, country
- Date range queries: last 7/30/90 days, custom ranges
- Advanced filtering: page-specific, device-specific, source-specific
- Sorting and limiting results

**API Integration:**

```python
from google.analytics.data_v1beta import BetaAnalyticsDataClient

client = BetaAnalyticsDataClient(credentials=credentials)

request = RunReportRequest(
    property=f"properties/{property_id}",
    dimensions=[Dimension(name="deviceCategory")],
    metrics=[Metric(name="activeUsers")],
    date_ranges=[DateRange(start_date="7daysAgo", end_date="today")]
)

response = client.run_report(request)
```

**Error Handling:**

- Missing property ID: Return error message
- No data found: Inform user gracefully
- API errors: Log and return meaningful error

#### SEO Agent (seo_agent.py)

**Data Source:** Google Sheets (Screaming Frog export)

**Capabilities:**

- Accessibility analysis: WCAG violations, severity levels
- Status code reports: 200, 404, 301, 500, etc.
- Page-level analysis: Specific URL inspection
- Bulk reports: All pages with specific issues
- Recommendation generation: Actionable SEO fixes

**Data Format:**

```
Columns: Address, Status Code, WCAG Type, Technique, Issue
Example: https://example.com, 200, Error, 1.3.1, Missing alt text
```

**Query Processing:**

```python
# Parse query to identify target
if "accessibility" in query.lower():
    filter_column = "WCAG Type"

if "status" in query.lower():
    filter_column = "Status Code"

# Filter data
filtered_data = df[df[filter_column].notna()]

# Generate response
response = llm_generate(
    system_prompt=SEO_RESPONSE_PROMPT,
    user_prompt=f"Data: {filtered_data}\nQuery: {query}"
)
```

### 4. LLM Integration (llm_utils.py)

**Provider:** LiteLLM  
**Endpoint:** `http://3.110.18.218`  
**Model:** `gemini-2.5-flash`

**Configuration:**

```python
API_KEY = "sk-itE0QuhkM_Gb1fZ1MGl53g"
BASE_URL = "http://3.110.18.218"
MODEL = "gemini-2.5-flash"
TIMEOUT = 30s
```

**Rate Limits:**

- 5 requests per minute
- $100 budget ($99.63 remaining)
- Expires: 2025-12-23

**Retry Strategy:**

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)
)
```

**Token Usage:**

- Intent classification: ~550 tokens
- Query parsing: ~600-800 tokens
- Response generation: ~800-3000 tokens
- Multi-agent: 2x-3x normal usage

### 5. Configuration (config.py)

**Environment Variables:**

```python
GA4_PROPERTY_ID = "516815205"
SEO_SPREADSHEET_ID = "1Z7mLwPG3kj0O5rwF8mN8HNXYzB3QaSYNf0jmRJDWuOk"
CREDENTIALS_FILE = "credentials.json"
```

**Timeouts:**

- LLM calls: 30s
- GA4 API: 30s
- Sheets API: 30s
- Total request: 120s

## Data Flow Diagrams

### Single-Agent Flow (Analytics)

```
User Query: "How many users visited last week?"
    │
    ▼
[Orchestrator: Intent Classification]
    │
    ├─ Analyze query content
    ├─ Detect: "users", "visited" → Analytics intent
    └─ Check property ID present → Route to Analytics Agent
    │
    ▼
[Analytics Agent: Parse Query]
    │
    ├─ Metric: activeUsers
    ├─ Date range: 7daysAgo to today
    └─ No filters
    │
    ▼
[GA4 API Call]
    │
    ├─ Construct RunReportRequest
    ├─ Execute via BetaAnalyticsDataClient
    └─ Receive response with data
    │
    ▼
[Response Generation]
    │
    ├─ Format data: "1,234 users"
    ├─ Add context: "In the last 7 days..."
    └─ Return natural language response
    │
    ▼
User receives: "Your website had 1,234 users in the last 7 days."
```

### Single-Agent Flow (SEO)

```
User Query: "Show accessibility violations"
    │
    ▼
[Orchestrator: Intent Classification]
    │
    ├─ Analyze query content
    ├─ Detect: "accessibility" → SEO intent
    └─ No property ID needed → Route to SEO Agent
    │
    ▼
[SEO Agent: Parse Query]
    │
    ├─ Target: Accessibility data
    ├─ Filter: WCAG violations
    └─ No page filter
    │
    ▼
[Google Sheets API Call]
    │
    ├─ Fetch all data from sheet
    ├─ Filter rows where "WCAG Type" is not null
    └─ Group by severity/type
    │
    ▼
[Response Generation]
    │
    ├─ Count violations by type
    ├─ Generate recommendations
    └─ Format as natural language
    │
    ▼
User receives: "Found 47 accessibility violations: 23 errors, 15 warnings..."
```

### Multi-Agent Flow

```
User Query: "Analyze traffic patterns AND technical SEO issues"
    │
    ▼
[Orchestrator: Intent Classification]
    │
    ├─ Analyze query content
    ├─ Detect: "AND", combined requirements
    └─ Classify as Multi-Agent
    │
    ▼
[Query Decomposition via LLM]
    │
    ├─ Sub-query 1: "What are the traffic patterns?"
    └─ Sub-query 2: "What are the technical SEO issues?"
    │
    ▼
[Parallel Agent Invocation]
    │
    ├─ Analytics Agent (propertyId + sub-query 1)
    │   └─ Fetches GA4 data: users, sessions, devices
    │
    └─ SEO Agent (sub-query 2)
        └─ Fetches Sheets data: status codes, accessibility
    │
    ▼
[Response Aggregation via LLM]
    │
    ├─ Combine both responses
    ├─ Synthesize unified analysis
    ├─ Maintain context and flow
    └─ Generate actionable recommendations
    │
    ▼
User receives: Comprehensive report with traffic analysis + SEO issues
```

## Design Decisions

### 1. Why LLM-Based Routing?

**Traditional Approach:** Rule-based routing with regex/keywords

```python
if property_id and "users" in query:
    route_to_analytics()
elif "accessibility" in query:
    route_to_seo()
```

**Our Approach:** Semantic understanding via LLM

```python
intent = llm_classify(query)  # Understands meaning, not just keywords
route_to_agent(intent)
```

**Advantages:**

- Handles variations: "visitors", "traffic", "people" → all map to users
- Context-aware: "show status codes" (SEO) vs "show session status" (Analytics)
- Resilient: New query patterns work without code changes
- Extensible: Easy to add new intent types

### 2. Why Multi-Agent Orchestration?

**Problem:** Some queries need data from multiple sources

```
"Analyze my site: show traffic AND technical issues"
```

**Solution:** Decompose → Execute → Aggregate

- Breaks complex query into sub-queries
- Invokes specialized agents in parallel
- Synthesizes unified response

**Benefits:**

- Leverages agent specialization
- Avoids monolithic "super agent"
- Scales to N agents

### 3. Why Separate Analytics and SEO Agents?

**Reasoning:**

- **Different data sources:** GA4 API vs Google Sheets
- **Different expertise:** Quantitative metrics vs technical audits
- **Different auth:** Service account with different scopes
- **Clear boundaries:** Analytics = user behavior, SEO = technical health

### 4. Why FastAPI?

**Alternatives:** Flask, Django
**Choice:** FastAPI

**Reasons:**

- Automatic Pydantic validation
- Built-in async support
- OpenAPI documentation
- High performance
- Type safety

### 5. Why Service Account Auth?

**Alternative:** OAuth2 user consent flow

**Choice:** Service account

**Reasons:**

- No user interaction required
- Automated deployment
- Consistent permissions
- Suitable for backend services

## Security Considerations

1. **Credentials:** Never commit `credentials.json` to Git
2. **API Keys:** Store LiteLLM key in environment variables (future improvement)
3. **CORS:** Enable only for trusted origins in production
4. **Rate Limiting:** Implement per-user rate limits (future improvement)
5. **Input Validation:** Pydantic models validate all inputs

## Scalability

**Current Limitations:**

- Single process (no horizontal scaling)
- Synchronous LLM calls
- No caching

**Future Improvements:**

- Deploy with gunicorn + multiple workers
- Implement async LLM calls
- Add Redis cache for frequent queries
- Use message queue for long-running queries

## Performance

**Typical Response Times:**

- Analytics query: 2-4 seconds
- SEO query: 1-3 seconds
- Multi-agent: 5-10 seconds

**Bottlenecks:**

- LLM calls (1-2s each)
- GA4 API (1-2s)
- Sheets API (0.5-1s)

**Optimizations:**

- Parallel agent invocation in multi-agent
- Connection pooling for APIs
- Retry with exponential backoff

## Error Handling

**Strategy:** Graceful degradation

```python
try:
    result = analytics_agent.process(query, property_id)
except MissingPropertyIdError:
    return "Please provide GA4 property ID for analytics queries"
except NoDataFoundError:
    return "No data found for the specified criteria"
except RateLimitError:
    return "Rate limit exceeded, please try again in 60 seconds"
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return "An error occurred. Please try again."
```

## Testing Strategy

**Unit Tests:** (Future improvement)

- Test each agent independently
- Mock GA4/Sheets APIs
- Validate response formats

**Integration Tests:** (Current)

- End-to-end query testing
- All 3 tiers validated
- Health check monitoring

**Load Tests:** (Future improvement)

- Test with 5 RPM limit
- Measure response times under load
- Identify bottlenecks

## Deployment Architecture

**Development:**

```
Local machine → .venv → uvicorn → localhost:8080
```

**Production:** (Future)

```
Cloud VM → Docker → Nginx reverse proxy → Public endpoint
```

## Monitoring and Logging

**Current:**

- Console logging (INFO level)
- Server logs to `server.log`
- Error tracking in try-catch blocks

**Future Improvements:**

- Structured logging (JSON)
- Metrics: response times, error rates
- Alerting: rate limit warnings, API failures
- Distributed tracing

---

**Last Updated:** 2025-01-19  
**Version:** 1.0.0
