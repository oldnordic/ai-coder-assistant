#!/usr/bin/env python3
"""
Script to install PyTorch with ROCm support for AMD GPUs
"""

import subprocess
import sys
import os

def check_rocm_version():
    """Check what ROCm version is installed"""
    try:
        result = subprocess.run(['rocm-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Try to extract ROCm version from output
            output = result.stdout
            if 'ROCm' in output:
                print("ROCm is installed and working")
                return True
            else:
                print("ROCm detected but version unclear")
                return True
    except Exception as e:
        print(f"Error checking ROCm: {e}")
        return False

def get_rocm_version():
    """Try to determine ROCm version"""
    try:
        # Check common ROCm version files
        rocm_paths = [
            "/opt/rocm/.info/version",
            "/opt/rocm/version",
            "/opt/rocm/.info/version-dev"
        ]
        
        for path in rocm_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    version = f.read().strip()
                    print(f"Found ROCm version: {version}")
                    return version
        
        # Try rocm-smi version
        result = subprocess.run(['rocm-smi', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"ROCm version from rocm-smi: {result.stdout.strip()}")
            return "detected"
            
    except Exception as e:
        print(f"Error getting ROCm version: {e}")
    
    return "unknown"

def install_pytorch_rocm(rocm_version="5.7"):
    """Install PyTorch with ROCm support"""
    print(f"\n🚀 Installing PyTorch with ROCm {rocm_version} support...")
    
    # Uninstall current PyTorch packages
    print("Uninstalling current PyTorch packages...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision", "torchaudio"])
    
    # Install PyTorch with ROCm support
    print(f"Installing PyTorch with ROCm {rocm_version}...")
    index_url = f"https://download.pytorch.org/whl/rocm{rocm_version}"
    
    result = subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "torch", "torchvision", "torchaudio",
        "--index-url", index_url
    ])
    
    if result.returncode == 0:
        print("✅ PyTorch with ROCm support installed successfully!")
        return True
    else:
        print("❌ Failed to install PyTorch with ROCm support")
        return False

def verify_installation():
    """Verify that PyTorch can see the GPU"""
    print("\n🔍 Verifying GPU detection...")
    
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            print(f"GPU count: {device_count}")
            
            for i in range(device_count):
                device_name = torch.cuda.get_device_name(i)
                print(f"  GPU {i}: {device_name}")
            
            # Test GPU memory allocation
            try:
                device = torch.device("cuda:0")
                test_tensor = torch.randn(1000, 1000, device=device)
                print(f"✅ GPU memory test successful: {test_tensor.device}")
                del test_tensor
                torch.cuda.empty_cache()
            except Exception as e:
                print(f"❌ GPU memory test failed: {e}")
        else:
            print("❌ CUDA/ROCm not available in PyTorch")
            
    except ImportError as e:
        print(f"❌ Error importing torch: {e}")

def main():
    print("🔧 PyTorch ROCm Installation Helper")
    print("=" * 50)
    
    # Check if ROCm is installed
    if not check_rocm_version():
        print("❌ ROCm not detected. Please install ROCm first:")
        print("   https://rocmdocs.amd.com/en/latest/Installation_Guide/Installation-Guide.html")
        return
    
    # Get ROCm version
    rocm_version = get_rocm_version()
    
    # Ask user for ROCm version to use
    print("\n📋 Available ROCm versions for PyTorch:")
    print("  5.7 - Stable, widely supported")
    print("  6.0 - Latest, may have compatibility issues")
    
    while True:
        choice = input("\nEnter ROCm version to use (5.7 or 6.0, default 5.7): ").strip()
        if not choice:
            choice = "5.7"
        if choice in ["5.7", "6.0"]:
            break
        print("Invalid choice. Please enter 5.7 or 6.0.")
    
    # Install PyTorch
    if install_pytorch_rocm(choice):
        verify_installation()
    else:
        print("\n💡 If installation failed, try:")
        print("  1. Check your internet connection")
        print("  2. Try a different ROCm version")
        print("  3. Check if your GPU is supported")

if __name__ == "__main__":
    main() 