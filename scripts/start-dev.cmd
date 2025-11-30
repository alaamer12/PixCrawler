@echo off
REM ################################################################################
REM # PixCrawler Development Startup Script (Windows Command Prompt)
REM ################################################################################
REM # This script starts both the backend (FastAPI) and frontend (Next.js) services
REM # for local development with a single command.
REM #
REM # Usage:
REM #   scripts\start-dev.cmd
REM #
REM # Requirements:
REM #   - Python 3.11+
REM #   - Node.js 18+
REM #   - Redis server
REM #   - PostgreSQL (Supabase)
REM #   - UV package manager
REM #   - Bun package manager
REM ################################################################################

setlocal enabledelayedexpansion

REM Store process IDs for cleanup
set BACKEND_PID=
set FRONTEND_PID=

REM ################################################################################
REM # Helper Functions
REM ################################################################################

:print_header
echo.
echo ================================================================================
echo   %~1
echo ================================================================================
echo.
goto :eof

:print_success
echo [SUCCESS] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

:print_warning
echo [WARNING] %~1
goto :eof

:print_info
echo [INFO] %~1
goto :eof

REM ################################################################################
REM # Cleanup Function
REM ################################################################################

:cleanup
echo.
call :print_header "Shutting Down Services"

if defined BACKEND_PID (
    call :print_info "Stopping backend (PID: %BACKEND_PID%)..."
    taskkill /PID %BACKEND_PID% /F /T >nul 2>&1
    call :print_success "Backend stopped"
)

if defined FRONTEND_PID (
    call :print_info "Stopping frontend (PID: %FRONTEND_PID%)..."
    taskkill /PID %FRONTEND_PID% /F /T >nul 2>&1
    call :print_success "Frontend stopped"
)

call :print_success "All services stopped gracefully"
exit /b 0

REM ################################################################################
REM # Dependency Checking
REM ################################################################################

:check_dependencies
call :print_header "Checking Dependencies"

set ALL_DEPS_OK=1

REM Check Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
    for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
        set PYTHON_MAJOR=%%a
        set PYTHON_MINOR=%%b
    )
    if !PYTHON_MAJOR! geq 3 if !PYTHON_MINOR! geq 11 (
        call :print_success "Python !PYTHON_VERSION! found"
    ) else (
        call :print_error "Python 3.11+ required (found !PYTHON_VERSION!)"
        call :print_info "Install from: https://www.python.org/downloads/"
        set ALL_DEPS_OK=0
    )
) else (
    call :print_error "Python not found"
    call :print_info "Install from: https://www.python.org/downloads/"
    set ALL_DEPS_OK=0
)

REM Check UV
uv --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%v in ('uv --version 2^>^&1') do set UV_VERSION=%%v
    call :print_success "UV !UV_VERSION! found"
) else (
    call :print_error "UV package manager not found"
    call :print_info "Install with: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
    set ALL_DEPS_OK=0
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=1 delims=v" %%v in ('node --version 2^>^&1') do set NODE_VERSION=%%v
    for /f "tokens=1 delims=." %%a in ("!NODE_VERSION!") do set NODE_MAJOR=%%a
    if !NODE_MAJOR! geq 18 (
        call :print_success "Node.js !NODE_VERSION! found"
    ) else (
        call :print_error "Node.js 18+ required (found !NODE_VERSION!)"
        call :print_info "Install from: https://nodejs.org/"
        set ALL_DEPS_OK=0
    )
) else (
    call :print_error "Node.js not found"
    call :print_info "Install from: https://nodejs.org/"
    set ALL_DEPS_OK=0
)

REM Check Bun
bun --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f %%v in ('bun --version 2^>^&1') do set BUN_VERSION=%%v
    call :print_success "Bun !BUN_VERSION! found"
) else (
    call :print_error "Bun package manager not found"
    call :print_info "Install from: https://bun.sh/install (use WSL or install via npm: npm install -g bun)"
    set ALL_DEPS_OK=0
)

REM Check Redis
redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    call :print_success "Redis server is running"
) else (
    call :print_warning "Redis not found or not running"
    call :print_info "Install from: https://redis.io/download or use WSL"
    call :print_info "The backend will start but caching/rate limiting will be disabled"
)

REM Check PostgreSQL (optional - using Supabase)
psql --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=3" %%v in ('psql --version 2^>^&1') do set PSQL_VERSION=%%v
    call :print_success "PostgreSQL !PSQL_VERSION! found (using Supabase)"
) else (
    call :print_info "PostgreSQL client not found (using Supabase cloud)"
)

if !ALL_DEPS_OK! equ 0 (
    echo.
    call :print_error "Missing required dependencies. Please install them and try again."
    exit /b 1
)

echo.
goto :eof

REM ################################################################################
REM # Environment Validation
REM ################################################################################

:validate_environment
call :print_header "Validating Environment"

set ALL_ENV_OK=1

REM Check root .env
if exist ".env" (
    call :print_success "Root .env file found"
) else (
    call :print_warning "Root .env file not found"
    call :print_info "Copy .env.example to .env and configure it"
)

REM Check backend .env
if exist "backend\.env" (
    call :print_success "Backend .env file found"
    
    REM Check critical backend variables
    findstr /C:"SUPABASE_URL=" backend\.env >nul 2>&1
    set SUPABASE_FOUND=!errorlevel!
    findstr /C:"DATABASE_URL=" backend\.env >nul 2>&1
    set DATABASE_FOUND=!errorlevel!
    
    if !SUPABASE_FOUND! equ 0 if !DATABASE_FOUND! equ 0 (
        call :print_success "Backend environment variables configured"
    ) else (
        call :print_error "Backend .env missing critical variables"
        call :print_info "Ensure SUPABASE_URL and DATABASE_URL are set"
        set ALL_ENV_OK=0
    )
) else (
    call :print_error "Backend .env file not found"
    call :print_info "Copy backend\.env.example to backend\.env and configure it"
    set ALL_ENV_OK=0
)

REM Check frontend .env
set FRONTEND_ENV_FILE=
if exist "frontend\.env.local" (
    set FRONTEND_ENV_FILE=frontend\.env.local
) else if exist "frontend\.env" (
    set FRONTEND_ENV_FILE=frontend\.env
)

if defined FRONTEND_ENV_FILE (
    call :print_success "Frontend .env file found"
    
    REM Check critical frontend variables
    findstr /C:"NEXT_PUBLIC_SUPABASE_URL=" !FRONTEND_ENV_FILE! >nul 2>&1
    set SUPABASE_URL_FOUND=!errorlevel!
    findstr /C:"NEXT_PUBLIC_SUPABASE_ANON_KEY=" !FRONTEND_ENV_FILE! >nul 2>&1
    set ANON_KEY_FOUND=!errorlevel!
    
    if !SUPABASE_URL_FOUND! equ 0 if !ANON_KEY_FOUND! equ 0 (
        call :print_success "Frontend environment variables configured"
    ) else (
        call :print_error "Frontend .env missing critical variables"
        call :print_info "Ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are set"
        set ALL_ENV_OK=0
    )
) else (
    call :print_error "Frontend .env file not found"
    call :print_info "Copy frontend\.env.example to frontend\.env.local and configure it"
    set ALL_ENV_OK=0
)

if !ALL_ENV_OK! equ 0 (
    echo.
    call :print_error "Environment configuration incomplete. Please configure .env files and try again."
    exit /b 1
)

echo.
goto :eof

REM ################################################################################
REM # Backend Startup
REM ################################################################################

:start_backend
call :print_header "Starting Backend Service"

cd backend

REM Install dependencies
call :print_info "Installing backend dependencies with UV..."
uv sync --quiet >nul 2>&1
if %errorlevel% equ 0 (
    call :print_success "Backend dependencies installed"
) else (
    call :print_error "Failed to install backend dependencies"
    cd ..
    exit /b 1
)

REM Start backend server
call :print_info "Starting FastAPI server with Uvicorn..."
start /B "" uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 > ..\backend.log 2>&1

REM Get the PID (approximate - last started process)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /NH') do set BACKEND_PID=%%a

cd ..

REM Wait for backend to be ready
call :print_info "Waiting for backend to be ready..."
set /a ATTEMPTS=0
:backend_wait_loop
if !ATTEMPTS! geq 30 goto backend_timeout
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    call :print_success "Backend is ready!"
    call :print_success "Backend API: http://localhost:8000"
    call :print_success "API Docs: http://localhost:8000/docs"
    echo.
    goto :eof
)
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
goto backend_wait_loop

:backend_timeout
call :print_warning "Backend health check timeout (may still be starting)"
call :print_info "Backend API: http://localhost:8000"
call :print_info "API Docs: http://localhost:8000/docs"
echo.
goto :eof

REM ################################################################################
REM # Frontend Startup
REM ################################################################################

:start_frontend
call :print_header "Starting Frontend Service"

cd frontend

REM Install dependencies
call :print_info "Installing frontend dependencies with Bun..."
bun install >nul 2>&1
if %errorlevel% equ 0 (
    call :print_success "Frontend dependencies installed"
) else (
    call :print_error "Failed to install frontend dependencies"
    cd ..
    exit /b 1
)

REM Start frontend server
call :print_info "Starting Next.js development server..."
start /B "" bun dev > ..\frontend.log 2>&1

REM Get the PID (approximate - last started process)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq bun.exe" /NH') do set FRONTEND_PID=%%a

cd ..

REM Wait for frontend to be ready
call :print_info "Waiting for frontend to be ready..."
set /a ATTEMPTS=0
:frontend_wait_loop
if !ATTEMPTS! geq 60 goto frontend_timeout
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    call :print_success "Frontend is ready!"
    call :print_success "Frontend App: http://localhost:3000"
    echo.
    goto :eof
)
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
goto frontend_wait_loop

:frontend_timeout
call :print_warning "Frontend health check timeout (may still be starting)"
call :print_info "Frontend App: http://localhost:3000"
echo.
goto :eof

REM ################################################################################
REM # Main Execution
REM ################################################################################

:main
cls

call :print_header "PixCrawler Development Environment"

REM Run checks
call :check_dependencies
if %errorlevel% neq 0 exit /b 1

call :validate_environment
if %errorlevel% neq 0 exit /b 1

REM Start services
call :start_backend
if %errorlevel% neq 0 exit /b 1

call :start_frontend
if %errorlevel% neq 0 exit /b 1

REM Display summary
call :print_header "Services Running"
echo.
call :print_success "Backend API:  http://localhost:8000"
call :print_success "API Docs:     http://localhost:8000/docs"
call :print_success "Frontend App: http://localhost:3000"
echo.
call :print_info "Logs:"
call :print_info "  Backend:  type backend.log"
call :print_info "  Frontend: type frontend.log"
echo.
call :print_warning "Press Ctrl+C to stop all services"
echo.

REM Wait for user interrupt
pause >nul

REM Cleanup on exit
call :cleanup
goto :eof

REM Run main function
call :main
