# check_gpu.py
import sys
import torch

def run_gpu_check():
    """
    Performs a series of checks to diagnose the PyTorch GPU setup.
    """
    print("--- PyTorch GPU Diagnostic ---")
    
    # 1. Python and PyTorch Versions
    print(f"Python Version: {sys.version}")
    print(f"PyTorch Version: {torch.__version__}")
    print("-" * 30)
    
    # 2. Check for CUDA/ROCm Availability
    is_available = torch.cuda.is_available()
    print(f"Is CUDA/ROCm available? \t\t--> {is_available}")
    
    if not is_available:
        print("\n[DIAGNOSIS] PyTorch cannot detect a compatible GPU.")
        print("This is likely because the installed version of PyTorch does not have support for your GPU's drivers (e.g., ROCm for AMD on Linux).")
        print("\n[ACTION] Please go to https://pytorch.org/get-started/locally/ and get the correct command.")
        print("  - Your selections should be: PyTorch Build (Stable), Your OS (Linux), Package (Pip), Compute Platform (ROCm).")
        print("  - You must run the specific installation command they provide.")
        print("-" * 30)
        return

    # 3. Check GPU Details if available
    print("-" * 30)
    device_count = torch.cuda.device_count()
    print(f"Number of available GPUs: \t\t--> {device_count}")
    
    # --- THIS IS THE CORRECTED BLOCK ---
    # Use getattr() to safely access the 'version' submodule, avoiding static analysis errors.
    version_module = getattr(torch, 'version', None)
    if version_module and hasattr(version_module, 'cuda'):
        build_version = version_module.cuda
        print(f"PyTorch was compiled with: \t--> CUDA/ROCm {build_version}")
    else:
        print("Could not determine the CUDA/ROCm version PyTorch was compiled with.")
    # --- END OF CORRECTION ---

    for i in range(device_count):
        print("-" * 10, f"GPU {i}", "-" * 10)
        try:
            device_name = torch.cuda.get_device_name(i)
            total_mem = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            print(f"  Device Name: \t\t\t--> {device_name}")
            print(f"  Total Memory: \t\t--> {total_mem:.2f} GB")
        except Exception as e:
            print(f"  Could not get details for GPU {i}: {e}")

    # 4. Simple GPU Operation Test
    print("-" * 30)
    print("Performing a simple test operation on the GPU...")
    try:
        tensor = torch.randn(3, 3).to("cuda")
        result = tensor * tensor
        result_cpu = result.to("cpu")
        print("  Test operation SUCCEEDED! Your GPU is ready for training.")
    except Exception as e:
        print(f"  Test operation FAILED: {e}")
        print("\n[DIAGNOSIS] PyTorch detects the GPU but failed a basic operation.")
        print("This can indicate a problem with your drivers or toolkit installation.")

    print("\n--- End of Diagnostic ---")


if __name__ == "__main__":
    run_gpu_check()