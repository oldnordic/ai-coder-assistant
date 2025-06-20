#!/bin/bash

echo "========================================"
echo "Building AI Coder Assistant for macOS"
echo "========================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ and try again"
    echo "You can install it using Homebrew: brew install python"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "ERROR: Python $python_version is installed, but Python $required_version+ is required"
    exit 1
fi

echo "Python version: $python_version"

# Check if Homebrew is available (recommended for macOS)
if ! command -v brew &> /dev/null; then
    echo "WARNING: Homebrew is not installed"
    echo "It's recommended to install Homebrew for easier dependency management:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install requirements"
    echo "You may need to install additional system dependencies:"
    echo "  brew install openssl readline sqlite3 xz zlib"
    exit 1
fi

# Install build tools
echo "Installing build tools..."
pip install pyinstaller pytest pytest-qt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install build tools"
    exit 1
fi

# Run tests to ensure everything is working
echo "Running tests to verify build environment..."
export PYTHONPATH=src
python -m pytest src/tests/core/test_config.py src/tests/core/test_error_handler.py src/tests/test_base_component.py -v --tb=short
if [ $? -ne 0 ]; then
    echo "WARNING: Some tests failed, but continuing with build..."
fi

# Check for UPX
echo "Checking for UPX..."
if ! command -v upx &> /dev/null; then
    echo "UPX not found. Installing UPX..."
    
    if command -v brew &> /dev/null; then
        brew install upx
    else
        echo "WARNING: Could not install UPX automatically"
        echo "Please install UPX manually from: https://upx.github.io/"
        echo "Or install Homebrew and run: brew install upx"
        echo "Continuing without UPX optimization..."
    fi
fi

# Make build script executable
chmod +x build_all.py

# Run build with proper PYTHONPATH
echo "Starting build process..."
export PYTHONPATH=src
python build_all.py
if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""
echo "Output files are in the 'dist' directory:"
echo "- ai-coder-assistant (Main GUI application)"
echo "- ai-coder-cli (Command line interface)"
echo "- ai-coder-api (REST API server)"
echo ""
echo "To run the application:"
echo "  ./dist/ai-coder-assistant"
echo ""
echo "To run the CLI:"
echo "  ./dist/ai-coder-cli"
echo ""
echo "To run the API server:"
echo "  ./dist/ai-coder-api"
echo ""
echo "Make sure to make the binaries executable:"
echo "  chmod +x dist/*"
echo ""
echo "For development, use:"
echo "  PYTHONPATH=src python src/main.py"
echo ""
echo "Note: On macOS, you may need to allow the application in Security & Privacy settings"
echo "if you get a security warning when running the binary for the first time."
echo "" 