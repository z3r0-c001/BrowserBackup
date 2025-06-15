#!/usr/bin/env python3
"""
Debug script to check the bookmarkBackup.py file
"""

import os
import sys
from pathlib import Path

def check_script_content():
    script_path = Path("bookmarkBackup.py")
    
    print(f"🔍 Checking script: {script_path.absolute()}")
    print(f"File exists: {script_path.exists()}")
    
    if not script_path.exists():
        print("❌ Script file not found!")
        return
    
    print(f"File size: {script_path.stat().st_size} bytes")
    print(f"Modified: {script_path.stat().st_mtime}")
    
    # Check for old method references
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Look for problematic references
    old_refs = [
        '_get_brave_paths',
        'BraveBookmarkBackup',
        '.brave_backup_config.json'
    ]
    
    print("\n🔍 Checking for old references:")
    for ref in old_refs:
        count = content.count(ref)
        if count > 0:
            print(f"  ❌ Found '{ref}': {count} times")
            # Show line numbers
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if ref in line:
                    print(f"    Line {i}: {line.strip()}")
        else:
            print(f"  ✅ '{ref}': Not found")
    
    # Check for new references
    new_refs = [
        '_get_browser_paths',
        'BrowserBookmarkBackup',
        '.browser_backup_config.json'
    ]
    
    print("\n🔍 Checking for new references:")
    for ref in new_refs:
        count = content.count(ref)
        if count > 0:
            print(f"  ✅ Found '{ref}': {count} times")
        else:
            print(f"  ❌ Missing '{ref}'")

def check_python_cache():
    print("\n🔍 Checking Python cache files:")
    
    # Check for __pycache__ directory
    pycache_dir = Path("__pycache__")
    if pycache_dir.exists():
        print(f"  Found __pycache__ directory: {pycache_dir}")
        cache_files = list(pycache_dir.glob("*.pyc"))
        print(f"  Cache files: {len(cache_files)}")
        for cache_file in cache_files:
            print(f"    {cache_file}")
        print("  ⚠️ Try removing cache: rm -rf __pycache__")
    else:
        print("  ✅ No __pycache__ directory found")
    
    # Check for .pyc files in current directory
    pyc_files = list(Path(".").glob("*.pyc"))
    if pyc_files:
        print(f"  Found .pyc files: {pyc_files}")
        print("  ⚠️ Try removing: rm *.pyc")
    else:
        print("  ✅ No .pyc files in current directory")

def check_multiple_scripts():
    print("\n🔍 Checking for multiple script versions:")
    
    possible_names = [
        "bookmarkBackup.py",
        "brave_backup.py", 
        "browser_backup.py",
        "BraveBookmarkBackup.py"
    ]
    
    for name in possible_names:
        path = Path(name)
        if path.exists():
            print(f"  Found: {path} ({path.stat().st_size} bytes)")
        else:
            print(f"  Not found: {name}")

def main():
    print("🐛 DEBUG: bookmarkBackup.py Script Check")
    print("=" * 50)
    
    check_script_content()
    check_python_cache()
    check_multiple_scripts()
    
    print("\n💡 SUGGESTED FIXES:")
    print("1. Clear Python cache: rm -rf __pycache__ *.pyc")
    print("2. Make sure you're editing the right file")
    print("3. Check file permissions: ls -la bookmarkBackup.py") 
    print("4. Try running: python3 -B bookmarkBackup.py (bypasses cache)")
    print("5. If still broken, download fresh copy from artifact")

if __name__ == "__main__":
    main()