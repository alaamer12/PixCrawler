################################################################################
# PixCrawler Development Startup Script (Windows PowerShell)
################################################################################
# This script starts both the backend (FastAPI) and frontend (Next.js) services
# for local development with a single command.
#
# Usage:
#   .\scripts\start-dev.ps1
#
# Requirements:
#   - Python 3.11+
#   - Node.js 18+
#   - Redis server
#   - PostgreSQL (Supabase)
#   - UV package manager
#   - Bun package manager
################################################################################

# Enable strict mode
$ErrorActionPreference = "Stop"

# Process objects for cleanup
$script:BackendProcess = $null
$script:FrontendProcess = $null

################################################################################
# Helper Functions
################################################################################

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host "  $Message" -ForegroundColor Blue
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

################################################################################
# Cleanup Function
################################################################################

function Stop-Services {
    Write-Host ""
    Write-Header "Shutting Down Services"
    
    if ($script:BackendProcess -and !$script:BackendProcess.HasExited) {
        Write-Info "Stopping backend (PID: $($script:BackendProcess.Id))..."
        Stop-Process -Id $script:BackendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Success "Backend stopped"
    }
    
    if ($script:FrontendProcess -and !$script:FrontendProcess.HasExited) {
        Write-Info "Stopping frontend (PID: $($script:FrontendProcess.Id))..."
        Stop-Process -Id $script:FrontendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Success "Frontend stopped"
    }
    
    Write-Success "All services stopped gracefully"
}

# Register cleanup on exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Stop-Services
} | Out-Null

################################################################################
# Dependency Checking
################################################################################

function Test-Dependencies {
    Write-Header "Checking Dependencies"
    
    $allDepsOk = $true
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            
            if ($major -ge 3 -and $minor -ge 11) {
                Write-Success "Python $($matches[1]).$($matches[2]).$($matches[3]) found"
            } else {
                Write-ErrorMsg "Python 3.11+ required (found $($matches[1]).$($matches[2]).$($matches[3]))"
                Write-Info "Install from: https://www.python.org/downloads/"
                $allDepsOk = $false
            }
        }
    } catch {
        Write-ErrorMsg "Python not found"
        Write-Info "Install from: https://www.python.org/downloads/"
        $allDepsOk = $false
    }
    
    # Check UV
    try {
        $uvVersion = uv --version 2>&1
        if ($uvVersion -match "uv (\S+)") {
            Write-Success "UV $($matches[1]) found"
        }
    } catch {
        Write-ErrorMsg "UV package manager not found"
        Write-Info "Install with: powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`""
        $allDepsOk = $false
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>&1
        if ($nodeVersion -match "v(\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            
            if ($major -ge 18) {
                Write-Success "Node.js $($matches[1]).$($matches[2]).$($matches[3]) found"
            } else {
                Write-ErrorMsg "Node.js 18+ required (found $($matches[1]).$($matches[2]).$($matches[3]))"
                Write-Info "Install from: https://nodejs.org/"
                $allDepsOk = $false
            }
        }
    } catch {
        Write-ErrorMsg "Node.js not found"
        Write-Info "Install from: https://nodejs.org/"
        $allDepsOk = $false
    }
    
    # Check Bun
    try {
        $bunVersion = bun --version 2>&1
        Write-Success "Bun $bunVersion found"
    } catch {
        Write-ErrorMsg "Bun package manager not found"
        Write-Info "Install from: https://bun.sh/install (use WSL or install via npm: npm install -g bun)"
        $allDepsOk = $false
    }
    
    # Check Redis
    try {
        $redisCheck = redis-cli ping 2>&1
        if ($redisCheck -eq "PONG") {
            Write-Success "Redis server is running"
        } else {
            Write-Warning "Redis is installed but not running"
            Write-Info "Start with: redis-server"
            Write-Info "The backend will start but caching/rate limiting will be disabled"
        }
    } catch {
        Write-Warning "Redis not found"
        Write-Info "Install from: https://redis.io/download or use WSL"
        Write-Info "The backend will start but caching/rate limiting will be disabled"
    }
    
    # Check PostgreSQL (optional - using Supabase)
    try {
        $psqlVersion = psql --version 2>&1
        if ($psqlVersion -match "psql \(PostgreSQL\) (\S+)") {
            Write-Success "PostgreSQL $($matches[1]) found (using Supabase)"
        }
    } catch {
        Write-Info "PostgreSQL client not found (using Supabase cloud)"
    }
    
    if (-not $allDepsOk) {
        Write-Host ""
        Write-ErrorMsg "Missing required dependencies. Please install them and try again."
        exit 1
    }
    
    Write-Host ""
}

################################################################################
# Environment Validation
################################################################################

function Test-Environment {
    Write-Header "Validating Environment"
    
    $allEnvOk = $true
    
    # Check root .env
    if (Test-Path ".env") {
        Write-Success "Root .env file found"
    } else {
        Write-Warning "Root .env file not found"
        Write-Info "Copy .env.example to .env and configure it"
    }
    
    # Check backend .env
    if (Test-Path "backend\.env") {
        Write-Success "Backend .env file found"
        
        # Check critical backend variables
        $backendEnv = Get-Content "backend\.env" -Raw
        if ($backendEnv -match "SUPABASE_URL=" -and $backendEnv -match "DATABASE_URL=") {
            Write-Success "Backend environment variables configured"
        } else {
            Write-ErrorMsg "Backend .env missing critical variables"
            Write-Info "Ensure SUPABASE_URL and DATABASE_URL are set"
            $allEnvOk = $false
        }
    } else {
        Write-ErrorMsg "Backend .env file not found"
        Write-Info "Copy backend\.env.example to backend\.env and configure it"
        $allEnvOk = $false
    }
    
    # Check frontend .env
    $frontendEnvPath = if (Test-Path "frontend\.env.local") { "frontend\.env.local" } 
                       elseif (Test-Path "frontend\.env") { "frontend\.env" }
                       else { $null }
    
    if ($frontendEnvPath) {
        Write-Success "Frontend .env file found"
        
        # Check critical frontend variables
        $frontendEnv = Get-Content $frontendEnvPath -Raw
        if ($frontendEnv -match "NEXT_PUBLIC_SUPABASE_URL=" -and $frontendEnv -match "NEXT_PUBLIC_SUPABASE_ANON_KEY=") {
            Write-Success "Frontend environment variables configured"
        } else {
            Write-ErrorMsg "Frontend .env missing critical variables"
            Write-Info "Ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are set"
            $allEnvOk = $false
        }
    } else {
        Write-ErrorMsg "Frontend .env file not found"
        Write-Info "Copy frontend\.env.example to frontend\.env.local and configure it"
        $allEnvOk = $false
    }
    
    if (-not $allEnvOk) {
        Write-Host ""
        Write-ErrorMsg "Environment configuration incomplete. Please configure .env files and try again."
        exit 1
    }
    
    Write-Host ""
}

################################################################################
# Backend Startup
################################################################################

function Start-Backend {
    Write-Header "Starting Backend Service"
    
    Push-Location backend
    
    try {
        # Install dependencies
        Write-Info "Installing backend dependencies with UV..."
        $installOutput = uv sync --quiet 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Backend dependencies installed"
        } else {
            Write-ErrorMsg "Failed to install backend dependencies"
            Write-Host $installOutput
            Pop-Location
            exit 1
        }
        
        # Start backend server
        Write-Info "Starting FastAPI server with Uvicorn..."
        $script:BackendProcess = Start-Process -FilePath "uv" -ArgumentList "run", "uvicorn", "backend.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" -NoNewWindow -PassThru -RedirectStandardOutput "..\backend.log" -RedirectStandardError "..\backend-error.log"
        
        Pop-Location
        
        # Wait for backend to be ready
        Write-Info "Waiting for backend to be ready..."
        $maxAttempts = 30
        $attempt = 0
        $backendReady = $false
        
        while ($attempt -lt $maxAttempts) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    $backendReady = $true
                    break
                }
            } catch {
                # Continue waiting
            }
            Start-Sleep -Seconds 1
            $attempt++
        }
        
        if ($backendReady) {
            Write-Success "Backend is ready!"
            Write-Success "Backend API: http://localhost:8000"
            Write-Success "API Docs: http://localhost:8000/docs"
        } else {
            Write-Warning "Backend health check timeout (may still be starting)"
            Write-Info "Backend API: http://localhost:8000"
            Write-Info "API Docs: http://localhost:8000/docs"
        }
        
        Write-Host ""
    } catch {
        Write-ErrorMsg "Failed to start backend: $_"
        Pop-Location
        exit 1
    }
}

################################################################################
# Frontend Startup
################################################################################

function Start-Frontend {
    Write-Header "Starting Frontend Service"
    
    Push-Location frontend
    
    try {
        # Install dependencies
        Write-Info "Installing frontend dependencies with Bun..."
        $installOutput = bun install 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Frontend dependencies installed"
        } else {
            Write-ErrorMsg "Failed to install frontend dependencies"
            Write-Host $installOutput
            Pop-Location
            exit 1
        }
        
        # Start frontend server
        Write-Info "Starting Next.js development server..."
        $script:FrontendProcess = Start-Process -FilePath "bun" -ArgumentList "dev" -NoNewWindow -PassThru -RedirectStandardOutput "..\frontend.log" -RedirectStandardError "..\frontend-error.log"
        
        Pop-Location
        
        # Wait for frontend to be ready
        Write-Info "Waiting for frontend to be ready..."
        $maxAttempts = 60
        $attempt = 0
        $frontendReady = $false
        
        while ($attempt -lt $maxAttempts) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    $frontendReady = $true
                    break
                }
            } catch {
                # Continue waiting
            }
            Start-Sleep -Seconds 1
            $attempt++
        }
        
        if ($frontendReady) {
            Write-Success "Frontend is ready!"
            Write-Success "Frontend App: http://localhost:3000"
        } else {
            Write-Warning "Frontend health check timeout (may still be starting)"
            Write-Info "Frontend App: http://localhost:3000"
        }
        
        Write-Host ""
    } catch {
        Write-ErrorMsg "Failed to start frontend: $_"
        Pop-Location
        exit 1
    }
}

################################################################################
# Main Execution
################################################################################

function Main {
    Clear-Host
    
    Write-Header "PixCrawler Development Environment"
    
    # Run checks
    Test-Dependencies
    Test-Environment
    
    # Start services
    Start-Backend
    Start-Frontend
    
    # Display summary
    Write-Header "Services Running"
    Write-Host ""
    Write-Success "Backend API:  http://localhost:8000"
    Write-Success "API Docs:     http://localhost:8000/docs"
    Write-Success "Frontend App: http://localhost:3000"
    Write-Host ""
    Write-Info "Logs:"
    Write-Info "  Backend:  Get-Content backend.log -Wait"
    Write-Info "  Frontend: Get-Content frontend.log -Wait"
    Write-Host ""
    Write-Warning "Press Ctrl+C to stop all services"
    Write-Host ""
    
    # Wait for user interrupt
    try {
        while ($true) {
            Start-Sleep -Seconds 1
            
            # Check if processes are still running
            if ($script:BackendProcess -and $script:BackendProcess.HasExited) {
                Write-ErrorMsg "Backend process has exited unexpectedly"
                break
            }
            if ($script:FrontendProcess -and $script:FrontendProcess.HasExited) {
                Write-ErrorMsg "Frontend process has exited unexpectedly"
                break
            }
        }
    } catch {
        # Ctrl+C pressed
    } finally {
        Stop-Services
    }
}

# Run main function
Main
