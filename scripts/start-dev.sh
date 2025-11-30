#!/bin/bash

################################################################################
# PixCrawler Development Startup Script (Unix/Linux/Mac)
################################################################################
# This script starts both the backend (FastAPI) and frontend (Next.js) services
# for local development with a single command.
#
# Usage:
#   ./scripts/start-dev.sh
#
# Requirements:
#   - Python 3.11+
#   - Node.js 18+
#   - Redis server
#   - PostgreSQL (Supabase)
#   - UV package manager
#   - Bun package manager
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Process IDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

################################################################################
# Cleanup Function
################################################################################

cleanup() {
    echo ""
    print_header "Shutting Down Services"
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_info "Stopping backend (PID: $BACKEND_PID)..."
        kill -TERM "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
        print_success "Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_info "Stopping frontend (PID: $FRONTEND_PID)..."
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
        print_success "Frontend stopped"
    fi
    
    print_success "All services stopped gracefully"
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

################################################################################
# Dependency Checking
################################################################################

check_dependencies() {
    print_header "Checking Dependencies"
    
    local all_deps_ok=true
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            print_success "Python $PYTHON_VERSION found"
        else
            print_error "Python 3.11+ required (found $PYTHON_VERSION)"
            print_info "Install from: https://www.python.org/downloads/"
            all_deps_ok=false
        fi
    else
        print_error "Python 3 not found"
        print_info "Install from: https://www.python.org/downloads/"
        all_deps_ok=false
    fi
    
    # Check UV
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version 2>&1 | awk '{print $2}')
        print_success "UV $UV_VERSION found"
    else
        print_error "UV package manager not found"
        print_info "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        all_deps_ok=false
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version 2>&1 | sed 's/v//')
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
        
        if [ "$NODE_MAJOR" -ge 18 ]; then
            print_success "Node.js $NODE_VERSION found"
        else
            print_error "Node.js 18+ required (found $NODE_VERSION)"
            print_info "Install from: https://nodejs.org/"
            all_deps_ok=false
        fi
    else
        print_error "Node.js not found"
        print_info "Install from: https://nodejs.org/"
        all_deps_ok=false
    fi
    
    # Check Bun
    if command -v bun &> /dev/null; then
        BUN_VERSION=$(bun --version 2>&1)
        print_success "Bun $BUN_VERSION found"
    else
        print_error "Bun package manager not found"
        print_info "Install with: curl -fsSL https://bun.sh/install | bash"
        all_deps_ok=false
    fi
    
    # Check Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_success "Redis server is running"
        else
            print_warning "Redis is installed but not running"
            print_info "Start with: redis-server"
            print_info "The backend will start but caching/rate limiting will be disabled"
        fi
    else
        print_warning "Redis not found"
        print_info "Install from: https://redis.io/download"
        print_info "The backend will start but caching/rate limiting will be disabled"
    fi
    
    # Check PostgreSQL (optional - using Supabase)
    if command -v psql &> /dev/null; then
        PSQL_VERSION=$(psql --version 2>&1 | awk '{print $3}')
        print_success "PostgreSQL $PSQL_VERSION found (using Supabase)"
    else
        print_info "PostgreSQL client not found (using Supabase cloud)"
    fi
    
    if [ "$all_deps_ok" = false ]; then
        echo ""
        print_error "Missing required dependencies. Please install them and try again."
        exit 1
    fi
    
    echo ""
}

################################################################################
# Environment Validation
################################################################################

validate_environment() {
    print_header "Validating Environment"
    
    local all_env_ok=true
    
    # Check root .env
    if [ -f ".env" ]; then
        print_success "Root .env file found"
    else
        print_warning "Root .env file not found"
        print_info "Copy .env.example to .env and configure it"
    fi
    
    # Check backend .env
    if [ -f "backend/.env" ]; then
        print_success "Backend .env file found"
        
        # Check critical backend variables
        if grep -q "SUPABASE_URL=" backend/.env && grep -q "DATABASE_URL=" backend/.env; then
            print_success "Backend environment variables configured"
        else
            print_error "Backend .env missing critical variables"
            print_info "Ensure SUPABASE_URL and DATABASE_URL are set"
            all_env_ok=false
        fi
    else
        print_error "Backend .env file not found"
        print_info "Copy backend/.env.example to backend/.env and configure it"
        all_env_ok=false
    fi
    
    # Check frontend .env
    if [ -f "frontend/.env" ] || [ -f "frontend/.env.local" ]; then
        print_success "Frontend .env file found"
        
        # Check critical frontend variables
        ENV_FILE="frontend/.env"
        [ -f "frontend/.env.local" ] && ENV_FILE="frontend/.env.local"
        
        if grep -q "NEXT_PUBLIC_SUPABASE_URL=" "$ENV_FILE" && grep -q "NEXT_PUBLIC_SUPABASE_ANON_KEY=" "$ENV_FILE"; then
            print_success "Frontend environment variables configured"
        else
            print_error "Frontend .env missing critical variables"
            print_info "Ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are set"
            all_env_ok=false
        fi
    else
        print_error "Frontend .env file not found"
        print_info "Copy frontend/.env.example to frontend/.env.local and configure it"
        all_env_ok=false
    fi
    
    if [ "$all_env_ok" = false ]; then
        echo ""
        print_error "Environment configuration incomplete. Please configure .env files and try again."
        exit 1
    fi
    
    echo ""
}

################################################################################
# Backend Startup
################################################################################

start_backend() {
    print_header "Starting Backend Service"
    
    cd backend
    
    # Install dependencies
    print_info "Installing backend dependencies with UV..."
    if uv sync --quiet; then
        print_success "Backend dependencies installed"
    else
        print_error "Failed to install backend dependencies"
        cd ..
        exit 1
    fi
    
    # Start backend server
    print_info "Starting FastAPI server with Uvicorn..."
    uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    
    cd ..
    
    # Wait for backend to be ready
    print_info "Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend is ready!"
            print_success "Backend API: http://localhost:8000"
            print_success "API Docs: http://localhost:8000/docs"
            return 0
        fi
        sleep 1
    done
    
    print_warning "Backend health check timeout (may still be starting)"
    print_info "Backend API: http://localhost:8000"
    print_info "API Docs: http://localhost:8000/docs"
    echo ""
}

################################################################################
# Frontend Startup
################################################################################

start_frontend() {
    print_header "Starting Frontend Service"
    
    cd frontend
    
    # Install dependencies
    print_info "Installing frontend dependencies with Bun..."
    if bun install > ../frontend-install.log 2>&1; then
        print_success "Frontend dependencies installed"
    else
        print_error "Failed to install frontend dependencies"
        cd ..
        exit 1
    fi
    
    # Start frontend server
    print_info "Starting Next.js development server..."
    bun dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    cd ..
    
    # Wait for frontend to be ready
    print_info "Waiting for frontend to be ready..."
    for i in {1..60}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend is ready!"
            print_success "Frontend App: http://localhost:3000"
            return 0
        fi
        sleep 1
    done
    
    print_warning "Frontend health check timeout (may still be starting)"
    print_info "Frontend App: http://localhost:3000"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    clear
    
    print_header "PixCrawler Development Environment"
    echo ""
    
    # Run checks
    check_dependencies
    validate_environment
    
    # Start services
    start_backend
    start_frontend
    
    # Display summary
    print_header "Services Running"
    echo ""
    print_success "Backend API:  http://localhost:8000"
    print_success "API Docs:     http://localhost:8000/docs"
    print_success "Frontend App: http://localhost:3000"
    echo ""
    print_info "Logs:"
    print_info "  Backend:  tail -f backend.log"
    print_info "  Frontend: tail -f frontend.log"
    echo ""
    print_warning "Press Ctrl+C to stop all services"
    echo ""
    
    # Wait for user interrupt
    wait
}

# Run main function
main
