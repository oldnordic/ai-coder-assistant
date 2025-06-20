#!/usr/bin/env python3
"""
Comprehensive build script for AI Coder Assistant
Creates optimized binaries for all platforms
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path

class Builder:
    def __init__(self, component=None):
        self.platform = platform.system().lower()
        self.dist_dir = Path("dist")
        self.build_dir = Path("build")
        self.specs_dir = Path("specs")
        self.component = component
        
        # Create directories
        self.dist_dir.mkdir(exist_ok=True)
        self.build_dir.mkdir(exist_ok=True)
        self.specs_dir.mkdir(exist_ok=True)
    
    def clean(self):
        """Clean previous builds"""
        print("🧹 Cleaning previous builds...")
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.dist_dir.mkdir()
        self.build_dir.mkdir()
    
    def create_component_main(self, component_name):
        """Create main entry point for component"""
        main_content = f'''#!/usr/bin/env python3
"""
AI Coder Assistant - {component_name.title()} Component
"""

import sys
import os

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

{self.get_component_init(component_name)}

def main():
    """Main entry point for {component_name} component"""
    try:
        {self.get_component_run(component_name)}
    except Exception as e:
        print(f"Error in {component_name} component: {{e}}")
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
        
        main_file = Path(f"{component_name}_main.py")
        main_file.write_text(main_content)
        return main_file
    
    def get_component_init(self, component_name):
        """Get component initialization code"""
        init_map = {
            'assistant': '''
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QCoreApplication
        from frontend.ui.main_window import AICoderAssistant
        from backend.services.logging_config import setup_logging
        
        # Setup logging
        setup_logging()
        
        # Create Qt application
        app = QApplication(sys.argv)
        QCoreApplication.setOrganizationName("AICoderOrg")
        QCoreApplication.setApplicationName("AICoderAssistant")
''',
            'cli': '''
        from cli.main import main as cli_main
        import argparse
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='AI Coder Assistant CLI')
        parser.add_argument('command', help='Command to execute')
        parser.add_argument('--config', help='Configuration file')
        args = parser.parse_args()
''',
            'api': '''
        from backend.services.web_server import start_server
        import argparse
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='AI Coder Assistant API Server')
        parser.add_argument('--host', default='localhost', help='Host to bind to')
        parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
        args = parser.parse_args()
''',
            'scanner': '''
        from backend.services.scanner import ScannerService
        import argparse
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Code Scanner')
        parser.add_argument('--path', required=True, help='Path to scan')
        parser.add_argument('--output', help='Output file for results')
        args = parser.parse_args()
''',
            'trainer': '''
        from backend.services.trainer import TrainerService
        import argparse
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Model Trainer')
        parser.add_argument('--data', required=True, help='Training data path')
        parser.add_argument('--output', help='Output model path')
        args = parser.parse_args()
'''
        }
        return init_map.get(component_name, '')
    
    def get_component_run(self, component_name):
        """Get component run code"""
        run_map = {
            'assistant': '''
        # Create and show main window
        window = AICoderAssistant()
        window.show()
        sys.exit(app.exec())
''',
            'cli': '''
        # Run CLI
        cli_main(args.command, config_file=args.config)
''',
            'api': '''
        # Start API server
        start_server(host=args.host, port=args.port)
''',
            'scanner': '''
        # Initialize scanner service
        scanner = ScannerService()
        
        # Scan codebase
        results = scanner.scan_directory(args.path)
        
        # Output results
        if args.output:
            import json
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            print(f"Found {{len(results)}} files with issues")
''',
            'trainer': '''
        # Initialize trainer service
        trainer = TrainerService()
        
        # Train model
        trainer.train_model(args.data, output_path=args.output)
        print("Training completed successfully")
'''
        }
        return run_map.get(component_name, '')
    
    def create_spec_file(self, component_name):
        """Create PyInstaller spec file for component"""
        spec_content = self.get_spec_content(component_name)
        spec_file = self.specs_dir / f"{component_name}.spec"
        spec_file.write_text(spec_content)
        return spec_file
    
    def get_spec_content(self, component_name):
        """Get spec file content for component"""
        spec_map = {
            'assistant': '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['assistant_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend/ui', 'ui'),
        ('backend/services/logging_config.py', 'core'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtWebEngineWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'torch', 'transformers', 'datasets',
        'requests', 'beautifulsoup4', 'networkx',
        'yt-dlp', 'youtube_transcript_api'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ai-coder-assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
''',
            'cli': '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cli_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('cli', 'cli'),
    ],
    hiddenimports=[
        'argparse',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6', 'matplotlib', 'pandas', 'scipy',
        'requests', 'beautifulsoup4', 'yt-dlp',
        'youtube_transcript_api', 'PyPDF2'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ai-coder-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
''',
            'api': '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['api_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend/services', 'services'),
    ],
    hiddenimports=[
        'argparse',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6', 'matplotlib', 'pandas', 'scipy',
        'requests', 'beautifulsoup4', 'yt-dlp',
        'youtube_transcript_api', 'PyPDF2'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ai-coder-api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
''',
            'scanner': '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['scanner_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend/services/scanner.py', 'core'),
    ],
    hiddenimports=[
        'pathspec',
        'networkx',
        'subprocess',
        're',
        'os',
        'sys',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6', 'torch', 'transformers',
        'requests', 'beautifulsoup4', 'yt-dlp',
        'youtube_transcript_api', 'PyPDF2'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ai-coder-scanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
''',
            'trainer': '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['trainer_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('backend/services/trainer.py', 'training'),
    ],
    hiddenimports=[
        'torch',
        'datasets',
        'transformers',
        'json',
        'os',
        'sys',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6', 'requests', 'beautifulsoup4',
        'networkx', 'yt-dlp', 'youtube_transcript_api'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ai-coder-trainer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
        }
        return spec_map.get(component_name, '')
    
    def build_component(self, component_name):
        """Build a specific component"""
        print(f"🔨 Building {component_name} component...")
        
        # Create component main file
        main_file = self.create_component_main(component_name)
        
        # Create spec file
        spec_file = self.create_spec_file(component_name)
        
        # Build with PyInstaller
        try:
            subprocess.run([
                "pyinstaller", "--clean", "--distpath", str(self.dist_dir),
                str(spec_file)
            ], check=True)
            print(f"✅ {component_name} component built successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error building {component_name} component: {e}")
            return False
        
        # Clean up main file
        main_file.unlink()
        
        return True
    
    def build_assistant(self):
        """Build the assistant application"""
        return self.build_component('assistant')
    
    def build_cli(self):
        """Build the CLI application"""
        return self.build_component('cli')
    
    def build_api(self):
        """Build the API server"""
        return self.build_component('api')
    
    def build_scanner(self):
        """Build the code scanner"""
        return self.build_component('scanner')
    
    def build_trainer(self):
        """Build the model trainer"""
        return self.build_component('trainer')
    
    def optimize_binaries(self):
        """Apply UPX compression and other optimizations"""
        print("⚡ Optimizing binaries...")
        binaries = [
            "ai-coder-assistant",
            "ai-coder-cli",
            "ai-coder-api",
            "ai-coder-scanner",
            "ai-coder-trainer"
        ]
        
        for binary in binaries:
            binary_path = self.dist_dir / binary
            if self.platform == "windows":
                binary_path = binary_path.with_suffix('.exe')
            
            if binary_path.exists():
                try:
                    # Apply UPX compression
                    subprocess.run([
                        "upx", "--best", "--lzma", str(binary_path)
                    ], check=True)
                    print(f"✅ Optimized {binary}")
                except subprocess.CalledProcessError:
                    print(f"⚠️  UPX optimization failed for {binary} (continuing)")
                except FileNotFoundError:
                    print(f"⚠️  UPX not found, skipping optimization for {binary}")
    
    def create_launcher(self):
        """Create main launcher script"""
        print("🚀 Creating launcher...")
        launcher_content = self.get_launcher_content()
        launcher_path = self.dist_dir / "launcher.py"
        launcher_path.write_text(launcher_content)
        
        # Build launcher
        try:
            subprocess.run([
                "pyinstaller", "--onefile", "--name=ai-coder-launcher",
                "--distpath", str(self.dist_dir), str(launcher_path)
            ], check=True)
            print("✅ Launcher created successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating launcher: {e}")
        
        # Clean up launcher script
        launcher_path.unlink()
    
    def get_launcher_content(self):
        """Generate launcher script content"""
        return '''#!/usr/bin/env python3
"""
AI Coder Assistant - Modular Launcher
"""

import os
import sys
import subprocess
from pathlib import Path

def get_binary_path(name):
    """Get path to binary executable"""
    base_dir = Path(__file__).parent
    if sys.platform == "win32":
        return base_dir / f"{name}.exe"
    else:
        return base_dir / name

def main():
    """Main launcher function"""
    if len(sys.argv) < 2:
        print("AI Coder Assistant - Modular Launcher")
        print("Usage: launcher <component> [args...]")
        print("")
        print("Components:")
        print("  assistant - Main GUI application")
        print("  cli       - Command-line interface")
        print("  api       - API server")
        print("  scanner   - Code scanning and linting")
        print("  trainer   - Model training and fine-tuning")
        print("")
        print("Examples:")
        print("  launcher assistant")
        print("  launcher cli --command analyze --config config.yaml")
        print("  launcher api --host 0.0.0.0 --port 8000")
        print("  launcher scanner --path /path/to/code")
        sys.exit(1)
    
    component = sys.argv[1]
    args = sys.argv[2:]
    
    binary_map = {
        "assistant": "ai-coder-assistant",
        "cli": "ai-coder-cli",
        "api": "ai-coder-api",
        "scanner": "ai-coder-scanner",
        "trainer": "ai-coder-trainer"
    }
    
    if component not in binary_map:
        print(f"Unknown component: {component}")
        print("Available components:", ", ".join(binary_map.keys()))
        sys.exit(1)
    
    binary_name = binary_map[component]
    binary_path = get_binary_path(binary_name)
    
    if not binary_path.exists():
        print(f"Binary not found: {binary_path}")
        print("Please ensure all components are built correctly.")
        sys.exit(1)
    
    # Run the component
    try:
        subprocess.run([str(binary_path)] + args)
    except KeyboardInterrupt:
        print("\\nOperation cancelled by user")
    except Exception as e:
        print(f"Error running {component}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    def create_package(self):
        """Create final package"""
        print("📦 Creating final package...")
        
        # Create shared directories
        shared_dir = self.dist_dir / "shared"
        shared_dir.mkdir(exist_ok=True)
        
        for subdir in ["models", "config", "data"]:
            (shared_dir / subdir).mkdir(exist_ok=True)
        
        # Copy configuration files
        config_files = [
            "requirements.txt",
            "README.md",
            "docs/",
            ".ai_coder_ignore"
        ]
        
        for file in config_files:
            if Path(file).exists():
                if Path(file).is_dir():
                    shutil.copytree(file, self.dist_dir / file, dirs_exist_ok=True)
                else:
                    shutil.copy2(file, self.dist_dir)
        
        # Create run script
        run_script = self.get_run_script()
        run_path = self.dist_dir / "run.py"
        run_path.write_text(run_script)
        
        # Make run script executable on Unix systems
        if self.platform != "windows":
            os.chmod(run_path, 0o755)
    
    def get_run_script(self):
        """Generate run script content"""
        return '''#!/usr/bin/env python3
"""
AI Coder Assistant - Modular Launcher
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Set up environment
    base_dir = Path(__file__).parent
    os.chdir(base_dir)
    
    # Check if running from source or binary
    if Path("main.py").exists():
        # Running from source
        print("Starting AI Coder Assistant from source...")
        subprocess.run([sys.executable, "main.py"])
    else:
        # Running from binary
        launcher_path = base_dir / "ai-coder-launcher"
        if sys.platform == "win32":
            launcher_path = launcher_path.with_suffix('.exe')
        
        if launcher_path.exists():
            print("Starting AI Coder Assistant...")
            subprocess.run([str(launcher_path), "assistant"])
        else:
            print("Launcher not found. Please run from source or rebuild.")
            print("To rebuild, run: python build_all.py")
            sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    def build_all(self):
        """Build all components"""
        print("🚀 Starting comprehensive build...")
        print(f"📁 Platform: {self.platform}")
        print(f"📁 Output directory: {self.dist_dir.absolute()}")
        
        if self.component:
            # Build specific component
            if self.component == 'assistant':
                success = self.build_assistant()
            elif self.component == 'cli':
                success = self.build_cli()
            elif self.component == 'api':
                success = self.build_api()
            elif self.component == 'scanner':
                success = self.build_scanner()
            elif self.component == 'trainer':
                success = self.build_trainer()
            else:
                print(f"❌ Unknown component: {self.component}")
                return False
            
            if success:
                self.optimize_binaries()
                print(f"✅ {self.component} component built successfully!")
            else:
                print(f"❌ Failed to build {self.component} component")
                return False
        else:
            # Build all components
            self.clean()
            
            components = [
                ('assistant', self.build_assistant),
                ('cli', self.build_cli),
                ('api', self.build_api),
                ('scanner', self.build_scanner),
                ('trainer', self.build_trainer)
            ]
            
            for name, build_func in components:
                if not build_func():
                    print(f"❌ Failed to build {name} component")
                    return False
            
            self.optimize_binaries()
            self.create_launcher()
            self.create_package()
            
            print("✅ All components built successfully!")
        
        print(f"📁 Output directory: {self.dist_dir.absolute()}")
        return True

def main():
    parser = argparse.ArgumentParser(description='Build AI Coder Assistant binaries')
    parser.add_argument('--component', choices=['assistant', 'cli', 'api', 'scanner', 'trainer'],
                       help='Build specific component only')
    parser.add_argument('--clean', action='store_true', help='Clean build directories')
    
    args = parser.parse_args()
    
    builder = Builder(component=args.component)
    
    if args.clean:
        builder.clean()
        print("🧹 Build directories cleaned")
        return
    
    success = builder.build_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 