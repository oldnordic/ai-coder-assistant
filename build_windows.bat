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
if not exist "build-env" (
    echo Creating virtual environment...
    python -m venv build-env
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call build-env\Scripts\activate.bat

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
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

REM Check for UPX
echo Checking for UPX...
where upx >nul 2>&1
if errorlevel 1 (
    echo UPX not found. Installing UPX...
    REM Download UPX for Windows
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/upx/upx/releases/download/v4.0.2/upx-4.0.2-win64.zip' -OutFile 'upx.zip'"
    powershell -Command "Expand-Archive -Path 'upx.zip' -DestinationPath '.' -Force"
    copy "upx-4.0.2-win64\upx.exe" "build-env\Scripts\"
    del "upx.zip"
    rmdir /s /q "upx-4.0.2-win64"
    echo UPX installed successfully
)

REM Run build
echo Starting build process...
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
echo - ai-coder-core.exe (Main GUI application)
echo - ai-coder-analyzer.exe (AI analysis engine)
echo - ai-coder-scanner.exe (Code scanner)
echo - ai-coder-web.exe (Web scraper)
echo - ai-coder-trainer.exe (Model trainer)
echo - ai-coder-launcher.exe (Component launcher)
echo.
echo To run the application:
echo   dist\ai-coder-core.exe
echo.
echo Or use the launcher:
echo   dist\ai-coder-launcher.exe core
echo.
pause 