#!/bin/bash
# Startup script for Commission Calculator Pro

echo "🚀 Starting Commission Calculator Pro"
echo "====================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️ Virtual environment not found. Creating..."
    python3 -m venv venv
    
    # Activate and install dependencies
    source venv/bin/activate
    echo "📦 Installing dependencies in virtual environment..."
    pip install streamlit pandas plotly openpyxl
else
    echo "✅ Virtual environment found"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if streamlit is available in venv
if ! python -c "import streamlit" &> /dev/null; then
    echo "⚠️ Streamlit not found in venv. Installing..."
    pip install streamlit pandas plotly openpyxl
fi

echo "✅ All dependencies available in virtual environment"

# Test core logic first
echo "🧪 Testing core logic..."
if python test_core_logic.py; then
    echo "✅ Core logic test passed"
else
    echo "❌ Core logic test failed"
    exit 1
fi

# Find available port
echo "🔍 Finding available port..."
PORT=8501
for p in 8501 8502 8505 8506 8507; do
    if ! netstat -tuln 2>/dev/null | grep -q ":$p "; then
        PORT=$p
        break
    fi
done

echo "✅ Using port: $PORT"

# Start the Streamlit app
echo "🌐 Starting Streamlit server..."
echo "📍 URL: http://localhost:$PORT"
echo "⚠️ Press Ctrl+C to stop the server"
echo ""

# Run streamlit with specific configuration
python -m streamlit run working_main_app.py \
    --server.port $PORT \
    --server.address 127.0.0.1 \
    --server.headless true \
    --browser.gatherUsageStats false