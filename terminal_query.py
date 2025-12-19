#!/usr/bin/env python3
"""Simple terminal query interface for Spike AI Backend."""

import requests
import sys
import json

API_URL = "http://localhost:8080/query"
API_STREAM_URL = "http://localhost:8080/query/stream"

def send_query(query, property_id=None, stream=False):
    """Send query and display response."""
    payload = {"query": query}
    if property_id:
        payload["propertyId"] = property_id
    
    try:
        if stream:
            # Use streaming endpoint for real-time updates
            try:
                response = requests.post(
                    API_STREAM_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    stream=True,
                    timeout=120
                )
                
                print("\n" + "="*60)
                has_response = False
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data = json.loads(line_str[6:])
                            
                            if 'error' in data:
                                print(f"\n❌ Error: {data['error']}")
                                return
                            
                            if 'status' in data:
                                step = data.get('step', 0)
                                status = data['status']
                                
                                if step == 5:
                                    print(f"\n✅ {status}\n")
                                    print("="*60)
                                    print("\nResponse:")
                                    print("-"*60)
                                    print(data.get('response', ''))
                                    print("="*60 + "\n")
                                    has_response = True
                                else:
                                    print(f"⏳ Step {step}/5: {status}")
                
                if not has_response:
                    print("⚠️  No response received from streaming endpoint, falling back to regular endpoint...\n")
                    stream = False
            except Exception as e:
                print(f"⚠️  Streaming failed ({e}), falling back to regular endpoint...\n")
                stream = False
        
        if not stream:
            # Use regular endpoint
            response = requests.post(
                API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                print("\n" + "="*60)
                print("Response:")
                print("-"*60)
                print(result.get('response', ''))
                print("="*60 + "\n")
            else:
                print(f"\n❌ Error: HTTP {response.status_code}")
                print(response.text + "\n")
                
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

def main():
    """Interactive terminal query interface."""
    print("="*60)
    print("🚀 Spike AI Backend - Terminal Interface")
    print("="*60)
    print("\nℹ️  Property ID (516815205) is configured by default.")
    print("    The AI will automatically decide whether to use it based on your query.")
    print("\nCommands:")
    print("  - Type your query and press Enter")
    print("  - Type 'quit' or 'exit' to quit")
    print("  - Type 'property <ID>' to override default property ID (optional)")
    print("  - Type 'stream on/off' to toggle streaming")
    print("="*60 + "\n")
    
    property_id = "516815205"  # Default property ID, always available
    stream_enabled = False  # Disabled by default for stability
    
    while True:
        try:
            query = input("Query> ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if query.lower().startswith('property '):
                property_id = query.split(maxsplit=1)[1]
                print(f"✅ Property ID set to: {property_id}\n")
                continue
            
            if query.lower() == 'stream on':
                stream_enabled = True
                print("✅ Streaming enabled\n")
                continue
            
            if query.lower() == 'stream off':
                stream_enabled = False
                print("✅ Streaming disabled\n")
                continue
            
            send_query(query, property_id, stream_enabled)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye!\n")
            break

if __name__ == "__main__":
    # Check if query provided as command-line argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        send_query(query)
    else:
        main()
