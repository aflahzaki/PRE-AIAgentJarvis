#!/usr/bin/env python
"""
Helper script untuk menjalankan J.A.R.V.I.S dengan diagnostik lengkap
"""
import os
import sys
import subprocess

def check_dependencies():
    """Check if all required packages are installed"""
    print("=" * 70)
    print("CHECKING DEPENDENCIES")
    print("=" * 70)
    
    required = {
        'phi': 'phidata',
        'openai': 'openai',
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✓ {module} is installed")
        except ImportError:
            print(f"✗ {module} is NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    print("\n✓ All dependencies OK\n")
    return True

def verify_environment():
    """Verify environment setup"""
    print("=" * 70)
    print("ENVIRONMENT VERIFICATION")
    print("=" * 70)
    
    print(f"Python: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Current Directory: {os.getcwd()}")
    
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        key_preview = api_key[:20] + "..." if len(api_key) > 20 else api_key
        print(f"✓ OPENAI_API_KEY is set ({key_preview})")
    else:
        print("⚠ OPENAI_API_KEY not in environment (will use hardcoded key)")
    
    print(f"✓ Current working directory OK\n")
    return True

def run_jarvis():
    """Run the main J.A.R.V.I.S script"""
    print("=" * 70)
    print("RUNNING J.A.R.V.I.S AGENT")
    print("=" * 70)
    print()
    
    try:
        result = subprocess.run(
            [sys.executable, "jarvis_coder.py"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode
    except Exception as e:
        print(f"❌ Error running jarvis_coder.py: {e}")
        return 1

def main():
    """Main entry point"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " J.A.R.V.I.S AUTONOMOUS CODING AGENT - LAUNCHER ".center(68) + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("Please install missing dependencies and try again.")
        return 1
    
    # Step 2: Verify environment
    verify_environment()
    
    # Step 3: Run J.A.R.V.I.S
    exit_code = run_jarvis()
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✓ J.A.R.V.I.S execution completed successfully!")
    else:
        print("✗ J.A.R.V.I.S execution failed with exit code:", exit_code)
    print("=" * 70)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
