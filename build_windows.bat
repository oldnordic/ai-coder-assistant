@echo off
echo ========================================
echo Building AI Coder Assistant for Windows
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

REM Install build tools
echo Installing build tools...
pip install pyinstaller pytest pytest-qt
if errorlevel 1 (
    echo ERROR: Failed to install build tools
    pause
    exit /b 1
)

REM Run tests to ensure everything is working
echo Running tests to verify build environment...
set PYTHONPATH=src
python -m pytest src/tests/core/test_config.py src/tests/core/test_error_handler.py src/tests/test_base_component.py -v --tb=short
if errorlevel 1 (
    echo WARNING: Some tests failed, but continuing with build...
)

REM Check for UPX
echo Checking for UPX...
where upx >nul 2>&1
if errorlevel 1 (
    echo UPX not found. Installing UPX...
    REM Download UPX for Windows
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/upx/upx/releases/download/v4.0.2/upx-4.0.2-win64.zip' -OutFile 'upx.zip'"
    powershell -Command "Expand-Archive -Path 'upx.zip' -DestinationPath '.' -Force"
    copy "upx-4.0.2-win64\upx.exe" ".venv\Scripts\"
    del "upx.zip"
    rmdir /s /q "upx-4.0.2-win64"
    echo UPX installed successfully
)

REM Run build with proper PYTHONPATH
echo Starting build process...
set PYTHONPATH=src
python build_all.py
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Output files are in the 'dist' directory:
echo - ai-coder-assistant.exe (Main GUI application)
echo - ai-coder-cli.exe (Command line interface)
echo - ai-coder-api.exe (REST API server)
echo.
echo To run the application:
echo   dist\ai-coder-assistant.exe
echo.
echo To run the CLI:
echo   dist\ai-coder-cli.exe
echo.
echo To run the API server:
echo   dist\ai-coder-api.exe
echo.
echo For development, use:
echo   set PYTHONPATH=src && python src/main.py
echo.
pause 