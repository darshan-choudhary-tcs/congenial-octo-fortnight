#!/bin/bash

# Quick Start Script for RAG & Multi-Agent System

echo "🚀 RAG & Multi-Agent System - Quick Start"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Backend Setup
echo "📦 Setting up Backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env and add your CUSTOM_LLM_API_KEY"
    read -p "Press Enter to continue..."
fi

echo "✅ Backend setup complete"
echo ""

# Frontend Setup
echo "📦 Setting up Frontend..."
cd ../frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
fi

echo "✅ Frontend setup complete"
echo ""

# Return to root
cd ..

echo "=========================================="
echo "✨ Setup Complete!"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Backend Configuration:"
echo "   - Edit backend/.env and add your CUSTOM_LLM_API_KEY"
echo "   - (Optional) Configure Ollama settings if using local LLM"
echo ""
echo "2. Start the Backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "3. Generate Synthetic Data (in another terminal):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python scripts/generate_synthetic_data.py"
echo ""
echo "4. Start the Frontend (in another terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "5. Access the Application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "6. Login with demo accounts:"
echo "   Admin: admin / admin123"
echo "   Analyst: analyst1 / analyst123"
echo "   Viewer: viewer1 / viewer123"
echo ""
echo "=========================================="
