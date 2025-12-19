# Assumptions & Limitations

## Core Assumptions

### 1. Data Availability

#### Google Analytics 4

- **Assumption:** The provided GA4 property ID contains data for the requested time periods
- **Impact:** Queries return "No data found" if property is empty or recently created
- **Mitigation:** System gracefully handles empty results with informative messages
- **Validation:** Users should verify property has data before deployment

#### Google Sheets (SEO Data)

- **Assumption:** Screaming Frog crawl data is exported to Google Sheets in expected format
- **Expected Columns:**
  - `Address`: Full URL of crawled page
  - `Status Code`: HTTP response code (200, 404, 301, etc.)
  - `WCAG Type`: Accessibility violation severity (Error, Warning, Notice)
  - `Technique`: WCAG technique number (e.g., 1.3.1, 2.4.4)
  - `Issue`: Description of the accessibility violation
- **Impact:** SEO agent cannot function if sheet structure differs
- **Mitigation:** Sheet ID and format are configurable in `config.py`
- **Validation:** Check sheet structure matches expected format

### 2. Authentication & Permissions

#### Service Account Access

- **Assumption:** The `credentials.json` service account has:
  - `analytics.readonly` scope for GA4 property
  - Viewer access to the GA4 property
  - `spreadsheets.readonly` scope for Google Sheets
  - Viewer access to the SEO spreadsheet
- **Impact:** API calls fail with 403/401 errors if permissions missing
- **Mitigation:** Deploy script validates credentials file exists
- **Validation:** Test authentication before deployment

#### LiteLLM API Key

- **Assumption:** API key `sk-itE0QuhkM_Gb1fZ1MGl53g` is valid and has budget
- **Current Budget:** $99.63 remaining of $100
- **Rate Limit:** 5 requests per minute
- **Expiration:** 2025-12-23 (3.8 days remaining)
- **Impact:** LLM calls fail if key expires or budget exhausted
- **Mitigation:** System retries with exponential backoff
- **Validation:** Monitor budget via `http://3.110.18.218/key/info`

### 3. Network & Infrastructure

#### Port Availability

- **Assumption:** Port 8080 is available on the deployment machine
- **Impact:** Server fails to start if port is in use
- **Mitigation:** Deploy script checks for existing server processes
- **Validation:** Check with `lsof -i :8080` (Linux/Mac) or `Get-NetTCPConnection -LocalPort 8080` (Windows)

#### Internet Connectivity

- **Assumption:** Deployment machine has internet access to:
  - `analyticsdata.googleapis.com` (GA4 API)
  - `sheets.googleapis.com` (Sheets API)
  - `http://3.110.18.218` (LiteLLM endpoint)
- **Impact:** API calls timeout without connectivity
- **Mitigation:** 30-second timeouts with retry logic
- **Validation:** Test connectivity to all endpoints

### 4. Python Environment

#### Python Version

- **Assumption:** Python 3.8+ is installed (tested on 3.13.2)
- **Impact:** Dependency installation fails on older versions
- **Mitigation:** Deploy script checks Python version
- **Validation:** Run `python --version` to verify

#### Virtual Environment

- **Assumption:** `.venv` can be created at repository root
- **Impact:** Dependencies install globally if venv creation fails
- **Mitigation:** Deploy script creates venv before installing packages
- **Validation:** Check `.venv/` exists after deployment

#### UV Package Manager

- **Assumption:** `uv` can be installed via pip if not present
- **Impact:** Falls back to standard pip (slower) if uv unavailable
- **Mitigation:** Deploy script auto-installs uv
- **Validation:** Run `uv --version` to check installation

### 5. Query Behavior

#### Property ID Requirements

- **Assumption:** Users provide property ID for analytics queries
- **Impact:** Analytics queries fail without property ID
- **Mitigation:** CLI tool prompts for property ID; API returns error message
- **Validation:** Test queries with and without property ID

#### Query Understanding

- **Assumption:** LLM can understand natural language queries in English
- **Impact:** Non-English queries may be misclassified
- **Mitigation:** Intent classification prompt is optimized for English
- **Validation:** Test with diverse query phrasings

#### Multi-Agent Detection

- **Assumption:** Queries with "AND" or combined requirements trigger multi-agent
- **Impact:** Some complex queries may route to single agent
- **Mitigation:** Classification prompt explicitly looks for multi-intent signals
- **Validation:** Test with various multi-intent queries

## Known Limitations

### 1. Performance Limits

#### Rate Limiting

- **LiteLLM:** 5 requests per minute (12-second minimum gap)
- **GA4 API:** 10,000 requests per day (unlikely to hit in demo)
- **Sheets API:** 60 requests per minute (unlikely to hit with caching)
- **Impact:** Rapid queries may hit rate limits and fail
- **Workaround:** Wait 60 seconds between queries if rate limited
- **Future Fix:** Implement request queuing and throttling

#### Timeout Constraints

- **LLM Calls:** 30 seconds per call
- **Total Request:** 120 seconds maximum
- **Multi-Agent:** Can timeout with >3 agents or slow APIs
- **Impact:** Complex queries may timeout and return partial results
- **Workaround:** Simplify queries or increase timeout in `streamlit_app.py`
- **Future Fix:** Implement async processing with webhooks

#### Token Limits

- **LLM Context:** Limited by model's context window
- **Large Datasets:** SEO queries with >1000 rows may truncate data
- **Impact:** Responses may be incomplete for very large datasets
- **Workaround:** Filter data before sending to LLM
- **Future Fix:** Implement chunking and summarization

### 2. Data Freshness

#### GA4 Reporting Delay

- **Delay:** 24-48 hours for full data availability
- **Real-time:** Only basic metrics available in real-time
- **Impact:** "Today" queries may show incomplete data
- **Workaround:** Use "yesterday" or "7daysAgo" for complete data
- **Future Fix:** Document data freshness in responses

#### SEO Data Staleness

- **Update Frequency:** Manual Screaming Frog crawls (not automated)
- **Assumption:** Sheet is updated regularly by user
- **Impact:** SEO data may be outdated
- **Workaround:** Document last crawl date in sheet
- **Future Fix:** Add timestamp check and warnings

### 3. Functionality Gaps

#### No Historical Analysis

- **Limitation:** Cannot compare time periods (e.g., "month-over-month growth")
- **Impact:** Queries like "compare last month to this month" fail
- **Workaround:** Run two separate queries manually
- **Future Fix:** Implement comparative analysis in analytics agent

#### Limited Metric Support

- **Analytics:** Only common metrics (users, sessions, pageviews, bounce rate)
- **SEO:** Only Screaming Frog export columns
- **Impact:** Advanced metrics (e.g., engagement rate, core web vitals) unsupported
- **Workaround:** Query available metrics only
- **Future Fix:** Expand metric support based on user needs

#### No Data Visualization

- **Limitation:** Text-only responses (no charts or graphs)
- **Impact:** Users must interpret data textually
- **Workaround:** Copy data to Excel/Google Sheets for visualization
- **Future Fix:** Add chart generation to responses

#### No Authentication

- **Limitation:** No user authentication or API key validation
- **Impact:** Anyone with endpoint access can query
- **Workaround:** Deploy behind firewall or VPN
- **Future Fix:** Implement API key authentication

### 4. Error Handling Gaps

#### Partial Multi-Agent Failures

- **Scenario:** One agent succeeds, one fails in multi-agent query
- **Current Behavior:** Returns partial response with error message
- **Impact:** Incomplete analysis without clear indication
- **Workaround:** Retry failed sub-query separately
- **Future Fix:** Better error aggregation and retry logic

#### Silent Data Truncation

- **Scenario:** SEO dataset >1000 rows, LLM context exceeded
- **Current Behavior:** Truncates data silently, analyzes subset
- **Impact:** Incomplete analysis without user awareness
- **Workaround:** Filter queries to specific pages/issues
- **Future Fix:** Warn users when data is truncated

#### Rate Limit Recovery

- **Scenario:** Hit 5 RPM limit on LiteLLM
- **Current Behavior:** Fails with generic error message
- **Impact:** Users don't know to wait 60 seconds
- **Workaround:** Check error message for rate limit indicator
- **Future Fix:** Detect rate limit errors and suggest wait time

## Open Questions

### 1. Data Source Questions

**Q1:** What happens if the GA4 property has no data for the requested date range?

- **Current Answer:** Returns "No data found for the specified criteria" message
- **Open Issue:** Should we suggest alternative date ranges or verify property has any data?

**Q2:** How should we handle SEO sheets with custom column names?

- **Current Answer:** System expects exact column names from Screaming Frog export
- **Open Issue:** Should we support configurable column mapping?

**Q3:** Can we cache GA4/Sheets data to reduce API calls?

- **Current Answer:** No caching implemented
- **Open Issue:** What TTL is appropriate? How to invalidate cache?

### 2. Query Understanding Questions

**Q4:** How should we handle ambiguous queries like "show me data"?

- **Current Answer:** LLM attempts to infer intent, may fail
- **Open Issue:** Should we prompt user for clarification?

**Q5:** Should we support multi-language queries?

- **Current Answer:** Optimized for English only
- **Open Issue:** Can gemini-2.5-flash handle non-English? What accuracy?

**Q6:** How do we handle queries spanning multiple time periods?

- **Current Answer:** Not supported, only single date range per query
- **Open Issue:** Should we implement comparative analysis?

### 3. Multi-Agent Questions

**Q7:** What order should we invoke agents in multi-agent queries?

- **Current Answer:** Parallel invocation (no specific order)
- **Open Issue:** Should analytics always run first? Dependencies?

**Q8:** How many agents can we invoke before hitting timeout?

- **Current Answer:** 2-3 agents tested, likely max is 4-5
- **Open Issue:** Should we limit number of sub-queries?

**Q9:** Should we cache sub-query results within multi-agent flow?

- **Current Answer:** No caching, each agent call is fresh
- **Open Issue:** If same sub-query appears twice, should we cache?

### 4. Performance Questions

**Q10:** What's the optimal timeout for LLM calls?

- **Current Answer:** 30 seconds
- **Open Issue:** Too short for complex parsing? Too long for simple intents?

**Q11:** Should we implement request queuing for rate limits?

- **Current Answer:** No queuing, immediate failure on rate limit
- **Open Issue:** Queue requests and process at 5 RPM rate?

**Q12:** Can we parallelize LLM calls in multi-agent orchestration?

- **Current Answer:** Sequential: decompose → invoke → aggregate
- **Open Issue:** Can we invoke agents while decomposition is streaming?

### 5. Production Readiness Questions

**Q13:** How do we monitor LiteLLM budget in production?

- **Current Answer:** Manual checks via API endpoint
- **Open Issue:** Automated alerts when budget <$10? Daily reports?

**Q14:** Should we implement user authentication?

- **Current Answer:** No authentication, open endpoint
- **Open Issue:** API keys? OAuth2? IP whitelisting?

**Q15:** How do we handle multiple concurrent requests?

- **Current Answer:** Single-process uvicorn, no concurrency limits
- **Open Issue:** Deploy with gunicorn? Max concurrent requests?

### 6. Extensibility Questions

**Q16:** How easy is it to add a third agent (e.g., Search Console)?

- **Current Answer:** Would require code changes in orchestrator
- **Open Issue:** Should we make agent registration pluggable?

**Q17:** Can we support custom data sources via configuration?

- **Current Answer:** GA4 and Sheets are hardcoded
- **Open Issue:** Generic data source interface?

**Q18:** Should we expose intermediate agent results to users?

- **Current Answer:** Only final aggregated response visible
- **Open Issue:** Show sub-query results for transparency?

## Validation Checklist

Before deploying, verify:

- [ ] `credentials.json` exists and has correct permissions
- [ ] GA4 property ID is correct and has data
- [ ] Google Sheets ID is correct and accessible
- [ ] LiteLLM API key has sufficient budget (check `http://3.110.18.218/key/info`)
- [ ] Port 8080 is available
- [ ] Python 3.8+ is installed
- [ ] Internet connectivity to all required endpoints
- [ ] Test query returns expected results

## Risk Assessment

| Risk                       | Likelihood      | Impact   | Mitigation                                |
| -------------------------- | --------------- | -------- | ----------------------------------------- |
| LiteLLM API key expires    | High (3.8 days) | Critical | Monitor expiration, obtain new key        |
| Rate limit exceeded        | Medium          | Medium   | Implement queuing, warn users             |
| GA4 property has no data   | Low             | Medium   | Validate property before deployment       |
| Sheet structure changes    | Low             | High     | Version sheet format, validate on startup |
| Port 8080 in use           | Low             | Low      | Check before starting server              |
| Timeout on complex queries | Medium          | Medium   | Increase timeout, simplify queries        |
| Budget exhaustion          | Low             | Critical | Monitor budget, set alerts at $10         |

## Future Improvements

### Short-Term (Next Sprint)

1. Add budget monitoring and alerts
2. Implement request queuing for rate limits
3. Better error messages with actionable guidance
4. Cache frequently queried data

### Medium-Term (Next Month)

1. Comparative time period analysis
2. Data visualization in responses
3. User authentication and API keys
4. Async processing for long queries

### Long-Term (Next Quarter)

1. Additional data sources (Search Console, CRM)
2. Pluggable agent architecture
3. Real-time streaming responses
4. Dashboard UI for monitoring

---

**Last Updated:** 2025-01-19  
**Version:** 1.0.0  
**Status:** Documented for hackathon submission
