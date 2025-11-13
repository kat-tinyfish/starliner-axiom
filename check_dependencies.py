"""
Pre-flight dependency checker.
This runs at startup to ensure all required packages are installed.
"""

import sys

REQUIRED_PACKAGES = {
    "streamlit": "streamlit",
    "aiohttp": "aiohttp",
    "supabase": "supabase",
    "openai": "openai",
    "anthropic": "anthropic",
    "google.generativeai": "google-generativeai",
    "playwright.async_api": "playwright",
    "PIL": "pillow",
    "pandas": "pandas",
    "plotly": "plotly",
    "pydantic": "pydantic",
}

missing_packages = []

for import_name, package_name in REQUIRED_PACKAGES.items():
    try:
        __import__(import_name)
    except ImportError:
        missing_packages.append(package_name)

if missing_packages:
    print("=" * 70)
    print("❌ MISSING REQUIRED PACKAGES")
    print("=" * 70)
    print("\nThe following packages are missing:")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    
    print("\n📝 This usually means Streamlit Cloud is using a cached environment.")
    print("\n🔧 TO FIX:")
    print("   1. Go to your Streamlit Cloud app")
    print("   2. Click '⋮' menu → 'Reboot app'")
    print("   3. Check 'Clear cache' ✅")
    print("   4. Click 'Reboot'")
    print("\n   OR delete and redeploy the app for a completely fresh start.")
    print("=" * 70)
    sys.exit(1)

print("✅ All required packages are installed")

