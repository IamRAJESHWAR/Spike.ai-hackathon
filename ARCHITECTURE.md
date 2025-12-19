# Architecture Documentation

## System Design

The Spike AI Backend implements a multi-tier architecture with intelligent routing, specialized agents, and robust error handling.

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

### 2. Orchestrator Layer (orchestrator.py)

The orchestrator is the brain of the system, implementing a three-tier routing strategy:

#### Tier 1: Intent Classification

**Method:** LLM-based analysis  
**Model:** gemini-2.5-flash via LiteLLM

```python
Classification Rules:
1. Analytics: User metrics, sessions, traffic patterns, GA4 data
   Keywords: users, sessions, page views, bounce rate, device, traffic source

2. SEO: Technical issues, accessibility, status codes, crawl data
   Keywords: accessibility, status codes, broken links, WCAG, technical SEO

3. Multi-Agent: Queries requiring both analytics AND SEO data
   Keywords: AND, analyze both, combined, overall performance
```

**Key Feature:** Content-based routing (not property ID presence)

The orchestrator analyzes the **semantic meaning** of the query, not just whether a property ID is provided. This ensures:

- SEO queries route to SEO agent even with property ID present
- Analytics queries require property ID but route based on content
- Multi-agent queries are identified by complex requirements

#### Tier 2: Single-Agent Routing

**Analytics Agent:**

```python
Input: Query + Property ID
Process:
  1. Parse query parameters (metrics, dimensions, date range, filters)
  2. Construct GA4 API request
  3. Execute API call
  4. Generate natural language response
Output: Formatted response with data insights
```

**SEO Agent:**

```python
Input: Query (no property ID needed)
Process:
  1. Parse query to identify target issues
  2. Fetch data from Google Sheets (Screaming Frog export)
  3. Filter/analyze based on query requirements
  4. Generate detailed response with recommendations
Output: Technical analysis with actionable items
```

#### Tier 3: Multi-Agent Orchestration

**Process:**

```python
1. Query Decomposition (LLM):
   - Break complex query into sub-queries
   - Identify dependencies between sub-queries

2. Agent Invocation:
   - Parallel execution when independent
   - Sequential execution when dependent

3. Response Aggregation (LLM):
   - Combine agent responses
   - Synthesize unified answer
   - Maintain context and coherence
```

**Example Multi-Agent Flow:**

```
Query: "Analyze my website traffic AND technical SEO issues"

Decomposition:
  Sub-query 1: "What are the traffic patterns?" → Analytics Agent
  Sub-query 2: "What are the technical SEO issues?" → SEO Agent

Execution:
  [Parallel] Analytics Agent → GA4 data
  [Parallel] SEO Agent → Sheets data

Aggregation:
  LLM synthesizes both responses into unified analysis
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
