#!/usr/bin/env python3
"""
Script to clear Streamlit cache and restart the app
"""

import os
import shutil
import subprocess
import sys


def clear_streamlit_cache():
    """Clear Streamlit cache and restart"""

    print("🧹 Clearing Streamlit Cache")
    print("=" * 30)

    # Clear Streamlit cache directory
    cache_dir = os.path.expanduser("~/.streamlit")
    if os.path.exists(cache_dir):
        print(f"📁 Found cache directory: {cache_dir}")
        try:
            # Remove cache files
            for root, dirs, files in os.walk(cache_dir):
                for file in files:
                    if file.endswith(".cache"):
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        print(f"   Removed: {file}")
            print("✅ Cache cleared successfully")
        except Exception as e:
            print(f"⚠️  Could not clear cache: {e}")
    else:
        print("ℹ️  No cache directory found")

    # Clear Python cache
    print("\n🐍 Clearing Python cache...")
    try:
        subprocess.run(
            [sys.executable, "-Bc", "import compileall; compileall.compile_dir('.', force=True)"],
            capture_output=True,
        )
        print("✅ Python cache cleared")
    except Exception as e:
        print(f"⚠️  Could not clear Python cache: {e}")

    print("\n🚀 To restart the app:")
    print("1. Stop the current Streamlit app (Ctrl+C)")
    print("2. Run: streamlit run social_media_app.py")
    print("3. The app will use the updated configuration")


if __name__ == "__main__":
    clear_streamlit_cache()
