# Spike AI Backend - Demo Script (5-7 minutes)

## 🚀 Quick Start

**Before Demo:**

```powershell
# Start server (takes ~30 seconds)
$env:Path += ";C:\Program Files\Git\bin"; bash deploy.sh
```

**During Demo:**

```powershell
# Run any query
python terminal_query.py "your query here"
```

---

## 🎯 Demo Objectives

- ✅ Show live data pull from GA4 and Google Sheets
- ✅ Demonstrate agent execution (Analytics, SEO, Multi-Agent)
- ✅ Execute 5+ test cases per tier
- ✅ Highlight key code sections

---

## ⏱️ Timeline Breakdown

**0:00-1:00** - Introduction & Architecture Overview  
**1:00-2:30** - Tier 1: Analytics Agent (5 test cases)  
**2:30-4:00** - Tier 2: SEO Agent (5 test cases)  
**4:00-6:00** - Tier 3: Multi-Agent System (3 test cases)  
**6:00-7:00** - Code Walkthrough & Q&A

---

## 📋 Pre-Demo Checklist

```powershell
# 1. Deploy and start server (one command!)
$env:Path += ";C:\Program Files\Git\bin"; bash deploy.sh

# 2. Wait 5 seconds, then verify server is running
Invoke-RestMethod -Uri "http://localhost:8080/health"

# 3. Open files in VS Code (have these ready in tabs):
# - README.md (show architecture diagram)
# - main.py (show API endpoints)
# - orchestrator.py (show intent classification)
# - analytics_agent.py (show GA4 integration)
# - seo_agent.py (show Google Sheets integration)

# 4. Have terminal ready for running queries with:
#    python terminal_query.py "your query here"
```

---

## 🎬 Demo Script

### **Part 1: Introduction (1 minute)**

**SAY:**

> "Hi! I've built a production-ready AI backend for Spike AI that intelligently routes natural language queries to specialized agents. Let me show you the architecture."

**SHOW:** README.md - Architecture diagram (lines 12-70)

**HIGHLIGHT:**

- Single POST endpoint at `/query`
- Orchestrator with LLM-based intent detection
- Three specialized agents: Analytics (GA4), SEO (Screaming Frog), Multi-Agent

**SAY:**

> "The system uses LiteLLM with Gemini 2.5 Flash for natural language understanding, GA4 Data API for live analytics, and Google Sheets for SEO audit data. Let's see it in action."

---

### **Part 2: Tier 1 - Analytics Agent (1.5 minutes)**

**SAY:**

> "First, let's test the Analytics Agent with live GA4 data. I'll run 5 different analytics queries."

**RUN:** `python test_api.py` (or run queries individually)

**SHOW TERMINAL:** Run these 5 queries:

```powershell
# Test 1: Daily Metrics Breakdown
python terminal_query.py "Give me a daily breakdown of page views, users, and sessions for the /pricing page over the last 14 days"

# Test 2: Traffic Source Analysis
python terminal_query.py "What are the top 5 traffic sources driving users in the last 30 days?"

# Test 3: Trend Analysis
python terminal_query.py "Calculate average daily page views for the homepage over the last 30 days"

# Test 4: Device Breakdown
python terminal_query.py "Show me sessions by device category for the last 7 days"

# Test 5: Geographic Analysis
python terminal_query.py "Which countries have the most users this month?"
```

**WHILE RUNNING, SHOW CODE:** `analytics_agent.py`

**HIGHLIGHT (Line 47-67):**

```python
def __init__(self):
    """Initialize the Analytics Agent with GA4 credentials."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            config.GA4_CREDENTIALS_PATH,
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        self.client = BetaAnalyticsDataClient(credentials=credentials)
```

**SAY:**

> "Notice how it loads credentials from credentials.json at runtime, making it evaluator-safe. The agent uses LLM to parse natural language into GA4 API calls with proper metrics, dimensions, and date ranges."

**HIGHLIGHT (Line 79-150):** `parse_natural_language_query()` function

**SAY:**

> "The LLM translates 'users visited last week' into GA4's 'activeUsers' metric with '7daysAgo' date range. It validates against allowlists to prevent invalid API calls."

---

### **Part 3: Tier 2 - SEO Agent (1.5 minutes)**

**SAY:**

> "Now let's test the SEO Agent with live Google Sheets data from Screaming Frog."

**SHOW TERMINAL:** Run these 5 queries:

```powershell
# Test 1: Conditional Filtering
python terminal_query.py "Which URLs do not use HTTPS and have title tags longer than 60 characters?"

# Test 2: Indexability Overview
python terminal_query.py "Group all pages by indexability status and provide counts"

# Test 3: SEO Health Assessment
python terminal_query.py "Calculate the percentage of indexable pages and assess SEO health"

# Test 4: Meta Description Analysis
python terminal_query.py "Find all pages with missing meta descriptions"

# Test 5: Duplicate Detection
python terminal_query.py "List all pages with duplicate title tags"
```

**WHILE RUNNING, SHOW CODE:** `seo_agent.py`

**HIGHLIGHT (Line 29-51):** `load_data()` function

```python
def load_data(self):
    """Load SEO data from Google Sheets."""
    try:
        spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
        worksheet = spreadsheet.get_worksheet(0)
        records = worksheet.get_all_records()

        if records:
            self.data = pd.DataFrame(records)
            print(f"[OK] Loaded {len(self.data)} SEO records from Google Sheets")
```

**SAY:**

> "The agent loads live data from Google Sheets on every query, so changes to the spreadsheet are immediately reflected. It uses pandas for filtering, grouping, and aggregations."

**HIGHLIGHT (Line 217-280):** `execute_analysis()` function

**SAY:**

> "The LLM determines whether to filter, group, aggregate, or calculate based on the query. For example, 'which pages' triggers filtering, while 'group by' triggers aggregation."

---

### **Part 4: Tier 3 - Multi-Agent System (2 minutes)**

**SAY:**

> "Now the most advanced feature: the multi-agent system that combines analytics and SEO data. Watch how the orchestrator decomposes queries and fuses results."

**SHOW TERMINAL:** Run these 3 queries:

```powershell
# Test 1: Analytics + SEO Fusion
python terminal_query.py "What are the top 10 pages by page views in the last 14 days, and what are their corresponding title tags?"

# Test 2: High Traffic Risk Analysis
python terminal_query.py "Which pages are in the top 20% by views but have missing or duplicate meta descriptions? Explain the SEO risk."

# Test 3: Cross-Agent JSON Output
python terminal_query.py "Return the top 5 pages by views along with their title tags and indexability status in JSON format"
```

**WHILE RUNNING, SHOW CODE:** `orchestrator.py`

**HIGHLIGHT (Line 22-146):** `detect_intent()` function

```python
def detect_intent(self, query: str, property_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Detect user intent and determine which agent(s) to use.

    Keywords: views, visitors, users → ANALYTICS
    Keywords: title, meta, HTTPS, indexability → SEO
    If needs BOTH traffic data AND technical SEO → MULTI_AGENT
    """
```

**SAY:**

> "The orchestrator uses LLM to classify queries into analytics, SEO, or multi-agent based on content, not just whether a property ID is provided."

**HIGHLIGHT (Line 250-380):** `decompose_query()` and `aggregate_results()` functions

**SAY:**

> "For multi-agent queries, it decomposes into sub-queries—one for analytics, one for SEO—executes both in parallel, then uses LLM to aggregate results into a unified insight."

**SHOW OUTPUT:** Point to how the response combines:

- GA4 traffic data (page views, rankings)
- SEO audit data (title tags, meta descriptions, indexability)
- Cross-domain insights (high traffic + SEO issues = priority fixes)

---

### **Part 5: Code Walkthrough (1 minute)**

**SAY:**

> "Let me quickly show the key architectural components."

**SHOW:** `main.py` (Lines 58-80)

```python
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main query endpoint for natural language questions.
    Accepts: {"query": "...", "propertyId": "optional"}
    Returns: {"response": "natural language answer"}
    """
    response = orchestrator.route_query(
        query=request.query,
        property_id=request.propertyId
    )
    return QueryResponse(response=response)
```

**SAY:**

> "Single endpoint. Accepts JSON. Routes through orchestrator. Returns natural language answers."

**SHOW:** `config.py`

```python
GA4_CREDENTIALS_PATH = "credentials.json"
GA4_PROPERTY_ID = "516815205"  # Default, overridden by request
```

**SAY:**

> "Credentials loaded from file—evaluators can replace both credentials.json and propertyId without code changes."

**SHOW:** `deploy.sh` (Lines 1-30)

```bash
#!/bin/bash
python -m venv .venv
. .venv/Scripts/activate
uv pip install -r requirements.txt
python main.py > server.log 2>&1 &
echo $! > server.pid
```

**SAY:**

> "Deployment script creates venv at root, installs dependencies with uv for speed, starts server in background on port 8080. Completes in under 30 seconds."

---

### **Part 6: Wrap-Up (30 seconds)**

**SAY:**

> "To summarize: I've built a production-ready system with intelligent orchestration, live data sources, proper error handling, and extensibility for new agents. All code is on GitHub, fully documented with architecture diagrams, assumptions, and test cases."

**SHOW:** GitHub repository page: https://github.com/IamRAJESHWAR/Spike.ai-hackathon

**HIGHLIGHT:**

- README.md with complete documentation
- ARCHITECTURE.md with technical details
- ASSUMPTIONS.md with limitations
- test_api.py with 15+ test cases

**END WITH:**

> "Happy to answer any questions!"

---

## 🎯 Quick Test Commands (Copy-Paste Ready)

### If Time is Short, Run These:

```powershell
# Tier 1 (30 seconds - show 2 queries)
python terminal_query.py "How many users visited last week?"
python terminal_query.py "Show me top 5 pages by views in the last 14 days"

# Tier 2 (30 seconds - show 2 queries)
python terminal_query.py "Which pages don't use HTTPS?"
python terminal_query.py "Group pages by indexability status"

# Tier 3 (45 seconds - show 1 query)
python terminal_query.py "What are the top 10 pages by views and their title tags?"
```

---

## 🔍 Key Points to Emphasize

### Technical Excellence:

- ✅ LLM-based intent classification (not keyword matching)
- ✅ Live data sources (GA4 API, Google Sheets API)
- ✅ Property-agnostic design (works with any GA4 property)
- ✅ Evaluator-safe (credentials loaded at runtime)
- ✅ Proper error handling (empty datasets, API failures)

### Production Readiness:

- ✅ FastAPI with proper request/response models
- ✅ Exponential backoff for rate limiting
- ✅ Structured logging to server.log
- ✅ Background process management (PID tracking)
- ✅ Fast deployment with uv (<30 seconds)

### System Design:

- ✅ Modular architecture (6 independent modules)
- ✅ Single responsibility (each agent has one job)
- ✅ Extensible (easy to add new agents)
- ✅ Clean separation (API → Orchestrator → Agents → Data Sources)

---

## 💡 If Questions Come Up

**Q: "What if the GA4 property has no data?"**  
A: Show the graceful error message: "I successfully queried Google Analytics, but no data was found..." Explain it handles empty properties without crashing.

**Q: "How do you handle rate limits?"**  
A: Show `llm_utils.py` exponential backoff implementation (lines 25-55).

**Q: "Can it work with a different GA4 property?"**  
A: Show how propertyId is accepted in the request and loaded dynamically—no hardcoding.

**Q: "How extensible is it?"**  
A: Show how to add a new agent: create new file, add to orchestrator's routing logic, update intent classification prompt. Takes ~30 minutes.

**Q: "What's the LiteLLM budget usage?"**  
A: Show config.py with budget remaining (~$99.63 / $100).

---

## 📊 Success Metrics to Mention

- **4,075 lines of code** committed
- **16 files** in clean structure
- **15+ test cases** (5 per tier)
- **3 data sources** (GA4, Google Sheets, LiteLLM)
- **<30 second deployment** with uv
- **100% hackathon compliance** (all deliverables met)

---

**Good luck with your demo! 🚀**
