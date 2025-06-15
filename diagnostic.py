#!/usr/bin/env python3

import os
import platform
import json
from pathlib import Path

def find_brave_installations():
    system = platform.system()
    print(f"Operating System: {system}")
    print(f"User Home: {Path.home()}")
    
    # Check if running in WSL
    is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
    if is_wsl:
        print("WSL detected - looking for Windows Brave installation")
    
    if system == "Windows" or is_wsl:
        if is_wsl:
            # WSL - look in Windows filesystem
            print("Checking Windows user directories...")
            users_dir = Path('/mnt/c/Users')
            
            if users_dir.exists():
                print(f"Found Users directory: {users_dir}")
                accessible_users = []
                
                for user_dir in users_dir.iterdir():
                    if user_dir.is_dir() and user_dir.name not in ['Public', 'Default', 'All Users', 'Default User']:
                        try:
                            # Test if we can access AppData
                            appdata_local = user_dir / 'AppData' / 'Local'
                            if appdata_local.exists():
                                accessible_users.append(user_dir.name)
                                print(f"  ✓ Accessible user: {user_dir.name}")
                        except PermissionError:
                            print(f"  ✗ Permission denied: {user_dir.name}")
                        except Exception as e:
                            print(f"  ✗ Error accessing {user_dir.name}: {e}")
                
                # Check Brave for accessible users
                for username in accessible_users:
                    print(f"\nChecking Brave installation for user: {username}")
                    user_path = Path(f'/mnt/c/Users/{username}')
                    brave_paths = [
                        user_path / 'AppData' / 'Local' / 'BraveSoftware',
                        user_path / 'AppData' / 'Roaming' / 'BraveSoftware'
                    ]
                    
                    for brave_path in brave_paths:
                        try:
                            if brave_path.exists():
                                print(f"  ✓ Found: {brave_path}")
                                check_brave_directory(brave_path)
                            else:
                                print(f"  ✗ Not found: {brave_path}")
                        except PermissionError:
                            print(f"  ✗ Permission denied: {brave_path}")
                        except Exception as e:
                            print(f"  ✗ Error: {brave_path} - {e}")
            else:
                print("⚠ /mnt/c/Users not found - is Windows C: drive mounted?")
        else:
            # Regular Windows
            possible_paths = [
                Path(os.environ.get('LOCALAPPDATA', '')) / 'BraveSoftware',
                Path(os.environ.get('APPDATA', '')) / 'BraveSoftware',
                Path.home() / 'AppData' / 'Local' / 'BraveSoftware',
                Path.home() / 'AppData' / 'Roaming' / 'BraveSoftware'
            ]
            
            print("\nChecking possible Brave installation paths:")
            for path in possible_paths:
                check_brave_directory_safe(path)
                
    elif system == "Darwin":  # macOS
        possible_paths = [
            Path.home() / 'Library' / 'Application Support' / 'BraveSoftware',
            Path.home() / 'Library' / 'Preferences' / 'BraveSoftware'
        ]
        
        print("\nChecking possible Brave installation paths:")
        for path in possible_paths:
            check_brave_directory_safe(path)
            
    elif system == "Linux" and not is_wsl:
        possible_paths = [
            Path.home() / '.config' / 'BraveSoftware',
            Path.home() / '.brave',
            Path.home() / 'snap' / 'brave' / 'current' / '.config' / 'BraveSoftware'
        ]
        
        print("\nChecking possible Brave installation paths:")
        for path in possible_paths:
            check_brave_directory_safe(path)
    else:
        print(f"Unsupported OS: {system}")
        return

def check_brave_directory_safe(path):
    """Check Brave directory with proper error handling"""
    try:
        if path.exists():
            print(f"✓ Found: {path}")
            check_brave_directory(path)
        else:
            print(f"✗ Not found: {path}")
    except PermissionError:
        print(f"✗ Permission denied: {path}")
    except Exception as e:
        print(f"✗ Error checking {path}: {e}")

def check_brave_directory(brave_path):
    """Check a Brave directory for browser data"""
    try:
        # Look for browser directories
        if (brave_path / 'Brave-Browser').exists():
            browser_path = brave_path / 'Brave-Browser'
            print(f"  ✓ Browser data: {browser_path}")
            
            # Look for User Data
            user_data = browser_path / 'User Data'
            if user_data.exists():
                print(f"    ✓ User Data: {user_data}")
                
                # List all profiles
                for item in user_data.iterdir():
                    if item.is_dir() and (item.name.startswith('Default') or item.name.startswith('Profile')):
                        bookmark_file = item / 'Bookmarks'
                        if bookmark_file.exists():
                            print(f"      ✓ Bookmarks found: {bookmark_file}")
                            
                            # Check file size
                            size = bookmark_file.stat().st_size
                            print(f"        Size: {size} bytes")
                            
                            # Try to peek at content
                            try:
                                with open(bookmark_file, 'r', encoding='utf-8') as f:
                                    content = f.read(200)
                                    if '"roots"' in content:
                                        print(f"        ✓ Valid bookmark file")
                                    else:
                                        print(f"        ⚠ May not be valid bookmark file")
                            except Exception as e:
                                print(f"        ⚠ Cannot read file: {e}")
                        else:
                            print(f"      ✗ No bookmarks: {item}")
            else:
                print(f"    ✗ No User Data directory")
        else:
            print(f"  ✗ No Brave-Browser directory")
    except Exception as e:
        print(f"  ✗ Error checking directory: {e}")
    
    # Show config file location
    config_file = Path.home() / '.brave_backup_config.json'
    print(f"\nConfiguration file: {config_file}")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"Current configured user: {config.get('windows_user', 'None')}")
        except:
            print("Configuration file exists but cannot be read")
    else:
        print("No configuration file found")

if __name__ == "__main__":
    find_brave_installations()
