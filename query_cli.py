#!/usr/bin/env python3
"""
CLI tool for querying the Spike AI Backend.
Usage: python query_cli.py
"""

import requests
import json
import sys
from typing import Optional

def query_backend(query: str, property_id: Optional[str] = None, base_url: str = "http://localhost:8080") -> dict:
    """
    Send a query to the backend API.
    
    Args:
        query: Natural language query
        property_id: Optional GA4 property ID
        base_url: Backend server URL
        
    Returns:
        Response dictionary
    """
    url = f"{base_url}/query"
    payload = {
        "query": query,
        "propertyId": property_id or ""
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server. Is the server running on port 8080?")
        print("   Start the server with: python main.py")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out after 120 seconds.")
        print("   The query may be too complex. Try a simpler query.")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def check_server_health(base_url: str = "http://localhost:8080") -> bool:
    """Check if the server is running."""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def print_response(response: dict):
    """Pretty print the response."""
    print("\n" + "┌" + "─"*68 + "┐")
    print("│" + " 🤖  AI RESPONSE".ljust(68) + "│")
    print("└" + "─"*68 + "┘\n")
    
    response_text = response.get("response", "No response")
    
    # Print response with nice formatting
    for line in response_text.split('\n'):
        print(line)
    
    print("\n" + "─"*70)

def interactive_mode():
    """Run in interactive mode."""
    # Clear screen for better presentation
    print("\033[2J\033[H", end="")
    
    print("\n" + "="*70)
    print(" 🤖  SPIKE AI BACKEND - INTERACTIVE QUERY INTERFACE")
    print("="*70 + "\n")
    
    # Check server health
    print("⏳ Checking server status...", end=" ", flush=True)
    if check_server_health():
        print("✅ Server is running!\n")
    else:
        print("❌ Server not responding\n")
        print("┌─────────────────────────────────────────────────────────────┐")
        print("│  Please start the server first:                            │")
        print("│                                                             │")
        print("│  Option 1: Start manually                                  │")
        print("│    → python main.py                                        │")
        print("│                                                             │")
        print("│  Option 2: Use deployment script                           │")
        print("│    → bash deploy.sh                                        │")
        print("└─────────────────────────────────────────────────────────────┘\n")
        sys.exit(1)
    
    # Get property ID (optional)
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│  STEP 1: Configuration (Optional)                          │")
    print("└─────────────────────────────────────────────────────────────┘\n")
    print("Do you have a GA4 Property ID for analytics queries?")
    print("  • Enter your Property ID for analytics + SEO queries")
    print("  • Press ENTER to skip (SEO queries only)\n")
    property_id = input("📊 GA4 Property ID (or press Enter): ").strip()
    
    print()
    if not property_id:
        print("✓ Configuration: SEO Mode")
        print("\n┌─────────────────────────────────────────────────────────────┐")
        print("│  💡 What you can ask:                                      │")
        print("│                                                             │")
        print("│  ✓ Show me all accessibility violations                   │")
        print("│  ✓ List pages with their status codes                     │")
        print("│  ✓ What are the main WCAG issues?                         │")
        print("│  ✓ Which pages have SEO problems?                         │")
        print("└─────────────────────────────────────────────────────────────┘\n")
    else:
        print(f"✓ Configuration: Analytics + SEO Mode")
        print(f"✓ Property ID: {property_id}")
        print("\n┌─────────────────────────────────────────────────────────────┐")
        print("│  💡 What you can ask:                                      │")
        print("│                                                             │")
        print("│  📊 Analytics:                                             │")
        print("│     → How many users visited last week?                    │")
        print("│     → Show me top pages by traffic                         │")
        print("│     → What's my bounce rate by device?                     │")
        print("│                                                             │")
        print("│  🔍 SEO:                                                   │")
        print("│     → Show me accessibility violations                     │")
        print("│     → List pages with status codes                         │")
        print("│                                                             │")
        print("│  🔄 Combined:                                              │")
        print("│     → Analyze traffic AND SEO problems                     │")
        print("│     → Show high-traffic pages with issues                  │")
        print("└─────────────────────────────────────────────────────────────┘\n")
    
    print("="*70)
    print(" 📝  READY TO ANSWER YOUR QUESTIONS!")
    print("="*70)
    print("\n💬 Type your question below and press Enter")
    print("⚡ Commands: 'help' for tips, 'quit' to exit\n")
    
    query_count = 0
    
    while True:
        try:
            # Get query with user-friendly prompt
            print("─" * 70)
            query = input(f"\n💬 Your Question #{query_count + 1}: ").strip()
            
            if not query:
                print("⚠️  Please enter a question or type 'quit' to exit")
                continue
                
            if query.lower() in ['quit', 'exit', 'q', 'bye']:
                print("\n" + "="*70)
                print("  👋  Thank you for using Spike AI Backend!")
                print("="*70 + "\n")
                break
            
            # Special commands
            if query.lower() == 'help':
                print("\n┌─────────────────────────────────────────────────────────────┐")
                print("│  ⚡ QUICK COMMANDS                                          │")
                print("├─────────────────────────────────────────────────────────────┤")
                print("│  help      → Show this help message                        │")
                print("│  examples  → Show example queries                          │")
                print("│  clear     → Clear the screen                              │")
                print("│  status    → Check server health                           │")
                print("│  property  → Change GA4 Property ID                        │")
                print("│  quit      → Exit the application                          │")
                print("└─────────────────────────────────────────────────────────────┘\n")
                continue
            
            if query.lower() == 'examples':
                print("\n┌─────────────────────────────────────────────────────────────┐")
                print("│  📝 EXAMPLE QUESTIONS                                       │")
                print("├─────────────────────────────────────────────────────────────┤")
                if property_id:
                    print("│  📊 Analytics:                                             │")
                    print("│    • How many users visited my site last week?            │")
                    print("│    • Show me page views by traffic source                 │")
                    print("│    • What's the bounce rate for mobile users?             │")
                    print("│                                                             │")
                print("│  🔍 SEO & Accessibility:                                   │")
                print("│    • Show me all accessibility violations                   │")
                print("│    • List pages with their HTTP status codes                │")
                print("│    • What WCAG issues were found?                           │")
                print("│    • Which pages have 200 OK status?                        │")
                if property_id:
                    print("│                                                             │")
                    print("│  🔄 Combined Analysis:                                     │")
                    print("│    • Analyze traffic patterns AND SEO issues               │")
                    print("│    • Show high traffic pages with accessibility problems   │")
                print("└─────────────────────────────────────────────────────────────┘\n")
                continue
            
            if query.lower() == 'clear':
                print("\033[2J\033[H")  # Clear screen
                print("✨ Screen cleared!\n")
                continue
                
            if query.lower() == 'status':
                print("\n⏳ Checking server...", end=" ", flush=True)
                if check_server_health():
                    print("✅ Server is running and healthy!")
                else:
                    print("❌ Server is not responding")
                continue
                
            if query.lower() == 'property':
                print("\n📊 Current Property ID:", property_id or "(not set)")
                new_property_id = input("🔄 Enter new Property ID (or press Enter to keep current): ").strip()
                if new_property_id:
                    property_id = new_property_id
                    print(f"✅ Property ID updated to: {property_id}")
                else:
                    print("ℹ️  Property ID unchanged")
                continue
            
            # Send query
            print("\n" + "─"*70)
            print("⏳ Processing your question...")
            print("─"*70)
            result = query_backend(query, property_id)
            print_response(result)
            query_count += 1
            
            # Show friendly prompt for next question
            print("💡 Ask another question, or type 'quit' to exit")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

def single_query_mode(query: str, property_id: Optional[str] = None):
    """Run a single query and exit."""
    print("\n" + "="*70)
    print(" 🤖  SPIKE AI BACKEND - SINGLE QUERY MODE")
    print("="*70 + "\n")
    
    print("⏳ Checking server...", end=" ", flush=True)
    if not check_server_health():
        print("❌ Not running\n")
        print("┌─────────────────────────────────────────────────────────────┐")
        print("│  Server is not running on port 8080                        │")
        print("│  Start with: python main.py                                │")
        print("└─────────────────────────────────────────────────────────────┘\n")
        sys.exit(1)
    print("✅ Running\n")
    
    print(f"📝 Your Question: {query}")
    if property_id:
        print(f"📊 Property ID: {property_id}")
    print("\n⏳ Processing your question...\n")
    
    result = query_backend(query, property_id)
    print_response(result)

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Single query mode
        query = " ".join(sys.argv[1:])
        single_query_mode(query)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
