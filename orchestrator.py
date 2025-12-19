"""Orchestrator for intent detection and agent routing."""

import json
from typing import Dict, Any, Optional
from llm_utils import llm_client
from analytics_agent import AnalyticsAgent
from seo_agent import SEOAgent
import config


class Orchestrator:
    """Central orchestrator for intent detection and agent routing."""
    
    def __init__(self):
        """Initialize orchestrator with agents."""
        self.analytics_agent = AnalyticsAgent()
        self.seo_agent = SEOAgent()
        self.default_property_id = config.GA4_PROPERTY_ID
        print(f"[OK] Orchestrator initialized (Default Property ID: {self.default_property_id})")
    
    def detect_intent(self, query: str, property_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect user intent and determine which agent(s) to use.
        
        Args:
            query: Natural language query
            property_id: GA4 property ID (if provided, hints at analytics intent)
            
        Returns:
            Dictionary with intent classification
        """
        prompt = f"""You are an expert intent classifier for a multi-agent AI system that analyzes web analytics and SEO data.

=== AVAILABLE AGENTS ===

1. ANALYTICS AGENT (Google Analytics 4)
   Handles queries about:
   - Traffic metrics: page views, users, sessions, bounce rate, engagement
   - Traffic sources: organic, paid, referral, social, direct, email
   - User behavior: session duration, pages per session, conversion events
   - Demographics: country, city, device category, browser
   - Time-series analysis: daily/weekly/monthly trends, comparisons
   - Specific page performance: views, users, engagement for individual URLs
   
   Keywords: views, visitors, users, traffic, sessions, clicks, conversions, analytics, engagement, 
   source, medium, campaign, behavior, trends, increase, decrease, comparison

2. SEO AGENT (Screaming Frog Technical Audit)
   Handles queries about:
   - URL structure: protocols (HTTP/HTTPS), URL length, parameters
   - On-page elements: title tags, meta descriptions, headings (H1-H6)
   - Technical health: indexability, crawlability, status codes (200, 301, 404, 500)
   - Content analysis: word count, duplicate content, missing elements
   - Site architecture: internal links, external links, redirects
   
   Keywords: title, meta, description, HTTPS, HTTP, indexable, crawl, status code, redirect, 
   duplicate, missing, technical SEO, on-page, site structure, URL

3. MULTI-AGENT (Combines Both)
   Required when query needs BOTH traffic performance AND technical SEO data.
   Common patterns:
   - "Top pages by [traffic metric] + their [SEO element]"
   - "High-traffic pages with [SEO issue]"
   - "Correlate [analytics metric] with [SEO attribute]"
   - Comparing performance of pages with different SEO characteristics

=== CLASSIFICATION RULES ===

1. If query asks about traffic, users, views, sessions, sources → ANALYTICS
2. If query asks about titles, meta tags, HTTPS, indexability, technical issues, accessibility, violations → SEO
3. If query needs to COMBINE traffic data WITH SEO attributes → MULTI_AGENT
4. Analyze the CONTENT of the query, not just whether propertyId is provided
5. Keywords like "accessibility", "violations", "WCAG", "status code" → SEO
6. Keywords like "users", "sessions", "traffic", "views" → ANALYTICS

=== EXAMPLES ===

Query: "How many users visited my site last week?"
Intent: analytics (pure traffic metric)

Query: "Which pages don't use HTTPS?"
Intent: seo (pure technical issue)

Query: "What are the top 10 pages by views AND their title tags?"
Intent: multi_agent (needs both traffic ranking AND SEO data)

Query: "Show me pages with high traffic that have missing meta descriptions"
Intent: multi_agent (combines traffic threshold with SEO issue)

Query: "Give me a breakdown of sessions by traffic source"
Intent: analytics (analytics-only query)

Query: "How many pages are indexable?"
Intent: seo (SEO audit question)

Query: "Compare page views between /pricing and /features"
Intent: analytics (comparing traffic metrics)

Query: "Which top 20% pages by traffic have duplicate title tags?"
Intent: multi_agent (needs traffic ranking + SEO audit)

=== USER QUERY ===

Query: "{query}"

=== TASK ===

Analyze the query and classify the intent based ONLY on the query content. Consider:
1. What data sources are needed?
2. Can this be answered with analytics data alone?
3. Can this be answered with SEO data alone?
4. Does it require joining/combining both data sources?

Ignore whether a property ID is provided - focus on what the user is asking for.

Provide your response as JSON:
{{
  "intent": "analytics|seo|multi_agent",
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation of why you chose this classification"
}}

Respond ONLY with valid JSON, no other text."""

        response = llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            intent = json.loads(response)
            return intent
        
        except json.JSONDecodeError as e:
            print(f"Failed to parse intent: {e}")
            # Default to analytics if property_id provided, else SEO
            return {
                'intent': 'analytics' if property_id else 'seo',
                'confidence': 0.5,
                'reasoning': 'Failed to parse, using default'
            }
    
    def route_query(
        self, 
        query: str, 
        property_id: Optional[str] = None
    ) -> str:
        """
        Route query to appropriate agent(s) and return response.
        
        Args:
            query: Natural language query
            property_id: GA4 property ID (optional, uses default if not provided)
            
        Returns:
            Response string
        """
        try:
            # Use default property ID if not provided
            if not property_id:
                property_id = self.default_property_id
            
            # Step 1: Detect intent
            print(f"\n{'='*60}")
            print(f"📨 Received Query: {query}")
            print(f"🔑 Property ID: {property_id} {'(default)' if property_id == self.default_property_id else '(user-provided)'}")
            
            intent_result = self.detect_intent(query, property_id)
            intent = intent_result.get('intent', 'analytics')
            print(f"🎯 Intent: {intent} (confidence: {intent_result.get('confidence', 0):.2f})")
            print(f"💭 Reasoning: {intent_result.get('reasoning', 'N/A')}")
            
            # Step 2: Route to agent(s) - LLM decides whether to use property_id
            if intent == 'analytics':
                print("→ Routing to Analytics Agent (LLM classified as analytics query)")
                return self.analytics_agent.handle_query(query, property_id)
            
            elif intent == 'seo':
                print("→ Routing to SEO Agent (LLM classified as SEO query, property_id available but not used)")
                return self.seo_agent.handle_query(query)
            
            elif intent == 'multi_agent':
                print("→ Routing to Multi-Agent System (LLM classified as multi-agent query)")
                return self.handle_multi_agent_query(query, property_id)
            
            else:
                return f"Unknown intent: {intent}. Please rephrase your query."
        
        except Exception as e:
            print(f"❌ Error in orchestrator: {e}")
            return f"I encountered an error processing your request: {str(e)}"
    
    def handle_multi_agent_query(
        self, 
        query: str, 
        property_id: Optional[str] = None
    ) -> str:
        """
        Handle queries that require multiple agents.
        
        Args:
            query: Natural language query
            property_id: GA4 property ID (optional)
            
        Returns:
            Unified response
        """
        try:
            # Decompose query into sub-queries
            print("🔀 Decomposing multi-agent query...")
            decomposition = self.decompose_query(query)
            
            # Execute sub-queries
            analytics_result = None
            seo_result = None
            
            if decomposition.get('analytics_query'):
                if not property_id:
                    analytics_result = "Analytics data not available (no propertyId provided)"
                else:
                    print(f"  📊 Analytics sub-query: {decomposition['analytics_query']}")
                    analytics_result = self.analytics_agent.handle_query(
                        decomposition['analytics_query'], 
                        property_id
                    )
            
            if decomposition.get('seo_query'):
                print(f"  🔍 SEO sub-query: {decomposition['seo_query']}")
                seo_result = self.seo_agent.handle_query(decomposition['seo_query'])
            
            # Aggregate results
            print("🔗 Aggregating results...")
            final_response = self.aggregate_results(
                query, 
                analytics_result, 
                seo_result
            )
            
            return final_response
        
        except Exception as e:
            print(f"Error in multi-agent handling: {e}")
            return f"I encountered an error processing your multi-domain query: {str(e)}"
    
    def decompose_query(self, query: str) -> Dict[str, str]:
        """
        Decompose a multi-agent query into sub-queries for each agent.
        
        Args:
            query: Original query
            
        Returns:
            Dictionary with analytics_query and seo_query
        """
        prompt = f"""You are an expert query decomposer for a multi-agent AI system. Your task is to break down complex questions that require both analytics AND SEO data into separate, focused sub-queries.

=== AVAILABLE DATA SOURCES ===

1. ANALYTICS AGENT (Google Analytics 4)
   Can answer: traffic metrics, user counts, page views, sessions, sources, trends, comparisons
   Cannot answer: technical SEO attributes, page content, meta tags

2. SEO AGENT (Screaming Frog Technical Audit)
   Can answer: title tags, meta descriptions, HTTPS status, indexability, technical issues, URL structure
   Cannot answer: traffic data, user behavior, conversion metrics

=== DECOMPOSITION RULES ===

1. ANALYTICS SUB-QUERY:
   - Should ask for traffic/performance metrics
   - Include time periods if mentioned
   - Request top N items if ranking is needed
   - Focus on quantitative performance
   - Example: "What are the top 10 pages by page views in the last 30 days?"

2. SEO SUB-QUERY:
   - Should ask for technical SEO attributes
   - Reference the same pages/URLs mentioned in analytics query
   - Focus on on-page elements and technical health
   - Example: "What are the title tags and meta descriptions for these top pages?"

3. BOTH QUERIES SHOULD:
   - Be self-contained (can be executed independently)
   - Reference the same pages/URLs for proper joining
   - Be clear and specific
   - Maintain the user's intent and filters

=== EXAMPLES ===

Query: "What are the top 10 pages by views in the last 14 days, and what are their title tags?"
Output:
{{
  "analytics_query": "What are the top 10 pages by page views in the last 14 days? Include the page URLs.",
  "seo_query": "What are the title tags for all pages in the site? Include the page URLs."
}}

Query: "Show me high-traffic pages with missing meta descriptions"
Output:
{{
  "analytics_query": "What are the top 20 pages by page views in the last 30 days? Include page URLs.",
  "seo_query": "Which pages have missing or empty meta descriptions? Include the page URLs."
}}

Query: "Which pages are in the top 20% by views but have duplicate title tags?"
Output:
{{
  "analytics_query": "What are the top 20% of pages by page views? Include page URLs and view counts.",
  "seo_query": "Which pages have duplicate title tags? Include page URLs and the title tag content."
}}

Query: "Compare traffic between HTTPS and HTTP pages"
Output:
{{
  "analytics_query": "What is the total traffic (page views and users) for all pages? Include page URLs.",
  "seo_query": "Which pages use HTTP vs HTTPS? Include page URLs and protocol."
}}

Query: "Top 5 pages by traffic and their indexability status"
Output:
{{
  "analytics_query": "What are the top 5 pages by page views in the last 30 days? Include page URLs.",
  "seo_query": "What is the indexability status for all pages? Include page URLs and indexability."
}}

=== USER QUERY ===

{query}

=== YOUR TASK ===

Decompose this query into two focused sub-queries. Think through:
1. What traffic/performance data is needed? (Analytics query)
2. What technical SEO data is needed? (SEO query)
3. How will the results be joined? (both should reference page URLs)
4. Are there time periods, filters, or rankings mentioned?

Provide your response as JSON:
{{
  "analytics_query": "Focused query for GA4 analytics data (traffic, users, views, etc.)",
  "seo_query": "Focused query for SEO technical audit data (titles, meta, HTTPS, indexability, etc.)"
}}

Respond with ONLY the JSON, no explanatory text."""

        response = llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response = response[json_start:json_end]
            
            return json.loads(response)
        except:
            return {
                'analytics_query': query,
                'seo_query': query
            }
    
    def aggregate_results(
        self, 
        original_query: str,
        analytics_result: Optional[str] = None,
        seo_result: Optional[str] = None
    ) -> str:
        """
        Aggregate results from multiple agents into a unified response.
        
        Args:
            original_query: Original user query
            analytics_result: Response from analytics agent
            seo_result: Response from SEO agent
            
        Returns:
            Unified natural language response
        """
        prompt = f"""You are an expert data analyst specializing in cross-domain insights. Synthesize analytics and SEO data into a unified, actionable answer.

=== USER'S ORIGINAL QUESTION ===
{original_query}

=== ANALYTICS DATA (Google Analytics 4) ===
{analytics_result if analytics_result else 'Analytics data not available'}

=== SEO AUDIT DATA (Screaming Frog) ===
{seo_result if seo_result else 'SEO data not available'}

=== YOUR TASK ===

Combine these two data sources into a comprehensive answer with this structure:

1. EXECUTIVE SUMMARY (2-3 sentences)
   - Direct answer combining both sources
   - Example: "Your top 5 pages generated 45,234 views last month. Of these, 3 have optimized title tags under 60 characters, while 2 exceed the limit."

2. DETAILED FINDINGS (by page or category)
   - Match analytics performance with SEO attributes
   - Use clear formatting (numbered list or table-like)
   - Example: "1. Homepage (/): 12,445 views, Title: 'Welcome' (23 chars, \u2713 Optimized)"

3. CROSS-DOMAIN INSIGHTS (2-3 points)
   - Correlations between traffic and SEO health
   - Opportunities or risks
   - Example: "Your highest-traffic page has a title 12% too long, potentially reducing CTR."

4. RECOMMENDATIONS (2-4 actions, prioritized)
   - Specific, actionable steps
   - Prioritize by impact (high-traffic + SEO issues = top priority)
   - Example: "Priority 1: Shorten /pricing title from 67 to 58 characters."

=== STYLE ===
- Use SPECIFIC NUMBERS from both sources
- Connect traffic metrics with SEO attributes
- Use \u2713 \u26a0 \u2717 for visual clarity
- Highlight high-traffic pages with SEO issues (biggest opportunities)
- Be conversational but data-driven
- Calculate percentages when adding value

If user requested JSON format, provide structured JSON. Otherwise, use natural language."""

        response = llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000
        )
        
        return response
