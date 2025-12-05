@echo off
REM Frontend Integration Testing Setup Script (Windows)
REM This script helps configure the frontend for testing with Prism mock server

setlocal enabledelayedexpansion

echo ==========================================
echo PixCrawler Frontend Integration Testing
echo Setup Script (Windows)
echo ==========================================
echo.

REM Check if we're in the correct directory
if not exist "openapi.json" (
    echo [ERROR] openapi.json not found!
    echo Please run this script from the backend\postman directory
    exit /b 1
)

echo Step 1: Checking prerequisites...
echo.

REM Check for Bun
where bun >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Bun found
    set PKG_MANAGER=bun
    goto check_prism
)

REM Check for Node.js
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Node.js found
    set PKG_MANAGER=npm
    goto check_prism
)

echo [ERROR] Neither Bun nor Node.js found!
echo Please install Bun or Node.js first:
echo   Bun: https://bun.sh
echo   Node.js: https://nodejs.org
exit /b 1

:check_prism
REM Check for Prism
where prism >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Prism CLI found
    goto configure_frontend
)

echo [WARNING] Prism CLI not found
echo.
echo Installing Prism CLI...
if "%PKG_MANAGER%"=="bun" (
    bun add -g @stoplight/prism-cli
) else (
    npm install -g @stoplight/prism-cli
)

where prism >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Prism CLI installed successfully
) else (
    echo [ERROR] Failed to install Prism CLI
    echo Please install manually: npm install -g @stoplight/prism-cli
    exit /b 1
)

:configure_frontend
echo.
echo Step 2: Configuring frontend environment...
echo.

REM Navigate to frontend directory
cd ..\..\frontend

REM Check if .env.local exists
if exist ".env.local" (
    echo [WARNING] .env.local already exists
    echo Creating backup: .env.local.backup
    copy /Y .env.local .env.local.backup >nul
)

REM Check if NEXT_PUBLIC_API_URL is already set correctly
findstr /C:"NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1" .env.local >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] NEXT_PUBLIC_API_URL already configured correctly
    goto check_dependencies
)

echo Setting NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1

REM Create or update .env.local
(
echo.
echo # Mock Server Configuration (for testing^)
echo NEXT_PUBLIC_API_URL=http://localhost:4010/api/v1
) >> .env.local

echo [OK] Frontend environment configured

:check_dependencies
echo.
echo Step 3: Checking frontend dependencies...
echo.

if not exist "node_modules" (
    echo Installing frontend dependencies...
    if "%PKG_MANAGER%"=="bun" (
        bun install
    ) else (
        npm install
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies already installed
)

echo.
echo ==========================================
echo [SUCCESS] Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo.
echo 1. Start the Prism mock server:
echo    cd backend\postman
echo    prism mock openapi.json -p 4010
echo.
echo 2. In a new terminal, start the frontend:
echo    cd frontend
if "%PKG_MANAGER%"=="bun" (
    echo    bun dev
) else (
    echo    npm run dev
)
echo.
echo 3. Open your browser to http://localhost:3000
echo.
echo 4. Follow the testing guide:
echo    backend\postman\FRONTEND_INTEGRATION_TESTING.md
echo.
echo 5. Use the checklist:
echo    backend\postman\INTEGRATION_TEST_CHECKLIST.md
echo.
echo ==========================================

endlocal
