#!/bin/bash

# deploy.sh - Deployment script for Spike AI Backend
# This script sets up the environment and starts the server

echo "======================================"
echo "Spike AI Backend Deployment"
echo "======================================"

# Check Python version
echo "Checking Python version..."
python --version 2>/dev/null || python3 --version || {
    echo "Python not found. Please install Python 3.8+"
    exit 1
}

# Create virtual environment at repository root
echo "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python -m venv .venv 2>/dev/null || python3 -m venv .venv || {
        echo "Failed to create virtual environment"
        exit 1
    }
fi

# Activate virtual environment (Windows/Linux compatible)
echo "Activating virtual environment..."
if [ -f ".venv/Scripts/activate" ]; then
    # Windows Git Bash
    . .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    # Linux/Mac
    . .venv/bin/activate
fi

# Install uv if not already installed
echo "Checking for uv..."
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    pip install uv 2>/dev/null || python -m pip install uv
fi

# Install dependencies using uv
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Check for credentials.json
if [ ! -f "credentials.json" ]; then
    echo "WARNING: credentials.json not found. Please ensure it exists at the repository root."
    echo "Creating placeholder credentials.json..."
    cat > credentials.json <<EOF
{
  "type": "service_account",
  "project_id": "placeholder-project",
  "private_key_id": "placeholder",
  "private_key": "-----BEGIN PRIVATE KEY-----\nPLACEHOLDER\n-----END PRIVATE KEY-----\n",
  "client_email": "placeholder@placeholder.iam.gserviceaccount.com",
  "client_id": "placeholder",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "placeholder"
}
EOF
fi

# Set environment variable
export LITELLM_API_KEY="${LITELLM_API_KEY:-sk-itE0QuhkM_Gb1fZ1MGl53g}"

# Start the server in the background
echo "Starting server on port 8080..."
python main.py > server.log 2>&1 &

# Save PID
SERVER_PID=$!
echo $SERVER_PID > server.pid

# Wait for server to start (cross-platform)
echo "Waiting for server to initialize..."
python -c "import time; time.sleep(3)" 2>/dev/null || {
    # Fallback if python not in path
    for i in 1 2 3; do
        echo -n "."
    done
    echo ""
}

echo ""
echo "✓ Server process started (PID: $SERVER_PID)"
echo "✓ Server should be running on http://0.0.0.0:8080"
echo "✓ Logs are being written to server.log"
echo ""
echo "To verify server is running:"
echo "  curl http://localhost:8080/health"
echo ""
echo "To test queries:"
echo "  python terminal_query.py \"How many users visited last week?\""
echo ""
echo "To stop the server:"
echo "  kill \$(cat server.pid)  # Linux/Mac"
echo "  taskkill //PID $SERVER_PID //F  # Windows"

echo ""
echo "======================================"
echo "Deployment Complete"
echo "======================================"
