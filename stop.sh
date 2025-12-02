#!/bin/bash

# RAG & Multi-Agent System - Stop Script

echo "🛑 Stopping RAG & Multi-Agent System..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Stop backend on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "Stopping backend (port 8000)..."
    kill $(lsof -t -i:8000)
    echo -e "${GREEN}✅ Backend stopped${NC}"
else
    echo -e "${RED}❌ Backend is not running${NC}"
fi

# Stop frontend on port 3000
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "Stopping frontend (port 3000)..."
    kill $(lsof -t -i:3000)
    echo -e "${GREEN}✅ Frontend stopped${NC}"
else
    echo -e "${RED}❌ Frontend is not running${NC}"
fi

echo ""
echo "✨ All services stopped"
