"""Streamlit UI for testing Spike AI Backend."""

import streamlit as st
import requests
import json
import time

# Configuration
API_URL = "http://localhost:8080/query"
API_STREAM_URL = "http://localhost:8080/query/stream"
HEALTH_URL = "http://localhost:8080/health"

# Page config
st.set_page_config(
    page_title="Spike AI Backend Test Dashboard",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .test-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background: white;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'test_results' not in st.session_state:
    st.session_state.test_results = []
if 'total_queries' not in st.session_state:
    st.session_state.total_queries = 0
if 'successful_queries' not in st.session_state:
    st.session_state.successful_queries = 0

# Header
st.title("🚀 Spike AI Backend - Test Dashboard")
st.markdown("**Production-ready AI backend for Analytics & SEO queries**")

# Server status check
def check_server_status():
    try:
        response = requests.get(HEALTH_URL, timeout=2)
        if response.status_code == 200:
            return True, "✅ Server Online"
    except:
        pass
    return False, "❌ Server Offline"

is_online, status_text = check_server_status()
if is_online:
    st.success(status_text)
else:
    st.error(status_text + " - Please start the server with `python main.py`")
    st.stop()

# Sidebar - Test Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    property_id = st.text_input(
        "GA4 Property ID",
        value="516815205",
        help="Your Google Analytics 4 Property ID"
    )
    
    st.divider()
    
    st.header("📊 Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Queries", st.session_state.total_queries)
    with col2:
        success_rate = 0
        if st.session_state.total_queries > 0:
            success_rate = (st.session_state.successful_queries / st.session_state.total_queries) * 100
        st.metric("Success Rate", f"{success_rate:.0f}%")
    
    st.divider()
    
    if st.button("🗑️ Clear Results", use_container_width=True):
        st.session_state.test_results = []
        st.session_state.total_queries = 0
        st.session_state.successful_queries = 0
        st.rerun()

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🧪 Quick Tests",
    "💬 Custom Query", 
    "📋 Test Results",
    "📖 Sample Queries"
])

def send_query(query, include_property_id=False, status_container=None):
    """Send a query to the API with real-time streaming progress."""
    try:
        payload = {"query": query}
        if include_property_id:
            payload["propertyId"] = property_id
        
        start_time = time.time()
        
        # Use streaming endpoint for real-time updates
        response = requests.post(
            API_STREAM_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=120
        )
        
        final_response = None
        
        # Process Server-Sent Events stream
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    
                    if 'error' in data:
                        if status_container:
                            status_container.error(f"❌ Error: {data['error']}")
                        return False, data['error'], 0
                    
                    if 'status' in data and status_container:
                        step = data.get('step', 0)
                        status = data['status']
                        
                        if step == 1:
                            status_container.info(f"🤔 **Step {step}/5:** {status}")
                        elif step == 2:
                            status_container.info(f"🎯 **Step {step}/5:** {status}")
                        elif step == 3:
                            status_container.info(f"🔄 **Step {step}/5:** {status}")
                        elif step == 4:
                            status_container.info(f"⚡ **Step {step}/5:** {status}")
                        elif step == 5:
                            elapsed_time = time.time() - start_time
                            status_container.success(f"✅ **{status}** Query finished in {elapsed_time:.2f}s")
                            final_response = data.get('response', '')
        
        elapsed_time = time.time() - start_time
        
        if final_response:
            st.session_state.total_queries += 1
            st.session_state.successful_queries += 1
            st.session_state.test_results.insert(0, {
                "query": query,
                "response": final_response,
                "time": f"{elapsed_time:.2f}s",
                "status": "success",
                "timestamp": time.strftime("%H:%M:%S")
            })
            
            return True, final_response, elapsed_time
        else:
            st.session_state.total_queries += 1
            error_msg = "No response received from server"
            st.session_state.test_results.insert(0, {
                "query": query,
                "response": error_msg,
                "time": f"{elapsed_time:.2f}s",
                "status": "error",
                "timestamp": time.strftime("%H:%M:%S")
            })
            
            if status_container:
                status_container.error(f"❌ Error: {error_msg}")
            
            return False, error_msg, elapsed_time
    except Exception as e:
        st.session_state.total_queries += 1
        error_msg = f"Error: {str(e)}"
        st.session_state.test_results.insert(0, {
            "query": query,
            "response": error_msg,
            "time": "N/A",
            "status": "error",
            "timestamp": time.strftime("%H:%M:%S")
        })
        
        if status_container:
            status_container.error(f"❌ Error: {error_msg}")
        
        return False, error_msg, 0

# Tab 1: Quick Tests
with tab1:
    st.header("Quick Test Queries")
    st.markdown("Click any button to test that specific query type. The system will **automatically route** to the correct agent.")
    
    # Tier 1: Analytics
    st.subheader("🎯 Tier 1 - Analytics Agent (GA4)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Daily Metrics", use_container_width=True):
            status_placeholder = st.empty()
            success, response, elapsed = send_query(
                "Give me a daily breakdown of page views, users, and sessions for the /pricing page over the last 14 days.",
                include_property_id=True,
                status_container=status_placeholder
            )
            if success:
                st.text_area("Response:", response, height=300)
            else:
                st.error(response)
    
    with col2:
        if st.button("🔍 Traffic Sources", use_container_width=True):
            status_placeholder = st.empty()
            success, response, elapsed = send_query(
                "What are the top 5 traffic sources driving users to the pricing page in the last 30 days?",
                include_property_id=True,
                status_container=status_placeholder
            )
            if success:
                st.text_area("Response:", response, height=300)
            else:
                st.error(response)
    
    with col3:
        if st.button("📈 Trend Analysis", use_container_width=True):
            with st.spinner("Querying..."):
                success, response, elapsed = send_query(
                    "Calculate the average daily page views for the homepage over the last 30 days.",
                    include_property_id=True
                )
                if success:
                    st.success(f"✅ Query completed in {elapsed:.2f}s")
                    st.text_area("Response:", response, height=300)
                else:
                    st.error(response)
    
    st.divider()
    
    # Tier 2: SEO
    st.subheader("🔍 Tier 2 - SEO Agent (Screaming Frog)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔒 HTTPS Check", use_container_width=True):
            with st.spinner("Querying..."):
                success, response, elapsed = send_query(
                    "Which URLs do not use HTTPS and have title tags longer than 60 characters?"
                )
                if success:
                    st.success(f"✅ Query completed in {elapsed:.2f}s")
                    st.text_area("Response:", response, height=300)
                else:
                    st.error(response)
    
    with col2:
        if st.button("📋 Indexability", use_container_width=True):
            with st.spinner("Querying..."):
                success, response, elapsed = send_query(
                    "Group all pages by indexability status and provide a count for each group with a brief explanation."
                )
                if success:
                    st.success(f"✅ Query completed in {elapsed:.2f}s")
                    st.text_area("Response:", response, height=300)
                else:
                    st.error(response)
    
    with col3:
        if st.button("💯 SEO Health", use_container_width=True):
            with st.spinner("Querying..."):
                success, response, elapsed = send_query(
                    "Calculate the percentage of indexable pages on the site and assess SEO health."
                )
                if success:
                    st.success(f"✅ Query completed in {elapsed:.2f}s")
                    st.text_area("Response:", response, height=300)
                else:
                    st.error(response)
    
    st.divider()
    
    # Tier 3: Multi-Agent
    st.subheader("🤖 Tier 3 - Multi-Agent System")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔗 Analytics + SEO Fusion", use_container_width=True):
            with st.spinner("Querying..."):
                success, response, elapsed = send_query(
                    "What are the top 10 pages by page views in the last 30 days, and what are their corresponding title tags?",
                    include_property_id=True
                )
                if success:
                    st.success(f"✅ Query completed in {elapsed:.2f}s")
                    st.text_area("Response:", response, height=300)
                else:
                    st.error(response)
    
    with col2:
        if st.button("⚠️ High Traffic Risks", use_container_width=True):
            with st.spinner("Querying..."):
                success, response, elapsed = send_query(
                    "Which pages are in the top 20% by views but have missing or duplicate meta descriptions?",
                    include_property_id=True
                )
                if success:
                    st.success(f"✅ Query completed in {elapsed:.2f}s")
                    st.text_area("Response:", response, height=300)
                else:
                    st.error(response)
    
    with col3:
        if st.button("📊 JSON Output", use_container_width=True):
            with st.spinner("Querying..."):
                success, response, elapsed = send_query(
                    "Return the top 5 pages by views along with their title tags and indexability status in JSON format.",
                    include_property_id=True
                )
                if success:
                    st.success(f"✅ Query completed in {elapsed:.2f}s")
                    st.text_area("Response:", response, height=300)
                else:
                    st.error(response)

# Tab 2: Custom Query
with tab2:
    st.header("Custom Query")
    st.markdown("**The orchestrator automatically detects intent and routes to the correct agent(s).**")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        custom_query = st.text_area(
            "Enter your natural language question:",
            placeholder="Ask anything about analytics or SEO...\nExamples:\n- How many users visited my site last week?\n- Which pages have missing meta descriptions?\n- What are the top pages by views and their SEO status?",
            height=150
        )
    
    with col2:
        st.write("")
        st.write("")
        include_property = st.checkbox("Include GA4 Property ID", value=False, help="Check this if your query involves analytics data")
    
    if st.button("🚀 Send Query", type="primary", use_container_width=True):
        if not custom_query.strip():
            st.warning("Please enter a query")
        else:
            with st.spinner("Processing your query..."):
                success, response, elapsed = send_query(custom_query, include_property_id=include_property)
                
                if success:
                    st.success(f"✅ Query completed in {elapsed:.2f}s")
                    
                    # Display response in an expander
                    with st.expander("📄 Full Response", expanded=True):
                        st.markdown(response)
                else:
                    st.error("❌ Query failed")
                    st.error(response)

# Tab 3: Test Results
with tab3:
    st.header("Test Results History")
    
    if not st.session_state.test_results:
        st.info("No test results yet. Run some queries to see results here!")
    else:
        for idx, result in enumerate(st.session_state.test_results):
            status_icon = "✅" if result["status"] == "success" else "❌"
            
            with st.expander(f"{status_icon} [{result['timestamp']}] {result['query'][:80]}...", expanded=(idx==0)):
                st.markdown(f"**Query:** {result['query']}")
                st.markdown(f"**Time:** {result['time']}")
                st.markdown(f"**Status:** {result['status'].upper()}")
                st.divider()
                st.markdown("**Response:**")
                st.text_area("Response", result['response'], height=200, key=f"result_{idx}", label_visibility="collapsed")

# Tab 4: Sample Queries
with tab4:
    st.header("📖 Sample Test Queries")
    st.markdown("These are the official test queries from the hackathon problem statement.")
    
    st.subheader("Tier 1 - Analytics Agent (GA4)")
    st.code("""
1. Give me a daily breakdown of page views, users, and sessions for the /pricing page over the last 14 days. Summarize any noticeable trends.

2. What are the top 5 traffic sources driving users to the pricing page in the last 30 days?

3. Calculate the average daily page views for the homepage over the last 30 days. Compare it to the previous 30-day period and explain whether traffic is increasing or decreasing.
    """)
    
    st.subheader("Tier 2 - SEO Agent (Screaming Frog)")
    st.code("""
1. Which URLs do not use HTTPS and have title tags longer than 60 characters?

2. Group all pages by indexability status and provide a count for each group with a brief explanation.

3. Calculate the percentage of indexable pages on the site. Based on this number, assess whether the site's technical SEO health is good, average, or poor.
    """)
    
    st.subheader("Tier 3 - Multi-Agent System")
    st.code("""
1. What are the top 10 pages by page views in the last 30 days, and what are their corresponding title tags?

2. Which pages are in the top 20% by views but have missing or duplicate meta descriptions? Explain the SEO risk.

3. Return the top 5 pages by views along with their title tags and indexability status in JSON format.
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>Spike AI Backend Test Dashboard | Port 8080 | Automatic Agent Routing ✨</small>
</div>
""", unsafe_allow_html=True)
