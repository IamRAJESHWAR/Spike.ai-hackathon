"""SEO Agent for Screaming Frog data analysis."""

import json
from typing import Dict, Any, List
import gspread
from google.oauth2 import service_account
import pandas as pd
import config
from llm_utils import llm_client


class SEOAgent:
    """Agent for handling SEO audit queries from Screaming Frog data."""
    
    def __init__(self):
        """Initialize the SEO Agent with Google Sheets access."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                config.GA4_CREDENTIALS_PATH,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets.readonly',
                    'https://www.googleapis.com/auth/drive.readonly'
                ]
            )
            self.gc = gspread.authorize(credentials)
            self.spreadsheet_id = config.SEO_SPREADSHEET_ID
            self.data = None
            self.load_data()
            print("[OK] SEO Agent initialized successfully")
        except Exception as e:
            print(f"[WARNING] Could not initialize SEO agent: {e}")
            self.gc = None
            self.data = None
    
    def load_data(self):
        """Load SEO data from Google Sheets."""
        try:
            if not self.gc:
                return
            
            # Open spreadsheet
            spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
            
            # Get first sheet (usually the main data)
            worksheet = spreadsheet.get_worksheet(0)
            
            # Get all records as list of dictionaries
            records = worksheet.get_all_records()
            
            if records:
                self.data = pd.DataFrame(records)
                print(f"[OK] Loaded {len(self.data)} SEO records from Google Sheets")
                print(f"📋 Columns: {', '.join(self.data.columns[:10])}...")
            else:
                print("[WARNING] No data found in spreadsheet")
                self.data = pd.DataFrame()
        
        except Exception as e:
            print(f"Error loading SEO data: {e}")
            self.data = pd.DataFrame()
    
    def get_data_schema(self) -> str:
        """Get a description of the available data schema."""
        if self.data is None or self.data.empty:
            return "No SEO data available"
        
        schema_info = {
            'total_rows': len(self.data),
            'columns': list(self.data.columns),
            'sample_data': self.data.head(3).to_dict('records')
        }
        
        return json.dumps(schema_info, indent=2)
    
    def parse_seo_query(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to parse natural language query into data analysis plan.
        
        Args:
            query: Natural language query from user
            
        Returns:
            Dictionary with analysis plan
        """
        schema = self.get_data_schema()
        
        prompt = f"""You are an expert SEO data analyst specializing in technical SEO audits. Convert natural language questions about website technical health into precise data analysis plans.

=== AVAILABLE SEO DATA ===
{schema}

This data is from a Screaming Frog crawl that audits all pages on a website for technical SEO issues.

=== COMMON COLUMN MAPPINGS ===

URL/Page: "Address" or "URL"
Protocol: "Protocol" (HTTP or HTTPS)
Status: "Status Code" (200=OK, 301=Redirect, 404=Not Found, 500=Error)
Title: "Title 1", "Title 1 Length", "Title 1 Pixel Width"
Meta Description: "Meta Description 1", "Meta Description 1 Length"
Indexability: "Indexability", "Indexability Status"
Headings: "H1-1", "H2-1", etc.
Content: "Word Count", "Content"
Links: "Inlinks", "Outlinks"

=== OPERATION TYPES ===

1. "filter" : Find pages matching criteria
   Example: "Which pages don't use HTTPS?"
   
2. "group" : Count/analyze pages by category
   Example: "Group pages by status code"
   
3. "aggregate" : Calculate statistics
   Example: "Average title tag length"
   
4. "calculate" : Perform custom calculations
   Example: "Percentage of pages that are indexable"
   
5. "list" : Simple listing of columns
   Example: "List all URLs and their titles"

=== FILTER OPERATORS ===

"==" : Exact match
"!=" : Not equal
"contains" : Partial string match
"not_contains" : Does not contain
">" : Greater than (numeric)
"<" : Less than (numeric)
">=" : Greater than or equal
"<=" : Less than or equal

=== EXAMPLES ===

Query: "Which URLs don't use HTTPS and have title tags longer than 60 characters?"
Output:
{{
  "operation": "filter",
  "columns": ["Address", "Protocol", "Title 1", "Title 1 Length"],
  "conditions": [
    {{"column": "Protocol", "operator": "!=", "value": "HTTPS"}},
    {{"column": "Title 1 Length", "operator": ">", "value": 60}}
  ],
  "group_by": null,
  "aggregate": null,
  "output_format": "text"
}}

Query: "Group all pages by indexability status"
Output:
{{
  "operation": "group",
  "columns": ["Indexability"],
  "conditions": [],
  "group_by": "Indexability",
  "aggregate": "count",
  "output_format": "text"
}}

Query: "Calculate percentage of indexable pages"
Output:
{{
  "operation": "calculate",
  "columns": ["Indexability"],
  "conditions": [],
  "group_by": "Indexability",
  "aggregate": "count",
  "output_format": "text"
}}

Query: "Return top 10 pages by word count in JSON"
Output:
{{
  "operation": "list",
  "columns": ["Address", "Title 1", "Word Count"],
  "conditions": [],
  "group_by": null,
  "aggregate": null,
  "output_format": "json"
}}

=== USER QUERY ===

{query}

=== YOUR TASK ===

Create a data analysis plan. Consider:
1. What operation? (filter, group, aggregate, calculate, list)
2. Which columns are relevant?
3. What filters/conditions?
4. Is grouping or aggregation needed?
5. Output format? (use "json" only if user explicitly asks for JSON/structured data)

Output as JSON:
{{
  "operation": "filter|group|aggregate|calculate|list",
  "columns": ["Column1", "Column2"],
  "conditions": [{{"column": "Name", "operator": "op", "value": "val"}}],
  "group_by": "ColumnName" or null,
  "aggregate": "count|sum|mean" or null,
  "output_format": "text|json"
}}

Respond with ONLY JSON, no explanatory text."""

        response = llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            plan = json.loads(response)
            return plan
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response: {e}")
            return {
                'operation': 'filter',
                'columns': [],
                'conditions': [],
                'group_by': None,
                'aggregate': None,
                'output_format': 'text'
            }
    
    def execute_analysis(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute data analysis based on the plan.
        
        Args:
            plan: Analysis plan from parse_seo_query
            
        Returns:
            Dictionary with analysis results
        """
        if self.data is None or self.data.empty:
            return {
                'success': False,
                'error': 'No SEO data available',
                'data': []
            }
        
        try:
            df = self.data.copy()
            
            # Apply filters
            conditions = plan.get('conditions', [])
            for condition in conditions:
                col = condition.get('column')
                op = condition.get('operator')
                val = condition.get('value')
                
                if col not in df.columns:
                    continue
                
                if op == '==':
                    df = df[df[col] == val]
                elif op == '!=':
                    df = df[df[col] != val]
                elif op == '>':
                    df = df[df[col] > val]
                elif op == '<':
                    df = df[df[col] < val]
                elif op == '>=':
                    df = df[df[col] >= val]
                elif op == '<=':
                    df = df[df[col] <= val]
                elif op == 'contains':
                    df = df[df[col].astype(str).str.contains(str(val), case=False, na=False)]
                elif op == 'not_contains':
                    df = df[~df[col].astype(str).str.contains(str(val), case=False, na=False)]
            
            # Apply grouping and aggregation
            group_by = plan.get('group_by')
            aggregate = plan.get('aggregate')
            
            if group_by and group_by in df.columns:
                if aggregate == 'count':
                    result = df.groupby(group_by).size().reset_index(name='count')
                elif aggregate in ['sum', 'mean', 'min', 'max']:
                    result = df.groupby(group_by).agg(aggregate).reset_index()
                else:
                    result = df.groupby(group_by).size().reset_index(name='count')
                
                results_data = result.to_dict('records')
            else:
                # Select columns
                columns = plan.get('columns', [])
                if columns:
                    available_cols = [c for c in columns if c in df.columns]
                    if available_cols:
                        df = df[available_cols]
                
                results_data = df.to_dict('records')
            
            return {
                'success': True,
                'data': results_data,
                'row_count': len(results_data)
            }
        
        except Exception as e:
            print(f"Error executing SEO analysis: {e}")
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
        Generate a natural language response from analysis results.
        
        Args:
            query: Original user query
            plan: Analysis plan
            results: Results from execute_analysis
            
        Returns:
            Natural language explanation or JSON (based on plan)
        """
        if not results.get('success'):
            return f"I encountered an error analyzing the SEO data: {results.get('error', 'Unknown error')}"
        
        data = results.get('data', [])
        
        if not data:
            return "I successfully analyzed the SEO data, but no results matched your criteria. Try broadening your filters or checking the available data columns."
        
        # Check if JSON output was requested
        if plan.get('output_format') == 'json' or 'json' in query.lower():
            return json.dumps(data, indent=2)
        
        # Generate natural language response
        data_summary = json.dumps(data[:50], indent=2)
        if len(data) > 50:
            data_summary += f"\n... ({len(data)} total results)"
        
        prompt = f"""You are an expert SEO consultant analyzing technical audit data. Your task is to explain SEO findings clearly and provide actionable insights.

=== USER'S QUESTION ===
{query}

=== ANALYSIS PERFORMED ===
Operation: {plan.get('operation')}
Columns analyzed: {', '.join(plan.get('columns', []))}
Filters applied: {json.dumps(plan.get('conditions', []))}
Grouping: {plan.get('group_by', 'None')}
Aggregation: {plan.get('aggregate', 'None')}

=== RESULTS FROM SEO AUDIT ===
{data_summary}

Total results: {len(data)}

=== YOUR TASK ===

Provide a comprehensive SEO analysis structured as follows:

1. SUMMARY (1-2 sentences)
   - Direct answer to the question with key number
   - Example: "I found 127 pages that don't use HTTPS and have title tags exceeding 60 characters."

2. DETAILED FINDINGS (2-4 points)
   - Break down the results with specific examples
   - Highlight the most critical issues
   - Show counts or percentages
   - Example: "The longest title tag is 89 characters on the /products/enterprise page."

3. SEO IMPACT (1-2 sentences)
   - Explain why these findings matter for SEO
   - What's the potential impact on rankings or indexing?
   - Example: "Non-HTTPS pages may be penalized by search engines and lose trust with users."

4. RECOMMENDATIONS (2-3 action items, optional)
   - Specific steps to fix issues
   - Prioritize by severity
   - Example: "Priority 1: Implement HTTPS site-wide using 301 redirects."

=== STYLE GUIDELINES ===

- Use SPECIFIC NUMBERS (not "many" or "several")
- Be clear about severity (Critical, High, Medium, Low priority)
- Cite specific examples from the data when possible
- Use SEO terminology but explain technical terms
- Format lists with numbers or bullets for clarity
- If showing grouped data, present it in an organized way

=== EXAMPLES OF GOOD RESPONSES ===

Query: "Which pages don't use HTTPS?"
Good: "I found 45 pages still using HTTP instead of HTTPS. These include:
- Homepage (http://example.com)
- About page (http://example.com/about)
- Contact page (http://example.com/contact)
... and 42 more pages.

SEO Impact: Non-HTTPS pages are flagged as 'Not Secure' in browsers, which hurts user trust and can negatively impact rankings. Google has confirmed HTTPS as a ranking signal.

Recommendation: Implement HTTPS site-wide by obtaining an SSL certificate and setting up 301 redirects from HTTP to HTTPS URLs."

Query: "Group pages by indexability status"
Good: "Here's the breakdown of your 1,247 crawled pages by indexability status:

• Indexable: 892 pages (71.5%) - These are properly configured for search engines
• Non-Indexable: 287 pages (23.0%) - Blocked from indexing
• Blocked by robots.txt: 68 pages (5.5%) - Intentionally excluded

The non-indexable pages include mostly admin, login, and duplicate content pages, which is expected. However, I noticed 12 product pages are non-indexable, which may be unintentional and should be reviewed."

Query: "Pages with missing meta descriptions"
Good: "I found 156 pages (12.5% of your site) without meta descriptions. The top missing pages by importance are:

1. /products/enterprise (high-value page)
2. /solutions/healthcare (key landing page)
3. /blog/seo-guide-2024 (popular blog post)

SEO Impact: Missing meta descriptions mean search engines will auto-generate snippets from page content, which may not be compelling or accurate. This can reduce click-through rates from search results by 15-30%.

Recommendations:
1. Write unique 150-160 character meta descriptions for all product and solution pages (Priority: High)
2. Add meta descriptions to top 50 blog posts based on traffic (Priority: Medium)
3. Create a template for auto-generating basic meta descriptions for less critical pages (Priority: Low)"

=== EDGE CASES ===

- If no issues found: Celebrate! "Great news: all pages use HTTPS properly."
- If overwhelming number of issues: Group and prioritize
- If technical jargon needed: Explain it briefly
- If grouping data: Show percentages for context

Now provide your SEO analysis:"""

        response = llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return response
    
    def handle_query(self, query: str) -> str:
        """
        Main entry point for handling SEO queries.
        
        Args:
            query: Natural language query
            
        Returns:
            Natural language response or JSON
        """
        try:
            # Refresh data in case spreadsheet was updated
            self.load_data()
            
            if self.data is None or self.data.empty:
                return "SEO data is not available. Please check the Google Sheets configuration and credentials."
            
            # Step 1: Parse query
            print(f"🔍 Parsing SEO query: {query}")
            plan = self.parse_seo_query(query)
            print(f"📋 Analysis Plan: {json.dumps(plan, indent=2)}")
            
            # Step 2: Execute analysis
            print("📊 Executing analysis...")
            results = self.execute_analysis(plan)
            print(f"[OK] Found {results.get('row_count', 0)} results")
            
            # Step 3: Generate response
            print("💬 Generating response...")
            response = self.generate_natural_language_response(query, plan, results)
            
            return response
        
        except Exception as e:
            return f"I encountered an error while processing your SEO query: {str(e)}"
