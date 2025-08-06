#!/bin/bash
# Test Runner Script for Commission Calculator Pro

set -e  # Exit on any error

echo "🧪 Commission Calculator Pro - Test Suite Runner"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements_api.txt
pip install -q pytest

# Check if API server is running
echo "🌐 Checking API server status..."
API_RUNNING=false
if curl -s http://127.0.0.1:8504/health > /dev/null 2>&1; then
    echo "✅ API server is running"
    API_RUNNING=true
else
    echo "🚀 Starting API server..."
    python api_server.py &
    API_PID=$!
    
    # Wait for API server to start
    for i in {1..10}; do
        if curl -s http://127.0.0.1:8504/health > /dev/null 2>&1; then
            echo "✅ API server started successfully"
            API_RUNNING=true
            break
        fi
        echo "⏳ Waiting for API server... ($i/10)"
        sleep 2
    done
fi

if [ "$API_RUNNING" = false ]; then
    echo "❌ Failed to start API server"
    exit 1
fi

# Run tests
echo "🧪 Running test suite..."
python test_commission_calculator.py

TEST_RESULT=$?

# Cleanup if we started the API server
if [ ! -z "$API_PID" ]; then
    echo "🛑 Stopping API server..."
    kill $API_PID 2>/dev/null || true
fi

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed successfully!"
    echo "✅ Commission Calculator Pro is ready for deployment"
else
    echo ""
    echo "❌ Test suite failed"
    echo "🔧 Please fix the failing tests before deployment"
    exit 1
fi