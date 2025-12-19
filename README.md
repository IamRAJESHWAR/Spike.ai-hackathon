# Spike AI Backend - Multi-Agent Analytics & SEO System

## Overview

A production-ready AI backend system that intelligently routes natural language queries to specialized agents for Google Analytics 4 (GA4) data analysis and technical SEO audits. Built with FastAPI, LiteLLM, and intelligent orchestration.

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT                                   │
│                    (HTTP POST /query)                           │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI SERVER                              │
│                    (main.py, port 8080)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         POST /query: {propertyId, query}                 │  │
│  │         GET /health: {status: "ok"}                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                                  │
│                  (orchestrator.py)                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  TIER 1: Intent Classification (LLM)                     │  │
│  │  ├─ Analytics: traffic, users, sessions                  │  │
│  │  ├─ SEO: technical issues, accessibility, status codes   │  │
│  │  └─ Multi-Agent: combined analytics + SEO queries        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  TIER 2: Agent Routing                                   │  │
│  │  └─ Routes query to appropriate specialized agent(s)     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  TIER 3: Multi-Agent Orchestration                       │  │
│  │  ├─ Query decomposition (LLM)                            │  │
│  │  ├─ Parallel/sequential agent invocation                 │  │
│  │  └─ Response aggregation (LLM)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────┬─────────────────────────────┬───────────────────────┘
            │                             │
            ▼                             ▼
┌───────────────────────────┐  ┌──────────────────────────────┐
│    ANALYTICS AGENT        │  │       SEO AGENT              │
│  (analytics_agent.py)     │  │    (seo_agent.py)            │
├───────────────────────────┤  ├──────────────────────────────┤
│ • Query Parsing (LLM)     │  │ • Query Parsing (LLM)        │
│ • GA4 API Integration     │  │ • Google Sheets Integration  │
│ • Data Retrieval          │  │ • Data Filtering/Analysis    │
│ • Response Generation     │  │ • Response Generation (LLM)  │
│   (LLM)                   │  │                              │
└───────────┬───────────────┘  └──────────────┬───────────────┘
            │                                 │
            ▼                                 ▼
┌───────────────────────────┐  ┌──────────────────────────────┐
│   GOOGLE ANALYTICS 4      │  │     GOOGLE SHEETS            │
│   Data API v1beta         │  │   (Screaming Frog Export)    │
│   • Metrics & Dimensions  │  │   • Technical SEO Data       │
│   • Date Ranges           │  │   • Accessibility Violations │
│   • Filters & Sorting     │  │   • HTTP Status Codes        │
└───────────────────────────┘  └──────────────────────────────┘
```

## Quick Start

### 1. Prerequisites

- Python 3.8+ (tested on 3.13.2)
- Git Bash (Windows) or Bash shell (Linux/Mac)
- Google Cloud service account credentials

### 2. Deploy

```bash
# Place your credentials at project root
cp your-service-account.json credentials.json

# Run deployment script
bash deploy.sh
```

**Deployment completes in ~30 seconds with uv** ⏱️

**For Windows users:** Run in Git Bash (not PowerShell)

### 3. Test

```bash
# Health check
curl http://localhost:8080/health

# Test query (interactive)
python terminal_query.py

# Test query (single command)
python terminal_query.py "How many users visited last week?"

# Test with curl
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"propertyId":"YOUR_ID","query":"How many users visited?"}'
```

## Setup Instructions

See detailed setup in sections below.

### Configure Data Sources

Edit `config.py`:

```python
GA4_PROPERTY_ID = "YOUR_PROPERTY_ID"
SEO_SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"
```

### Using the Terminal Interface

```bash
# Interactive mode
python terminal_query.py

# Single query
python terminal_query.py "Show me accessibility violations"
```

## Data Source Integrations

### Google Analytics 4 (GA4)

- **API:** Analytics Data API v1beta
- **Auth:** Service account
- **Scope:** `analytics.readonly`
- **Data:** Users, sessions, page views, device data, traffic sources

### Google Sheets (SEO)

- **API:** Sheets API v4
- **Auth:** Service account
- **Scopes:** `spreadsheets.readonly`, `drive.readonly`
- **Data:** Screaming Frog crawl exports (status codes, accessibility violations, WCAG compliance)

### LiteLLM

- **Endpoint:** `http://3.110.18.218`
- **Model:** `gemini-2.5-flash`
- **Rate:** 5 req/min
- **Budget:** $100 ($99.63 remaining)

## Project Structure

```
spike-ai-backend/
├── README.md              # This file
├── ARCHITECTURE.md        # Detailed architecture docs
├── ASSUMPTIONS.md         # Assumptions & limitations
├── deploy.sh              # Deployment script
├── requirements.txt       # Dependencies
├── credentials.json       # Google service account (gitignored)
│
├── main.py                # FastAPI server
├── orchestrator.py        # Multi-agent orchestration
├── analytics_agent.py     # GA4 specialist
├── seo_agent.py          # Technical SEO specialist
├── llm_utils.py          # LLM client
├── config.py             # Configuration
│
├── query_cli.py          # Interactive CLI tool
├── test_api.py           # API test script
├── streamlit_app.py      # Web UI (optional)
│
└── .venv/                # Virtual environment (created by deploy.sh)
```

## API Reference

### POST /query

```json
{
  "propertyId": "516815205", // Optional for SEO queries
  "query": "How many users visited last week?"
}
```

**Response:**

```json
{
  "response": "Natural language response with analysis..."
}
```

### GET /health

```json
{
  "status": "ok"
}
```

## Dependencies

```
fastapi==0.109.0
uvicorn==0.27.0
pydantic>=2.10.5
google-analytics-data==0.18.2
google-auth==2.27.0
gspread==5.12.3
openai>=1.50.0
pandas>=2.2.0
tenacity==8.2.3
requests>=2.31.0
```

## Assumptions and Limitations

### Key Assumptions

1. GA4 property contains data for requested time periods
2. Google Sheets follows Screaming Frog export format
3. Service account has viewer access to all resources
4. LiteLLM API key has sufficient budget

### Known Limitations

1. **Rate Limits:** 5 requests/minute (LiteLLM), 10,000/day (GA4)
2. **Timeout:** 120 seconds for complex multi-agent queries
3. **Property ID:** Required for analytics queries only
4. **Data Freshness:** GA4 data may have 24-48 hour delay

See [ASSUMPTIONS.md](./ASSUMPTIONS.md) for complete details.

## Testing

### Test All Tiers

```bash
# Tier 1: Analytics query
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"propertyId":"516815205","query":"Show sessions by device"}'

# Tier 2: SEO query
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What accessibility violations exist?"}'

# Tier 3: Multi-agent
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"propertyId":"516815205","query":"Analyze traffic AND SEO issues"}'
```

### Run Test Script

```bash
python test_api.py
```

## Troubleshooting

| Issue              | Solution                                                             |
| ------------------ | -------------------------------------------------------------------- |
| Server won't start | Check `server.log`, verify port 8080 is free                         |
| Auth errors        | Verify `credentials.json` exists and service account has permissions |
| Rate limits        | Wait 60 seconds between requests (5 RPM limit)                       |
| No data found      | Check GA4 property ID and data availability                          |
| LLM timeout        | Simplify query or increase timeout in `streamlit_app.py`             |

## Architecture Details

For in-depth architecture documentation, see:

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design and data flows
- [ASSUMPTIONS.md](./ASSUMPTIONS.md) - Assumptions and limitations
- [CLI_USAGE.md](./CLI_USAGE.md) - CLI tool documentation

## Deployment for Evaluation

The project is designed for easy evaluation:

1. **Replace credentials:** `cp evaluator-credentials.json credentials.json`
2. **Deploy:** `bash deploy.sh`
3. **Wait:** ~3-4 minutes
4. **Test:** Server available at `http://localhost:8080`

The deployment script:

- ✅ Creates `.venv` at repository root (required)
- ✅ Installs dependencies via `uv` (fast)
- ✅ Starts server in background on port 8080
- ✅ Saves PID to `server.pid`
- ✅ Completes in <7 minutes

## Contact

**Built for:** Spike AI Builder Hackathon 2025  
**Developer:** rajeshwar8616@gmail.com  
**Repository:** [GitHub Link]

---

**🚀 Ready for production deployment!**
