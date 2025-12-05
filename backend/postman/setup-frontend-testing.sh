#!/bin/bash

# Frontend Integration Testing Setup Script
# This script helps configure the frontend for testing with Prism mock server

set -e

echo "=========================================="
echo "PixCrawler Frontend Integration Testing"
echo "Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the correct directory
if [ ! -f "openapi.json" ]; then
    echo -e "${RED}Error: openapi.json not found!${NC}"
    echo "Please run this script from the backend/postman directory"
    exit 1
fi

echo "Step 1: Checking prerequisites..."
echo ""

# Check for Node.js or Bun
if command -v bun &> /dev/null; then
    echo -e "${GREEN}✓ Bun found: $(bun --version)${NC}"
    PKG_MANAGER="bun"
elif command -v node &> /dev/null; then
    echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"
    PKG_MANAGER="npm"
else
    echo -e "${RED}✗ Neither Bun nor Node.js found!${NC}"
    echo "Please install Bun or Node.js first:"
    echo "  Bun: https://bun.sh"
    echo "  Node.js: https://nodejs.org"
    exit 1
fi

# Check for Prism
if command -v prism &> /dev/null; then
    echo -e "${GREEN}✓ Prism CLI found: $(prism --version)${NC}"
else
    echo -e "${YELLOW}✗ Prism CLI not found${NC}"
    echo ""
    echo "Installing Prism CLI..."
    if [ "$PKG_MANAGER" = "bun" ]; then
        bun add -g @stoplight/prism-cli
    else
        npm install -g @stoplight/prism-cli
    fi
    
    if command -v prism &> /dev/null; then
        echo -e "${GREEN}✓ Prism CLI installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install Prism CLI${NC}"
        echo "Please install manually: npm install -g @stoplight/prism-cli"
        exit 1
    fi
fi

echo ""
echo "Step 2: Configuring frontend environment..."
echo ""

# Navigate to frontend directory
cd ../../frontend

# Check if .env.local exists
if [ -f ".env.local" ]; then
    echo -e "${YELLOW}Warning: .env.local already exists${NC}"
    echo "Creating backup: .env.local.backup"
    cp .env.local .env.local.backup
fi

# Check if NEXT_PUBLIC_API_URL is already set correctly
if grep -q "NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1" .env.local 2>/dev/null; then
    echo -e "${GREEN}✓ NEXT_PUBLIC_API_URL already configured correctly${NC}"
else
    echo "Setting NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1"
    
    # Remove existing NEXT_PUBLIC_API_URL if present
    if [ -f ".env.local" ]; then
        sed -i.bak '/^NEXT_PUBLIC_API_URL=/d' .env.local
    fi
    
    # Add new NEXT_PUBLIC_API_URL
    echo "" >> .env.local
    echo "# Mock Server Configuration (for testing)" >> .env.local
    echo "NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1" >> .env.local
    
    echo -e "${GREEN}✓ Frontend environment configured${NC}"
fi

echo ""
echo "Step 3: Checking frontend dependencies..."
echo ""

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    if [ "$PKG_MANAGER" = "bun" ]; then
        bun install
    else
        npm install
    fi
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the Prism mock server:"
echo "   cd backend/postman"
echo "   prism mock openapi.json -p 4010"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend"
if [ "$PKG_MANAGER" = "bun" ]; then
    echo "   bun dev"
else
    echo "   npm run dev"
fi
echo ""
echo "3. Open your browser to http://localhost:3000"
echo ""
echo "4. Follow the testing guide:"
echo "   backend/postman/FRONTEND_INTEGRATION_TESTING.md"
echo ""
echo "5. Use the checklist:"
echo "   backend/postman/INTEGRATION_TEST_CHECKLIST.md"
echo ""
echo "=========================================="
