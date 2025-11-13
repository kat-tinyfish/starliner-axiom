"""
Pre-flight dependency checker.
This runs at startup to ensure all required packages are installed.
"""

import sys

# Critical packages (app won't run without these)
CRITICAL_PACKAGES = {
    "streamlit": "streamlit",
    "supabase": "supabase",
    "pandas": "pandas",
    "plotly": "plotly",
}

# Optional packages (app will warn but still run)
OPTIONAL_PACKAGES = {
    "aiohttp": "aiohttp",
    "openai": "openai",
    "anthropic": "anthropic",
    "google.generativeai": "google-generativeai",
    "playwright.async_api": "playwright",
    "PIL": "pillow",
    "pydantic": "pydantic",
}

missing_critical = []
missing_optional = []

for import_name, package_name in CRITICAL_PACKAGES.items():
    try:
        __import__(import_name)
    except ImportError:
        missing_critical.append(package_name)

for import_name, package_name in OPTIONAL_PACKAGES.items():
    try:
        __import__(import_name)
    except ImportError:
        missing_optional.append(package_name)

# Critical packages missing - cannot run
if missing_critical:
    print("=" * 70)
    print("❌ MISSING CRITICAL PACKAGES - Cannot Start")
    print("=" * 70)
    print("\nThe following critical packages are missing:")
    for pkg in missing_critical:
        print(f"  - {pkg}")
    print("\n🔧 TO FIX: pip install -r requirements.txt")
    print("=" * 70)
    sys.exit(1)

# Optional packages missing - warn but continue
if missing_optional:
    print("=" * 70)
    print("⚠️  OPTIONAL PACKAGES MISSING")
    print("=" * 70)
    print("\nThe following optional packages are missing:")
    for pkg in missing_optional:
        print(f"  - {pkg}")
    print("\n📝 Some features may not work:")
    if "aiohttp" in missing_optional:
        print("  • BrowserBase integration requires aiohttp")
    if "openai" in missing_optional:
        print("  • GPT-4 agent requires openai")
    if "anthropic" in missing_optional:
        print("  • Claude agent requires anthropic")
    if "google-generativeai" in missing_optional:
        print("  • Gemini agent requires google-generativeai")
    if "playwright" in missing_optional:
        print("  • Browser automation requires playwright")
    
    print("\n🔧 TO FIX: pip install -r requirements.txt")
    print("=" * 70)
    print()

print("✅ Core packages installed - Starting app...")

