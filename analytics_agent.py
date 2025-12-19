"""Analytics Agent for GA4 queries."""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    FilterExpression,
    Filter,
    OrderBy,
)
from google.oauth2 import service_account
import config
from llm_utils import llm_client


class AnalyticsAgent:
    """Agent for handling GA4 analytics queries."""
    
    # Valid GA4 metrics and dimensions allowlist
    VALID_METRICS = {
        'activeUsers', 'sessions', 'totalUsers', 'screenPageViews', 
        'eventCount', 'conversions', 'engagementRate', 'bounceRate',
        'sessionDuration', 'averageSessionDuration', 'sessionsPerUser',
        'engagedSessions', 'userEngagementDuration', 'newUsers'
    }
    
    VALID_DIMENSIONS = {
        'date', 'pagePath', 'pageTitle', 'country', 'city', 
        'deviceCategory', 'sessionSource', 'sessionMedium', 
        'sessionCampaignName', 'browser', 'operatingSystem',
        'dayOfWeek', 'hour', 'month', 'year', 'hostName'
    }
    
    def __init__(self):
        """Initialize the Analytics Agent with GA4 credentials."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                config.GA4_CREDENTIALS_PATH,
                scopes=['https://www.googleapis.com/auth/analytics.readonly']
            )
            self.client = BetaAnalyticsDataClient(credentials=credentials)
            print("[OK] Analytics Agent initialized successfully")
        except Exception as e:
            print(f"[WARNING] Could not initialize GA4 client: {e}")
            self.client = None
    
    def parse_natural_language_query(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to parse natural language query into GA4 reporting plan.
        
        Args:
            query: Natural language query from user
            
        Returns:
            Dictionary with metrics, dimensions, date_range, filters, and order_by
        """
        prompt = f"""You are an expert Google Analytics 4 (GA4) query planner. Your task is to convert natural language questions into precise, executable GA4 API reporting plans.

=== AVAILABLE GA4 METRICS (use EXACT names) ===
{', '.join(sorted(self.VALID_METRICS))}

METRIC MAPPINGS (important translations):
- "page views" → "screenPageViews"
- "users" or "visitors" → "activeUsers" (for current period) or "totalUsers" (for unique count)
- "new users" or "new visitors" → "newUsers"
- "sessions" or "visits" → "sessions"
- "bounce rate" → "bounceRate"
- "engagement rate" → "engagementRate"
- "session duration" or "time on site" → "averageSessionDuration"

=== AVAILABLE GA4 DIMENSIONS (use EXACT names) ===
{', '.join(sorted(self.VALID_DIMENSIONS))}

DIMENSION MAPPINGS:
- "page" or "URL" → "pagePath"
- "page title" → "pageTitle"
- "location" → "country" (or "city" if more specific)
- "device" or "device type" → "deviceCategory"
- "source" → "sessionSource"
- "medium" → "sessionMedium"
- "campaign" → "sessionCampaignName"

=== DATE RANGE FORMATS ===
Use relative dates (preferred):
- "today", "yesterday"
- "7daysAgo", "14daysAgo", "30daysAgo", "90daysAgo"
- For "last N days" → use "NdaysAgo" to "today"
- For "last week" → "7daysAgo" to "today"
- For "last month" → "30daysAgo" to "today"

Absolute dates (if specific dates mentioned):
- Format: "YYYY-MM-DD" (e.g., "2024-01-15")

=== FILTER OPERATORS ===
- "==" : exact match (e.g., pagePath == "/pricing")
- "!=" : not equal
- "contains" : partial string match (e.g., pagePath contains "product")
- "not_contains" : does not contain
- ">" : greater than (for numeric comparisons)
- "<" : less than
- ">=" : greater than or equal
- "<=" : less than or equal

=== QUERY PLANNING RULES ===

1. METRICS SELECTION:
   - Always include relevant metrics based on what user asks
   - If user asks "how many", include count metrics (screenPageViews, activeUsers, sessions)
   - If user asks about "trends", include time-series metrics with date dimension
   - Limit to 3-5 most relevant metrics (avoid overloading)

2. DIMENSIONS SELECTION:
   - For "daily breakdown" or "trends" → MUST include "date" dimension
   - For "by page" or "which pages" → include "pagePath" (and optionally "pageTitle")
   - For "by location" → include "country" or "city"
   - For "by device" → include "deviceCategory"
   - For "by source" → include "sessionSource" and/or "sessionMedium"
   - Maximum 2-3 dimensions (GA4 limitation)

3. DATE RANGE:
   - "last week" → {{"start_date": "7daysAgo", "end_date": "today"}}
   - "last 14 days" → {{"start_date": "14daysAgo", "end_date": "today"}}
   - "last month" → {{"start_date": "30daysAgo", "end_date": "today"}}
   - "yesterday" → {{"start_date": "yesterday", "end_date": "yesterday"}}
   - If no time period mentioned, default to last 7 days

4. FILTERS:
   - If specific page mentioned (e.g., "/pricing", "pricing page") → add pagePath filter
   - If specific country mentioned → add country filter
   - If specific device mentioned (mobile, desktop, tablet) → add deviceCategory filter
   - Use "contains" for partial matches, "==" for exact matches

5. ORDERING:
   - For "top pages" → order by screenPageViews desc
   - For "trending" → order by date asc
   - For "most users" → order by activeUsers desc
   - For "least bounce rate" → order by bounceRate asc
   - Include limit implicitly (top N means order desc + limit N)

=== EXAMPLES ===

Query: "Give me a daily breakdown of page views, users, and sessions for the /pricing page over the last 14 days"
Output:
{{
  "metrics": ["screenPageViews", "activeUsers", "sessions"],
  "dimensions": ["date"],
  "date_range": {{"start_date": "14daysAgo", "end_date": "today"}},
  "filters": [{{"dimension": "pagePath", "operator": "==", "value": "/pricing"}}],
  "order_by": [{{"field": "date", "desc": false}}]
}}

Query: "What are the top 5 pages by views in the last 30 days?"
Output:
{{
  "metrics": ["screenPageViews", "activeUsers"],
  "dimensions": ["pagePath", "pageTitle"],
  "date_range": {{"start_date": "30daysAgo", "end_date": "today"}},
  "filters": [],
  "order_by": [{{"field": "screenPageViews", "desc": true}}]
}}

Query: "How many mobile users visited yesterday?"
Output:
{{
  "metrics": ["activeUsers"],
  "dimensions": ["deviceCategory"],
  "date_range": {{"start_date": "yesterday", "end_date": "yesterday"}},
  "filters": [{{"dimension": "deviceCategory", "operator": "==", "value": "mobile"}}],
  "order_by": []
}}

Query: "Show me traffic sources for the homepage last week"
Output:
{{
  "metrics": ["sessions", "activeUsers"],
  "dimensions": ["sessionSource", "sessionMedium"],
  "date_range": {{"start_date": "7daysAgo", "end_date": "today"}},
  "filters": [{{"dimension": "pagePath", "operator": "==", "value": "/"}}],
  "order_by": [{{"field": "sessions", "desc": true}}]
}}

=== USER QUERY ===

{query}

=== YOUR TASK ===

Analyze the user query and create a precise GA4 reporting plan. Think through:
1. What metrics answer the question? (translate common terms to GA4 metric names)
2. What dimensions provide the breakdown requested?
3. What time period is implied or stated?
4. Are there any filters needed (specific pages, devices, locations)?
5. How should results be ordered?

Output ONLY valid JSON matching this structure:
{{
  "metrics": ["metricName1", "metricName2"],
  "dimensions": ["dimensionName1"],
  "date_range": {{"start_date": "NdaysAgo", "end_date": "today"}},
  "filters": [{{"dimension": "dimensionName", "operator": "==", "value": "filterValue"}}],
  "order_by": [{{"field": "metricOrDimensionName", "desc": true}}]
}}

Respond with ONLY the JSON, no explanatory text before or after."""

        response = llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        # Extract JSON from response
        try:
            # Try to find JSON in the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            plan = json.loads(response)
            
            # Validate metrics and dimensions
            plan['metrics'] = [m for m in plan.get('metrics', []) if m in self.VALID_METRICS]
            plan['dimensions'] = [d for d in plan.get('dimensions', []) if d in self.VALID_DIMENSIONS]
            
            # Ensure we have at least some metrics
            if not plan['metrics']:
                plan['metrics'] = ['screenPageViews', 'activeUsers', 'sessions']
            
            return plan
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Response was: {response}")
            # Return default plan
            return {
                'metrics': ['screenPageViews', 'activeUsers', 'sessions'],
                'dimensions': ['date'],
                'date_range': {'start_date': '7daysAgo', 'end_date': 'today'},
                'filters': [],
                'order_by': []
            }
    
    def execute_ga4_query(
        self, 
        property_id: str, 
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a GA4 query based on the reporting plan.
        
        Args:
            property_id: GA4 property ID (format: "properties/123456789")
            plan: Reporting plan from parse_natural_language_query
            
        Returns:
            Dictionary with GA4 results
        """
        if not self.client:
            return {
                'error': 'GA4 client not initialized. Check credentials.json',
                'data': []
            }
        
        try:
            # Ensure property_id has correct format
            if not property_id.startswith('properties/'):
                property_id = f'properties/{property_id}'
            
            # Build date range
            date_range_config = plan.get('date_range', {})
            date_range = DateRange(
                start_date=date_range_config.get('start_date', '7daysAgo'),
                end_date=date_range_config.get('end_date', 'today')
            )
            
            # Build metrics
            metrics = [Metric(name=m) for m in plan.get('metrics', ['screenPageViews'])]
            
            # Build dimensions
            dimensions = [Dimension(name=d) for d in plan.get('dimensions', ['date'])]
            
            # Build request
            request = RunReportRequest(
                property=property_id,
                date_ranges=[date_range],
                metrics=metrics,
                dimensions=dimensions,
            )
            
            # Add filters if present
            filters = plan.get('filters', [])
            if filters:
                # Build filter expression (simplified - only handles first filter)
                if filters:
                    first_filter = filters[0]
                    dimension_filter = Filter(
                        field_name=first_filter['dimension'],
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.EXACT if first_filter['operator'] == '==' else Filter.StringFilter.MatchType.CONTAINS,
                            value=first_filter['value']
                        )
                    )
                    request.dimension_filter = FilterExpression(filter=dimension_filter)
            
            # Add ordering if present
            order_by_list = plan.get('order_by', [])
            if order_by_list:
                request.order_bys = [
                    OrderBy(
                        metric=OrderBy.MetricOrderBy(metric_name=ob['field']) if ob['field'] in self.VALID_METRICS else None,
                        dimension=OrderBy.DimensionOrderBy(dimension_name=ob['field']) if ob['field'] in self.VALID_DIMENSIONS else None,
                        desc=ob.get('desc', False)
                    )
                    for ob in order_by_list
                ]
            
            # Execute request
            response = self.client.run_report(request)
            
            # Parse response
            results = []
            for row in response.rows:
                row_data = {}
                
                # Add dimensions
                for i, dimension_value in enumerate(row.dimension_values):
                    dimension_name = plan['dimensions'][i]
                    row_data[dimension_name] = dimension_value.value
                
                # Add metrics
                for i, metric_value in enumerate(row.metric_values):
                    metric_name = plan['metrics'][i]
                    row_data[metric_name] = metric_value.value
                
                results.append(row_data)
            
            return {
                'success': True,
                'data': results,
                'row_count': len(results)
            }
        
        except Exception as e:
            print(f"Error executing GA4 query: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }
    
    def generate_natural_language_response(
        self, 
        query: str, 
        plan: Dict[str, Any], 
        results: Dict[str, Any]
    ) -> str:
        """
        Generate a natural language response from GA4 results using LLM.
        
        Args:
            query: Original user query
            plan: GA4 reporting plan
            results: Results from execute_ga4_query
            
        Returns:
            Natural language explanation
        """
        if not results.get('success'):
            return f"I encountered an error querying Google Analytics: {results.get('error', 'Unknown error')}. The GA4 property may be empty or the credentials may be invalid."
        
        data = results.get('data', [])
        
        if not data:
            return f"I successfully queried Google Analytics, but no data was found for your request. This could mean:\n- The GA4 property has no traffic for the specified time period\n- The filters excluded all data\n- The page or dimension you're looking for doesn't exist in the data\n\nQuery details: {json.dumps(plan, indent=2)}"
        
        # Prepare data summary for LLM
        data_summary = json.dumps(data, indent=2)
        if len(data_summary) > 3000:  # Truncate if too long
            data_summary = json.dumps(data[:20], indent=2) + f"\n... ({len(data)} total rows)"
        
        prompt = f"""You are an expert data analyst specializing in web analytics. Your task is to interpret Google Analytics 4 data and explain it clearly to non-technical users.

=== USER'S QUESTION ===
{query}

=== GA4 QUERY DETAILS ===
Metrics analyzed: {', '.join(plan.get('metrics', []))}
Dimensions: {', '.join(plan.get('dimensions', []))}
Time period: {plan.get('date_range', {}).get('start_date')} to {plan.get('date_range', {}).get('end_date')}
Filters applied: {json.dumps(plan.get('filters', []))}

=== RAW DATA FROM GOOGLE ANALYTICS ===
{data_summary}

Total rows: {len(data)}

=== YOUR TASK ===

Analyze this data and provide a comprehensive, natural language answer. Structure your response as follows:

1. DIRECT ANSWER (1-2 sentences)
   - Answer the user's exact question first
   - Use specific numbers from the data
   - Example: "Your pricing page received 3,847 page views from 2,156 unique users over the last 14 days."

2. KEY INSIGHTS (2-4 bullet points)
   - Identify trends (increasing, decreasing, stable)
   - Highlight top performers (if applicable)
   - Note any unusual patterns or outliers
   - Calculate averages or percentages when helpful
   - Example: "Traffic peaked on Monday (Dec 15) with 445 views, which is 67% higher than the daily average."

3. CONTEXT & INTERPRETATION (optional, 1-2 sentences)
   - Explain what the numbers might mean
   - Suggest potential actions if patterns are concerning
   - Compare to benchmarks if relevant

=== STYLE GUIDELINES ===

- Use SPECIFIC NUMBERS from the data (not "many" or "few")
- Format large numbers with commas (3,847 not 3847)
- Express percentages to 1 decimal place (23.5% not 23.456%)
- Use clear date references ("Monday, December 15" or "the week of Dec 10-16")
- Avoid jargon - explain technical terms if you use them
- Be conversational but professional
- If showing a trend, explain the direction and magnitude
- If comparing items, clearly state which is higher/lower

=== EXAMPLES OF GOOD RESPONSES ===

Query: "How many users visited last week?"
Good: "Your site had 8,234 users last week (Dec 10-16), with an average of 1,176 users per day. Traffic was highest on Wednesday (1,456 users) and lowest on Sunday (892 users), following a typical weekly pattern."

Query: "Top pages by views?"
Good: "Here are your top 5 pages by views: 1) Homepage (12,445 views) 2) Pricing page (3,821 views) 3) Features page (2,104 views) 4) About page (1,876 views) 5) Contact page (1,234 views). Your homepage accounts for 56.3% of all page views."

Query: "Show me daily trends for the pricing page"
Good: "The pricing page showed steady growth over the 14-day period, starting at 187 views on Dec 1 and reaching 312 views by Dec 14 - a 67% increase. The average daily views were 243, with weekdays (avg: 276 views) outperforming weekends (avg: 145 views) by 90%."

=== EDGE CASES ===

- If data is sparse (few rows): Acknowledge and provide what's available
- If trends are flat: Say "stable" rather than "no change"
- If comparing periods and one is much higher: Calculate and state the percentage difference
- If asked for top N but got fewer results: Explain why (e.g., "only 7 pages matched the filter")

Now provide your analysis:"""

        response = llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return response
    
    def handle_query(self, query: str, property_id: str) -> str:
        """
        Main entry point for handling analytics queries.
        
        Args:
            query: Natural language query
            property_id: GA4 property ID
            
        Returns:
            Natural language response
        """
        try:
            # Step 1: Parse natural language to GA4 plan
            print(f"📊 Parsing query: {query}")
            plan = self.parse_natural_language_query(query)
            print(f"📋 GA4 Plan: {json.dumps(plan, indent=2)}")
            
            # Step 2: Execute GA4 query
            print(f"🔍 Querying GA4 property: {property_id}")
            results = self.execute_ga4_query(property_id, plan)
            print(f"[OK] Retrieved {results.get('row_count', 0)} rows")
            
            # Step 3: Generate natural language response
            print("💬 Generating response...")
            response = self.generate_natural_language_response(query, plan, results)
            
            return response
        
        except Exception as e: 
            return f"I encountered an error while processing your analytics query: {str(e)}"
