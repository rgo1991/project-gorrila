"""
Fix dependencies script - Ensures compatible versions are installed
Run this script to fix httpx compatibility issues
"""

import subprocess
import sys

def fix_dependencies():
    """Install compatible httpx version."""
    print("Fixing httpx compatibility issue...")
    try:
        # Uninstall current httpx
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "httpx", "-y"])
        print("[OK] Uninstalled httpx")
        
        # Install compatible version
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx==0.27.0"])
        print("[OK] Installed httpx 0.27.0")
        
        # Verify installation
        import httpx
        print(f"[OK] httpx version: {httpx.__version__}")
        
        # Test OpenAI client
        from openai import OpenAI
        client = OpenAI(api_key="test")
        print("[OK] OpenAI client initialized successfully")
        
        print("\n[SUCCESS] Dependencies fixed! You can now run web_app.py")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    fix_dependencies()

