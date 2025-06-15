#!/usr/bin/env python3
"""
Multi-Browser Bookmark Backup Script
Automatically backs up browser bookmarks from WSL to a network location
Supports: Chrome, Edge, Brave, and custom browser paths
"""

import os
import json
import shutil
import platform
from datetime import datetime
import argparse
import sys
from pathlib import Path

# Default suggested backup directory (will prompt user on first run)
SUGGESTED_BACKUP_PATH = "/mnt/c/Users/user1/OneDrive/bookmarks"

# Supported browsers and their paths
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

class BrowserBookmarkBackup:
    def __init__(self, backup_destination=None, max_backups=30):
        self.config_file = Path.home() / '.browser_backup_config.json'
        self.max_backups = max_backups
        
        # Load or prompt for backup destination
        if backup_destination:
            self.backup_destination = Path(backup_destination)
        else:
            config = self._load_config()
            saved_path = config.get('backup_path')
            if saved_path:
                self.backup_destination = Path(saved_path)
            else:
                # Prompt for backup directory on first run
                print("\n=== First Time Setup: Backup Directory ===")
                backup_path = self._prompt_backup_directory()
                if backup_path:
                    self.backup_destination = Path(backup_path)
                    config['backup_path'] = backup_path
                    self._save_config(config)
                    print(f"\n✓ Backup directory saved: {backup_path}")
                    print(f"To change later, run: python3 {sys.argv[0]} --configure-backup")
                else:
                    raise ValueError("Backup directory is required")
        
        # Load or prompt for backup retention
        config = self._load_config()
        if 'max_backups' not in config:
            retention_count = self._prompt_backup_retention()
            if retention_count:
                self.max_backups = retention_count
                config['max_backups'] = retention_count
                self._save_config(config)
                print(f"\n✓ Backup retention set to: {retention_count} backups")
            else:
                self.max_backups = 30  # default
        else:
            self.max_backups = config.get('max_backups', 30)
        
        self.browser_paths = self._get_browser_paths()

    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}
    
    def _save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except OSError as e:
            print(f"Warning: Could not save configuration: {e}")

    def _prompt_backup_retention(self):
        """Prompt user to select backup retention count"""
        print("\n=== Backup Retention Setup ===")
        print("How many backup files should be kept?")
        print("  1. Keep 1 backup (only most recent)")
        print("  2. Keep 5 backups")
        print("  3. Keep 10 backups")
        print("  4. Keep 30 backups (recommended)")
        print("  5. Custom number")
        
        while True:
            try:
                choice = input("\nSelect retention option (1-5): ").strip()
                if choice == '1':
                    return 1
                elif choice == '2':
                    return 5
                elif choice == '3':
                    return 10
                elif choice == '4':
                    return 30
                elif choice == '5':
                    custom_count = input("Enter custom number of backups to keep: ").strip()
                    if custom_count.isdigit() and int(custom_count) > 0:
                        return int(custom_count)
                    else:
                        print("Please enter a valid positive number.")
                        continue
                else:
                    print("Invalid selection. Please choose 1-5.")
            except KeyboardInterrupt:
                print("\nUsing default: 30 backups")
                return 30
    
    def _prompt_backup_directory(self):
        """Prompt user to select backup directory"""
        print("\n=== Backup Directory Setup ===")
        print("Please specify where to store your bookmark backups.")
        print(f"Suggested location: {SUGGESTED_BACKUP_PATH}")
        print("\nExamples:")
        print("  - OneDrive: /mnt/c/Users/username/OneDrive/bookmarks")
        print("  - Network drive: /mnt/networkdrive/backups")
        print("  - Local folder: /home/username/bookmarks")
        print("  - Windows path: /mnt/c/backup/bookmarks")
        
        while True:
            try:
                choice = input(f"\nUse suggested location? (y/n): ").strip().lower()
                if choice in ['y', 'yes', '']:
                    return SUGGESTED_BACKUP_PATH
                elif choice in ['n', 'no']:
                    custom_path = input("Enter backup directory path: ").strip()
                    if custom_path:
                        # Test if we can create the directory
                        try:
                            test_path = Path(custom_path)
                            test_path.mkdir(parents=True, exist_ok=True)
                            print(f"✓ Backup directory set to: {custom_path}")
                            return custom_path
                        except Exception as e:
                            print(f"⚠ Cannot create directory {custom_path}: {e}")
                            continue
                    else:
                        print("Please enter a valid path.")
                        continue
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
            except KeyboardInterrupt:
                print("\nSetup cancelled.")
                return None

    def _select_browser(self):
        """Prompt user to select browser type"""
        print("\n=== Browser Selection ===")
        print("Select the browser you want to backup:")
        
        browser_list = []
        for i, (key, info) in enumerate(BROWSER_CONFIGS.items(), 1):
            print(f"  {i}. {info['name']}")
            browser_list.append(key)
        
        print(f"  {len(browser_list) + 1}. Custom browser (specify path)")
        
        while True:
            try:
                choice = input(f"\nSelect browser (1-{len(browser_list) + 1}): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(browser_list):
                        return browser_list[idx]
                    elif idx == len(browser_list):
                        # Custom browser option
                        custom_path = input("Enter custom browser data directory path: ").strip()
                        if custom_path:
                            return {'custom': custom_path}
                        else:
                            print("Please enter a valid path.")
                            continue
                print("Invalid selection. Please try again.")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None
    
    def _get_available_users(self):
        """Get list of available Windows user accounts"""
        users_path = Path('/mnt/c/Users')
        available_users = []
        
        if not users_path.exists():
            return available_users
        
        try:
            for user_dir in users_path.iterdir():
                if user_dir.is_dir() and not user_dir.name.startswith('.'):
                    # Check if user directory is accessible
                    try:
                        list(user_dir.iterdir())  # Try to list contents
                        available_users.append(user_dir.name)
                    except (PermissionError, OSError):
                        continue
        except Exception:
            pass
        
        return available_users
    
    def _select_user(self):
        """Prompt user to select Windows user account"""
        available_users = self._get_available_users()
        
        if not available_users:
            print("Error: No accessible Windows user accounts found")
            return None
        
        print("\n=== Windows User Selection ===")
        print("Available Windows user accounts:")
        for i, user in enumerate(available_users, 1):
            print(f"  {i}. {user}")
        
        while True:
            try:
                choice = input(f"\nSelect user account (1-{len(available_users)}): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_users):
                        return available_users[idx]
                print("Invalid selection. Please try again.")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None

    def _get_browser_paths(self):
        """Get browser bookmark file paths for different operating systems"""
        system = platform.system()
        paths = []
        
        # Check if running in WSL
        is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
        
        config = self._load_config()
        
        # Get browser selection
        selected_browser = config.get('browser')
        if not selected_browser:
            print("\n=== First Time Setup: Browser Selection ===")
            selected_browser = self._select_browser()
            if selected_browser:
                config['browser'] = selected_browser
                self._save_config(config)
                if isinstance(selected_browser, dict):
                    print(f"\n✓ Custom browser path configured: {selected_browser['custom']}")
                else:
                    browser_name = BROWSER_CONFIGS[selected_browser]['name']
                    print(f"\n✓ Browser '{browser_name}' configured for backups.")
                print(f"To change browser, run: python3 {sys.argv[0]} --configure-browser")
            else:
                print("Cannot proceed without selecting a browser.")
                return []
        
        if system == "Windows" or is_wsl:
            if is_wsl:
                # Get Windows user selection
                selected_user = config.get('windows_user')
                if not selected_user:
                    print("\n=== First Time Setup: Windows User Selection ===")
                    print("No Windows user configured for backup.")
                    selected_user = self._select_user()
                    if selected_user:
                        config['windows_user'] = selected_user
                        self._save_config(config)
                        print(f"\n✓ User '{selected_user}' saved for future backups.")
                        print(f"To change user later, run: python3 {sys.argv[0]} --configure-user")
                    else:
                        print("Cannot proceed without selecting a Windows user.")
                        return []
                
                # Build browser paths for selected user
                user_path = Path(f'/mnt/c/Users/{selected_user}')
                base_paths = []
                
                if isinstance(selected_browser, dict):
                    # Custom browser path
                    custom_path = selected_browser['custom']
                    if custom_path.startswith('/mnt/c/'):
                        base_paths.append(Path(custom_path))
                    else:
                        # Assume it's a Windows path and convert
                        base_paths.append(user_path / custom_path.replace('\\', '/'))
                else:
                    # Standard browser
                    browser_config = BROWSER_CONFIGS[selected_browser]
                    for browser_subpath in browser_config['paths']['Windows']:
                        base_paths.extend([
                            user_path / 'AppData' / 'Local' / browser_subpath,
                            user_path / 'AppData' / 'Roaming' / browser_subpath
                        ])
            else:
                # Regular Windows
                if isinstance(selected_browser, dict):
                    base_paths = [Path(selected_browser['custom'])]
                else:
                    browser_config = BROWSER_CONFIGS[selected_browser]
                    base_paths = []
                    for browser_subpath in browser_config['paths']['Windows']:
                        base_paths.extend([
                            Path(os.environ.get('LOCALAPPDATA', '')) / browser_subpath,
                            Path(os.environ.get('APPDATA', '')) / browser_subpath
                        ])
        elif system == "Darwin":  # macOS
            base_path = Path.home() / 'Library' / 'Application Support'
            if isinstance(selected_browser, dict):
                base_paths = [Path(selected_browser['custom'])]
            else:
                browser_config = BROWSER_CONFIGS[selected_browser]
                base_paths = [base_path / path for path in browser_config['paths']['Darwin']]
        elif system == "Linux" and not is_wsl:
            base_path = Path.home() / '.config'
            if isinstance(selected_browser, dict):
                base_paths = [Path(selected_browser['custom'])]
            else:
                browser_config = BROWSER_CONFIGS[selected_browser]
                base_paths = [base_path / path for path in browser_config['paths']['Linux']]
        else:
            raise OSError(f"Unsupported operating system: {system}")
        
        # Check all possible base paths
        for base_path in base_paths:
            try:
                if not base_path.exists():
                    continue
                    
                # Look for User Data directory (standard for Chromium-based browsers)
                user_data_candidates = [base_path / 'User Data', base_path]
                
                for user_data in user_data_candidates:
                    if not user_data.exists():
                        continue
                    
                    # Look for all profile directories
                    for profile_dir in user_data.iterdir():
                        if profile_dir.is_dir() and (profile_dir.name.startswith('Default') or profile_dir.name.startswith('Profile')):
                            bookmark_file = profile_dir / 'Bookmarks'
                            if bookmark_file.exists():
                                paths.append(bookmark_file)
                    
                    # If we found profiles, don't check other candidates
                    if paths:
                        break
                        
            except PermissionError:
                config = self._load_config()
                selected_user = config.get('windows_user', 'unknown')
                browser_info = config.get('browser', 'unknown')
                print(f"Permission denied accessing: {base_path}")
                print(f"Current user: {selected_user}, Browser: {browser_info}")
                print(f"Try running: python3 {sys.argv[0]} --configure-user")
                continue
            except Exception as e:
                print(f"Error checking {base_path}: {e}")
                continue
                
        return paths

    def configure_browser(self):
        """Reconfigure the browser selection"""
        print("Reconfiguring browser selection...")
        selected_browser = self._select_browser()
        if selected_browser:
            config = self._load_config()
            config['browser'] = selected_browser
            self._save_config(config)
            if isinstance(selected_browser, dict):
                print(f"Custom browser path configured: {selected_browser['custom']}")
            else:
                browser_name = BROWSER_CONFIGS[selected_browser]['name']
                print(f"Browser '{browser_name}' configured for backups.")
            
            # Refresh browser paths
            self.browser_paths = self._get_browser_paths()
            return True
        return False

    def configure_backup_directory(self):
        """Reconfigure the backup directory"""
        print("Reconfiguring backup directory...")
        backup_path = self._prompt_backup_directory()
        if backup_path:
            config = self._load_config()
            config['backup_path'] = backup_path
            self._save_config(config)
            self.backup_destination = Path(backup_path)
            print(f"Backup directory updated to: {backup_path}")
            return True
        return False
    
    def configure_retention(self):
        """Reconfigure backup retention"""
        print("Reconfiguring backup retention...")
        retention_count = self._prompt_backup_retention()
        if retention_count:
            config = self._load_config()
            config['max_backups'] = retention_count
            self._save_config(config)
            self.max_backups = retention_count
            print(f"Backup retention updated to: {retention_count} backups")
            return True
        return False

    def show_current_config(self):
        """Show current configuration"""
        config = self._load_config()
        print("Current configuration:")
        print(f"  Config file: {self.config_file}")
        
        # Browser info
        browser_config = config.get('browser')
        if isinstance(browser_config, dict):
            print(f"  Browser: Custom ({browser_config['custom']})")
        elif browser_config and browser_config in BROWSER_CONFIGS:
            print(f"  Browser: {BROWSER_CONFIGS[browser_config]['name']}")
        else:
            print(f"  Browser: Not configured")
            
        print(f"  Windows user: {config.get('windows_user', 'Not configured')}")
        print(f"  Backup directory: {config.get('backup_path', 'Not configured')}")
        print(f"  Backup retention: {config.get('max_backups', self.max_backups)} backups")
        
        # Show if directories exist
        backup_path = config.get('backup_path')
        if backup_path and Path(backup_path).exists():
            print(f"  ✓ Backup directory exists")
        elif backup_path:
            print(f"  ⚠ Backup directory does not exist")
    
    def configure_user(self):
        """Reconfigure the Windows user selection"""
        print("Reconfiguring Windows user selection...")
        selected_user = self._select_user()
        if selected_user:
            config = self._load_config()
            config['windows_user'] = selected_user
            self._save_config(config)
            print(f"User '{selected_user}' configured for backups.")
            
            # Refresh browser paths
            self.browser_paths = self._get_browser_paths()
            return True
        return False

    def _validate_bookmark_file(self, bookmark_path):
        """Validate that a bookmark file is readable and contains valid JSON"""
        try:
            if not bookmark_path.exists() or bookmark_path.stat().st_size == 0:
                return False
            
            with open(bookmark_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, PermissionError, OSError):
            return False
    
    def _count_bookmarks(self, data, path=""):
        """Recursively count bookmarks in browser data"""
        count = 0
        
        if isinstance(data, dict):
            if data.get('type') == 'url':
                return 1
            elif data.get('type') == 'folder':
                children = data.get('children', [])
                for child in children:
                    count += self._count_bookmarks(child, path)
            else:
                # Check common bookmark locations
                for key, value in data.items():
                    if key in ['bookmark_bar', 'other', 'synced'] or 'bookmarks' in key.lower():
                        count += self._count_bookmarks(value, f"{path}.{key}")
        
        elif isinstance(data, list):
            for item in data:
                count += self._count_bookmarks(item, path)
        
        return count

    def backup_bookmarks(self, verbose=False):
        """Main backup function"""
        timestamp = datetime.now()
        success_count = 0
        
        if not self.browser_paths:
            print("Error: No browser bookmark files found")
            config = self._load_config()
            browser_info = config.get('browser', 'Not configured')
            user_info = config.get('windows_user', 'Not configured')
            print(f"Current browser: {browser_info}")
            print(f"Current user: {user_info}")
            print("Try running configuration commands:")
            print("  --configure-browser  (change browser)")
            print("  --configure-user     (change Windows user)")
            return False
        
        # Create backup destination if it doesn't exist
        try:
            self.backup_destination.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error: Cannot create backup destination {self.backup_destination}: {e}")
            return False
        
        for bookmark_path in self.browser_paths:
            if not self._validate_bookmark_file(bookmark_path):
                if verbose:
                    print(f"Skipping invalid bookmark file: {bookmark_path}")
                continue
            
            # Extract profile name from path
            profile_name = bookmark_path.parent.name.lower().replace(' ', '_')
            
            # Get browser name for filename
            config = self._load_config()
            browser_config = config.get('browser')
            if isinstance(browser_config, dict):
                browser_name = 'custom'
            else:
                browser_name = browser_config or 'browser'
            
            backup_filename = self._create_backup_filename(browser_name, profile_name, timestamp)
            backup_path = self.backup_destination / backup_filename
            
            try:
                # Copy the bookmark file
                shutil.copy2(bookmark_path, backup_path)
                success_count += 1
                
                if verbose:
                    print(f"Backed up {profile_name} bookmarks to: {backup_path}")
                    
                    # Show bookmark count
                    with open(bookmark_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        bookmark_count = self._count_bookmarks(data)
                        print(f"  - {bookmark_count} bookmarks backed up")
                        
            except (OSError, PermissionError) as e:
                print(f"Error backing up {bookmark_path}: {e}")
        
        if success_count > 0:
            # Cleanup old backups
            self._cleanup_old_backups()
            print(f"Successfully backed up {success_count} bookmark file(s) to {self.backup_destination}")
            return True
        else:
            print("Error: No bookmark files were successfully backed up")
            return False

    def _create_backup_filename(self, browser_name, profile_name, timestamp):
        """Create backup filename with timestamp"""
        return f"{browser_name}_bookmarks_{profile_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    
    def _cleanup_old_backups(self):
        """Remove old backup files, keeping only the most recent max_backups"""
        if not self.backup_destination.exists():
            return
            
        backup_files = list(self.backup_destination.glob("*_bookmarks_*.json"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for old_backup in backup_files[self.max_backups:]:
            try:
                old_backup.unlink()
                print(f"Removed old backup: {old_backup.name}")
            except OSError as e:
                print(f"Warning: Could not remove old backup {old_backup.name}: {e}")
    
    def list_profiles(self):
        """List available browser profiles"""
        config = self._load_config()
        
        # Show configuration info
        browser_config = config.get('browser')
        if isinstance(browser_config, dict):
            print(f"Configured browser: Custom ({browser_config['custom']})")
        elif browser_config and browser_config in BROWSER_CONFIGS:
            print(f"Configured browser: {BROWSER_CONFIGS[browser_config]['name']}")
        else:
            print("Browser: Not configured")
            
        if config.get('windows_user'):
            print(f"Windows user: {config['windows_user']}")
        
        print("\nFound browser profiles:")
        if not self.browser_paths:
            print("  No profiles found")
            print("  Try running configuration commands:")
            print("    --configure-browser")
            print("    --configure-user")
            return
            
        for i, path in enumerate(self.browser_paths, 1):
            profile_name = path.parent.name
            bookmark_count = "unknown"
            
            if self._validate_bookmark_file(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        bookmark_count = self._count_bookmarks(data)
                except:
                    pass
            
            print(f"  {i}. {profile_name} - {bookmark_count} bookmarks")
            print(f"     Path: {path}")

def main():
    parser = argparse.ArgumentParser(description="Backup browser bookmarks (Chrome, Edge, Brave, or custom)")
    parser.add_argument("backup_path", nargs='?', help="Override backup path (optional)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-l", "--list", action="store_true", help="List available profiles and exit")
    parser.add_argument("-m", "--max-backups", type=int, help="Maximum number of backups to keep (overrides config)")
    parser.add_argument("-t", "--test", action="store_true", help="Test mode - show what would be backed up")
    parser.add_argument("--setup", action="store_true", help="Run initial setup (configure all settings)")
    parser.add_argument("--configure", action="store_true", help="Configure browser, Windows user and backup directory")
    parser.add_argument("--configure-browser", action="store_true", help="Configure browser selection only")
    parser.add_argument("--configure-user", action="store_true", help="Configure Windows user selection only")
    parser.add_argument("--configure-backup", action="store_true", help="Configure backup directory only")
    parser.add_argument("--configure-retention", action="store_true", help="Configure backup retention only")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    
    args = parser.parse_args()
    
    try:
        # For list mode, we don't need a valid backup path
        if args.list:
            max_backups = args.max_backups if args.max_backups else 30
            backup_tool = BrowserBookmarkBackup("/tmp", max_backups)
            backup_tool.list_profiles()
            return
        
        # Handle configuration commands
        if args.setup or args.configure:
            print("=== Browser Bookmark Backup Setup ===")
            backup_tool = BrowserBookmarkBackup("/tmp", 30)  # Temporary path for setup
            
            # Configure browser
            if not backup_tool.configure_browser():
                print("Setup cancelled.")
                return
            
            # Configure user (only for WSL)
            system = platform.system()
            is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
            if system == "Windows" or is_wsl:
                if not backup_tool.configure_user():
                    print("Setup cancelled.")
                    return
            
            # Configure backup directory
            if not backup_tool.configure_backup_directory():
                print("Setup cancelled.")
                return
            
            # Configure backup retention
            if not backup_tool.configure_retention():
                print("Setup cancelled.")
                return
            
            print("\n✓ Setup complete! You can now run backups.")
            return
        
        if args.configure_browser:
            backup_tool = BrowserBookmarkBackup("/tmp", 30)
            backup_tool.configure_browser()
            return
        
        if args.configure_user:
            backup_tool = BrowserBookmarkBackup("/tmp", 30)
            backup_tool.configure_user()
            return
        
        if args.configure_backup:
            backup_tool = BrowserBookmarkBackup("/tmp", 30)
            backup_tool.configure_backup_directory()
            return
        
        if args.configure_retention:
            backup_tool = BrowserBookmarkBackup("/tmp", 30)
            backup_tool.configure_retention()
            return
        
        if args.show_config:
            backup_tool = BrowserBookmarkBackup("/tmp", 30)
            backup_tool.show_current_config()
            return
        
        # Normal operation - create backup tool (will prompt for config if needed)
        # Use command line max_backups if provided, otherwise let the class handle it
        if args.max_backups:
            backup_tool = BrowserBookmarkBackup(args.backup_path, args.max_backups)
        else:
            backup_tool = BrowserBookmarkBackup(args.backup_path)
            
        if args.test:
            print("TEST MODE - No files will be backed up")
            print(f"Using backup path: {backup_tool.backup_destination}")
            backup_tool.list_profiles()
            print(f"\nBackup destination: {backup_tool.backup_destination}")
            print(f"Max backups to keep: {backup_tool.max_backups}")
            return
        
        success = backup_tool.backup_bookmarks(args.verbose)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Simple usage - uncomment this block and comment out main() to run with defaults
    # Note: This will prompt for configuration on first run
    # backup_tool = BrowserBookmarkBackup()
    # backup_tool.backup_bookmarks(verbose=True)
    
    main()