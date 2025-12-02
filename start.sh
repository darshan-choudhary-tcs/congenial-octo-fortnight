#!/bin/bash

# RAG & Multi-Agent System - Quick Start Script
# This script sets up and runs both backend and frontend

set -e

echo "🚀 RAG & Multi-Agent System - Quick Start"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Ollama status
echo "🔍 Checking Ollama..."
if lsof -Pi :11434 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✅ Ollama is running on port 11434${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama is NOT running${NC}"
    echo -e "${BLUE}   To start Ollama:${NC}"
    echo "   1. brew install ollama (if not installed)"
    echo "   2. ollama pull llama3.2"
    echo "   3. ollama serve"
    echo ""
fi

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Backend is already running on port 8000${NC}"
else
    echo "📦 Starting Backend..."
    cd backend

    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ Virtual environment not found. Run setup.sh first.${NC}"
        exit 1
    fi

    # Start backend in background
    uvicorn main:app --reload --port 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    echo "   Logs: backend.log"
    echo "   API Docs: http://localhost:8000/docs"
    cd ..
fi

# Check if frontend is already running
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Frontend is already running on port 3000${NC}"
else
    echo ""
    echo "🎨 Starting Frontend..."
    cd frontend

    # Start frontend in background
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    echo "   Logs: frontend.log"
    echo "   App: http://localhost:3000"
    cd ..
fi

echo ""
echo "=========================================="
echo -e "${GREEN}🎉 System is ready!${NC}"
echo ""
echo "📱 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "👤 Default Login Credentials:"
echo "   Admin:"
echo "     Username: admin"
echo "     Password: admin123"
echo ""
echo "   Analyst:"
echo "     Username: analyst1"
echo "     Password: password123"
echo ""
echo "   Viewer:"
echo "     Username: viewer1"
echo "     Password: password123"
echo ""
echo "📝 Logs:"
echo "   Backend: tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop the servers:"
echo "   Kill backend: kill $BACKEND_PID"
echo "   Kill frontend: kill $FRONTEND_PID"
echo "   Or run: ./stop.sh"
echo ""
echo "=========================================="
