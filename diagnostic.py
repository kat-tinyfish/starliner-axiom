"""
Diagnostic script to check installed packages and environment.
Run this to debug dependency issues.
"""

import sys
import subprocess

print("=" * 60)
print("SYSTEM DIAGNOSTICS")
print("=" * 60)

print(f"\n📍 Python Version: {sys.version}")
print(f"📍 Python Executable: {sys.executable}")
print(f"📍 Python Path: {sys.path}")

print("\n" + "=" * 60)
print("CHECKING KEY PACKAGES")
print("=" * 60)

packages_to_check = [
    "streamlit",
    "aiohttp",
    "playwright",
    "supabase",
    "openai",
    "anthropic",
    "google-generativeai",
    "pillow",
    "pandas",
    "plotly"
]

for package in packages_to_check:
    try:
        __import__(package.replace("-", "_"))
        print(f"✅ {package}")
    except ImportError as e:
        print(f"❌ {package} - NOT INSTALLED")
        print(f"   Error: {e}")

print("\n" + "=" * 60)
print("INSTALLED PACKAGES (pip freeze)")
print("=" * 60)

try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
except Exception as e:
    print(f"Could not run pip list: {e}")

print("\n" + "=" * 60)
print("ENVIRONMENT VARIABLES")
print("=" * 60)

import os
env_vars = [
    "BROWSERBASE_API_KEY",
    "BROWSERBASE_PROJECT_ID",
    "SUPABASE_URL",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "AWS_LAMBDA_FUNCTION_URL"
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        # Mask API keys
        if "KEY" in var or "URL" in var and "supabase" not in var.lower():
            masked = value[:10] + "..." if len(value) > 10 else "***"
            print(f"✅ {var}: {masked}")
        else:
            print(f"✅ {var}: {value[:30]}...")
    else:
        print(f"❌ {var}: NOT SET")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)

