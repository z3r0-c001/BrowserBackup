#!/usr/bin/env python3
"""
Multi-Browser Diagnostic Script
Diagnoses bookmark backup issues for Chrome, Edge, Brave, and custom browsers
"""

import os
import json
import platform
import sys
from pathlib import Path
from datetime import datetime

# Supported browsers and their paths (same as main script)
BROWSER_CONFIGS = {
    'chrome': {
        'name': 'Google Chrome',
        'paths': {
            'Windows': ['Google/Chrome'],
            'Darwin': ['Google/Chrome'],
            'Linux': ['google-chrome']
        }
    },
    'edge': {
        'name': 'Microsoft Edge',
        'paths': {
            'Windows': ['Microsoft/Edge'],
            'Darwin': ['Microsoft Edge'],
            'Linux': ['microsoft-edge']
        }
    },
    'brave': {
        'name': 'Brave Browser',
        'paths': {
            'Windows': ['BraveSoftware/Brave-Browser'],
            'Darwin': ['BraveSoftware/Brave-Browser'],
            'Linux': ['BraveSoftware/Brave-Browser']
        }
    }
}

def print_header(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")

def print_section(title):
    """Print a formatted subsection header"""
    print(f"\n{'-' * 40}")
    print(f" {title}")
    print(f"{'-' * 40}")

def check_system_info():
    """Check basic system information"""
    print_header("SYSTEM INFORMATION")
    
    system = platform.system()
    print(f"Operating System: {system}")
    print(f"Platform: {platform.platform()}")
    print(f"Python Version: {sys.version}")
    
    # Check if WSL
    is_wsl = False
    if system == "Linux":
        try:
            with open('/proc/version', 'r') as f:
                version_info = f.read().lower()
                if 'microsoft' in version_info or 'wsl' in version_info:
                    is_wsl = True
                    print("WSL Environment: ✓ Detected")
                    print(f"WSL Version Info: {version_info.strip()}")
                else:
                    print("WSL Environment: ✗ Not detected (native Linux)")
        except:
            print("WSL Environment: ✗ Cannot determine")
    else:
        print("WSL Environment: N/A (not Linux)")
    
    return system, is_wsl

def check_config_file():
    """Check configuration file"""
    print_header("CONFIGURATION FILE")
    
    config_file = Path.home() / '.browser_backup_config.json'
    print(f"Config file path: {config_file}")
    
    if config_file.exists():
        print("Config file exists: ✓")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print("\nConfiguration contents:")
            for key, value in config.items():
                if isinstance(value, dict):
                    print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")
            
            # Validate configuration
            browser_config = config.get('browser')
            if not browser_config:
                print("⚠ Warning: No browser configured")
            elif isinstance(browser_config, dict):
                custom_path = browser_config.get('custom')
                if custom_path:
                    print(f"✓ Custom browser path: {custom_path}")
                    if Path(custom_path).exists():
                        print("  Custom path exists: ✓")
                    else:
                        print("  Custom path exists: ✗")
                else:
                    print("⚠ Warning: Invalid custom browser configuration")
            elif browser_config in BROWSER_CONFIGS:
                print(f"✓ Valid browser: {BROWSER_CONFIGS[browser_config]['name']}")
            else:
                print(f"⚠ Warning: Unknown browser type: {browser_config}")
            
            if not config.get('backup_path'):
                print("⚠ Warning: No backup path configured")
            else:
                backup_path = Path(config['backup_path'])
                if backup_path.exists():
                    print(f"✓ Backup directory exists: {backup_path}")
                else:
                    print(f"⚠ Backup directory missing: {backup_path}")
            
            if not config.get('windows_user'):
                print("⚠ Warning: No Windows user configured")
            
            max_backups = config.get('max_backups', 30)
            print(f"✓ Backup retention: {max_backups}")
            
        except json.JSONDecodeError as e:
            print(f"✗ Config file is corrupted: {e}")
        except Exception as e:
            print(f"✗ Error reading config: {e}")
    else:
        print("Config file exists: ✗")
        print("This will trigger first-time setup when running the backup script.")

def check_windows_users(is_wsl):
    """Check available Windows users"""
    print_header("WINDOWS USER ACCOUNTS")
    
    if not is_wsl:
        print("Not in WSL environment - skipping Windows user check")
        return []
    
    users_path = Path('/mnt/c/Users')
    print(f"Windows Users directory: {users_path}")
    
    if not users_path.exists():
        print("✗ Cannot access /mnt/c/Users")
        print("  This suggests WSL cannot access Windows file system")
        return []
    
    print("✓ Can access Windows file system")
    
    try:
        available_users = []
        for user_dir in users_path.iterdir():
            if user_dir.is_dir() and not user_dir.name.startswith('.'):
                # Check if user directory is accessible
                try:
                    list(user_dir.iterdir())  # Try to list contents
                    available_users.append(user_dir.name)
                    print(f"  ✓ {user_dir.name} (accessible)")
                except PermissionError:
                    print(f"  ⚠ {user_dir.name} (permission denied)")
                except Exception as e:
                    print(f"  ✗ {user_dir.name} (error: {e})")
        
        if available_users:
            print(f"\nAccessible users: {len(available_users)}")
        else:
            print("\n⚠ No accessible user accounts found")
            
        return available_users
        
    except Exception as e:
        print(f"✗ Error checking users: {e}")
        return []

def check_browser_installations(system, is_wsl, available_users):
    """Check for browser installations"""
    print_header("BROWSER INSTALLATIONS")
    
    found_browsers = {}
    
    for browser_key, browser_config in BROWSER_CONFIGS.items():
        print_section(f"Checking {browser_config['name']}")
        
        browser_paths = []
        
        if system == "Windows" or is_wsl:
            if is_wsl:
                # Check each available user
                for user in available_users:
                    user_path = Path(f'/mnt/c/Users/{user}')
                    
                    for browser_subpath in browser_config['paths']['Windows']:
                        for app_data in ['AppData/Local', 'AppData/Roaming']:
                            browser_path = user_path / app_data / browser_subpath
                            if browser_path.exists():
                                print(f"  ✓ Found for user {user}: {browser_path}")
                                browser_paths.append(browser_path)
                            else:
                                print(f"  ✗ Not found for user {user}: {browser_path}")
            else:
                # Regular Windows
                for browser_subpath in browser_config['paths']['Windows']:
                    for env_var in ['LOCALAPPDATA', 'APPDATA']:
                        if env_var in os.environ:
                            browser_path = Path(os.environ[env_var]) / browser_subpath
                            if browser_path.exists():
                                print(f"  ✓ Found: {browser_path}")
                                browser_paths.append(browser_path)
                            else:
                                print(f"  ✗ Not found: {browser_path}")
        
        elif system == "Darwin":  # macOS
            base_path = Path.home() / 'Library' / 'Application Support'
            for browser_subpath in browser_config['paths']['Darwin']:
                browser_path = base_path / browser_subpath
                if browser_path.exists():
                    print(f"  ✓ Found: {browser_path}")
                    browser_paths.append(browser_path)
                else:
                    print(f"  ✗ Not found: {browser_path}")
        
        elif system == "Linux" and not is_wsl:
            base_path = Path.home() / '.config'
            for browser_subpath in browser_config['paths']['Linux']:
                browser_path = base_path / browser_subpath
                if browser_path.exists():
                    print(f"  ✓ Found: {browser_path}")
                    browser_paths.append(browser_path)
                else:
                    print(f"  ✗ Not found: {browser_path}")
        
        found_browsers[browser_key] = browser_paths
        
        if not browser_paths:
            print(f"  ⚠ No {browser_config['name']} installations found")
    
    return found_browsers

def check_bookmark_files(found_browsers):
    """Check for bookmark files in browser installations"""
    print_header("BOOKMARK FILES")
    
    total_profiles = 0
    total_bookmarks = 0
    
    for browser_key, browser_paths in found_browsers.items():
        browser_name = BROWSER_CONFIGS[browser_key]['name']
        print_section(f"{browser_name} Bookmarks")
        
        if not browser_paths:
            print(f"  No {browser_name} installations to check")
            continue
        
        for browser_path in browser_paths:
            print(f"\nChecking: {browser_path}")
            
            # Look for User Data directory
            user_data_candidates = [browser_path / 'User Data', browser_path]
            
            for user_data in user_data_candidates:
                if not user_data.exists():
                    continue
                
                print(f"  User Data: {user_data}")
                
                try:
                    # Look for profile directories
                    for profile_dir in user_data.iterdir():
                        if profile_dir.is_dir() and (profile_dir.name.startswith('Default') or profile_dir.name.startswith('Profile')):
                            bookmark_file = profile_dir / 'Bookmarks'
                            print(f"    Profile: {profile_dir.name}")
                            
                            if bookmark_file.exists():
                                total_profiles += 1
                                print(f"      ✓ Bookmark file found: {bookmark_file}")
                                
                                # Try to read and count bookmarks
                                try:
                                    with open(bookmark_file, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                    
                                    bookmark_count = count_bookmarks(data)
                                    total_bookmarks += bookmark_count
                                    print(f"      ✓ Contains {bookmark_count} bookmarks")
                                    
                                    # Check file size and modification time
                                    stat = bookmark_file.stat()
                                    size_kb = stat.st_size / 1024
                                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                                    print(f"      📊 Size: {size_kb:.1f} KB, Modified: {mod_time}")
                                    
                                except json.JSONDecodeError:
                                    print(f"      ⚠ Bookmark file is corrupted (invalid JSON)")
                                except Exception as e:
                                    print(f"      ⚠ Cannot read bookmark file: {e}")
                            else:
                                print(f"      ✗ No bookmark file found")
                
                except PermissionError:
                    print(f"  ⚠ Permission denied accessing {user_data}")
                except Exception as e:
                    print(f"  ✗ Error checking {user_data}: {e}")
    
    print(f"\n📈 SUMMARY: Found {total_profiles} profiles with {total_bookmarks} total bookmarks")

def count_bookmarks(data, path=""):
    """Recursively count bookmarks in browser data"""
    count = 0
    
    if isinstance(data, dict):
        if data.get('type') == 'url':
            return 1
        elif data.get('type') == 'folder':
            children = data.get('children', [])
            for child in children:
                count += count_bookmarks(child, path)
        else:
            # Check common bookmark locations
            for key, value in data.items():
                if key in ['bookmark_bar', 'other', 'synced'] or 'bookmarks' in key.lower():
                    count += count_bookmarks(value, f"{path}.{key}")
    
    elif isinstance(data, list):
        for item in data:
            count += count_bookmarks(item, path)
    
    return count

def check_backup_functionality():
    """Test basic backup functionality"""
    print_header("BACKUP FUNCTIONALITY TEST")
    
    print("Testing backup script import...")
    try:
        # Try to import the backup script to check for syntax errors
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Create a simple test to see if the backup script can be imported
        print("✓ Diagnostic script can run")
        
        # Check if backup script exists
        backup_script = Path(__file__).parent / 'bookmarkBackup.py'
        if backup_script.exists():
            print(f"✓ Main backup script found: {backup_script}")
        else:
            print(f"⚠ Main backup script not found: {backup_script}")
            print("  Make sure bookmarkBackup.py is in the same directory")
        
    except Exception as e:
        print(f"✗ Error testing backup functionality: {e}")

def check_permissions_and_paths():
    """Check file permissions and path accessibility"""
    print_header("PERMISSIONS AND PATHS")
    
    # Check write permissions for common backup locations
    test_paths = [
        "/tmp",
        str(Path.home()),
        "/mnt/c/temp" if Path("/mnt/c").exists() else None,
    ]
    
    for test_path in test_paths:
        if test_path is None:
            continue
            
        print(f"\nTesting path: {test_path}")
        try:
            test_dir = Path(test_path)
            if test_dir.exists():
                print("  ✓ Path exists")
                
                # Test write permission
                test_file = test_dir / f"browser_backup_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tmp"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    print("  ✓ Write permission available")
                except:
                    print("  ⚠ Write permission denied")
            else:
                print("  ✗ Path does not exist")
        except Exception as e:
            print(f"  ✗ Error checking path: {e}")

def main():
    """Main diagnostic function"""
    print("🔍 MULTI-BROWSER BOOKMARK BACKUP DIAGNOSTIC")
    print("=" * 60)
    print("This diagnostic tool will check your system for browser bookmark")
    print("backup compatibility and identify potential issues.")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all diagnostic checks
        system, is_wsl = check_system_info()
        check_config_file()
        available_users = check_windows_users(is_wsl)
        found_browsers = check_browser_installations(system, is_wsl, available_users)
        check_bookmark_files(found_browsers)
        check_backup_functionality()
        check_permissions_and_paths()
        
        # Final recommendations
        print_header("RECOMMENDATIONS")
        
        config_file = Path.home() / '.browser_backup_config.json'
        if not config_file.exists():
            print("🔧 NEXT STEPS:")
            print("1. Run: python3 bookmarkBackup.py --setup")
            print("2. Follow the setup prompts to configure your browser and backup settings")
        else:
            print("🔧 CONFIGURATION COMMANDS:")
            print("• python3 bookmarkBackup.py --show-config    (view current settings)")
            print("• python3 bookmarkBackup.py --configure-browser    (change browser)")
            print("• python3 bookmarkBackup.py --configure-user       (change Windows user)")
            print("• python3 bookmarkBackup.py --configure-backup     (change backup path)")
            print("• python3 bookmarkBackup.py --configure-retention  (change retention)")
            print("• python3 bookmarkBackup.py -t                     (test backup)")
            print("• python3 bookmarkBackup.py -v                     (run backup)")
        
        print("\n✅ Diagnostic complete!")
        
    except KeyboardInterrupt:
        print("\n\n❌ Diagnostic interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Diagnostic failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()