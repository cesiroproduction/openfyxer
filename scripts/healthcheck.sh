#!/bin/bash
# Health check script for OpenFyxer services

echo "OpenFyxer Health Check"
echo "======================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    local expected=$3
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" == "$expected" ]; then
        echo -e "${GREEN}[OK]${NC} $name is running"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $name is not responding (got $response, expected $expected)"
        return 1
    fi
}

check_port() {
    local name=$1
    local port=$2
    
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}[OK]${NC} $name port $port is open"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $name port $port is not accessible"
        return 1
    fi
}

echo ""
echo "Checking services..."
echo ""

# Check Backend API
check_service "Backend API" "http://localhost:8000/health" "200"

# Check Frontend
check_service "Frontend" "http://localhost:3000" "200"

# Check PostgreSQL
check_port "PostgreSQL" "5432"

# Check Neo4j HTTP
check_service "Neo4j Browser" "http://localhost:7474" "200"

# Check Neo4j Bolt
check_port "Neo4j Bolt" "7687"

# Check Redis
check_port "Redis" "6379"

# Check Ollama (if running)
check_service "Ollama" "http://localhost:11434/api/tags" "200" 2>/dev/null || echo -e "${YELLOW}[WARN]${NC} Ollama not running (optional for local LLM)"

echo ""
echo "======================"

# Summary
echo ""
echo "Quick Links:"
echo "  Frontend:     http://localhost:3000"
echo "  Backend API:  http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Neo4j:        http://localhost:7474"
echo ""
