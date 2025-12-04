#!/bin/bash

# Streamlit Admin Application Runner
# Quick start script for the admin dashboard

echo "🎛️  Starting Streamlit Admin Dashboard..."
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

# Check if backend is running
echo "🔍 Checking backend availability..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Backend is running at http://localhost:8000"
else
    echo "⚠️  Warning: Backend may not be running"
    echo "   Start backend with: cd backend && python main.py"
    echo ""
fi

# Check if database exists
if [ -f "../backend/data/data_store.db" ]; then
    echo "✅ Database found at ../backend/data/data_store.db"
else
    echo "⚠️  Warning: Database not found at backend/data/data_store.db"
    echo "   Initialize backend first to create the database"
    echo ""
fi

# Check if requirements are installed
echo ""
echo "📦 Checking dependencies..."
if python3 -c "import streamlit" 2>/dev/null; then
    echo "✅ Streamlit is installed"
else
    echo "❌ Streamlit is not installed"
    echo "   Installing dependencies..."
    pip install -r requirements_streamlit.txt
fi

echo ""
echo "================================================"
echo "🚀 Launching Streamlit Admin Dashboard..."
echo "================================================"
echo ""
echo "📝 Login Credentials:"
echo "   Admin:   admin / admin123"
echo "   Analyst: analyst1 / analyst123"
echo "   Viewer:  viewer1 / viewer123"
echo ""
echo "🌐 The app will open at http://localhost:8501"
echo "Press Ctrl+C to stop the application"
echo ""

# Run Streamlit
streamlit run main.py
