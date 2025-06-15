# Brave Bookmark Backup for WSL

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-WSL-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A Python script to automatically backup Brave browser bookmarks from WSL (Windows Subsystem for Linux) to a configurable location with scheduling support.

## 🚀 Features

- **Cross-platform bookmark detection** - Automatically finds Brave bookmarks on Windows from WSL
- **Smart configuration** - Prompts for user and backup directory on first run
- **OneDrive integration** - Suggests OneDrive folder for automatic cloud backup
- **Multiple scheduling options** - Works around WSL cron limitations
- **Persistent configuration** - Saves settings for future runs
- **Backup rotation** - Keeps only the most recent N backups
- **Multiple profile support** - Backs up all Brave browser profiles

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Scheduling Options](#scheduling-options)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🛠 Installation

### Prerequisites

- Windows 10/11 with WSL enabled
- Python 3.8 or higher
- Brave browser installed on Windows
- Access to Windows user directories from WSL

### Setup

1. **Clone or download the script:**
   ```bash
   wget https://raw.githubusercontent.com/yourusername/brave-backup-wsl/main/bookmarkBackup.py
   # or
   curl -O https://raw.githubusercontent.com/yourusername/brave-backup-wsl/main/bookmarkBackup.py
   ```

2. **Make executable:**
   ```bash
   chmod +x bookmarkBackup.py
   ```

3. **Initial setup:**
   ```bash
   python3 bookmarkBackup.py --setup
   ```

## 🚀 Quick Start

### First Time Setup

```bash
# Run initial setup to configure user and backup directory
python3 bookmarkBackup.py --setup
```

This will prompt you to:
1. Select which Windows user account to backup
2. Choose backup directory (suggests OneDrive by default)

### Basic Usage

```bash
# Perform backup with verbose output
python3 bookmarkBackup.py -v

# Test run (dry run)
python3 bookmarkBackup.py -t

# List available browser profiles
python3 bookmarkBackup.py -l
```

## ⚙️ Configuration

### Configuration Commands

| Command | Description |
|---------|-------------|
| `--setup` | Complete initial setup |
| `--show-config` | Display current configuration |
| `--configure-user` | Change Windows user selection |
| `--configure-backup` | Change backup directory |
| `--configure` | Reconfigure user and backup directory |

### Configuration File

Settings are stored in `~/.brave_backup_config.json`:

```json
{
  "windows_user": "tameg",
  "backup_path": "/mnt/c/Users/tameg/OneDrive/bookmarks"
}
```

### Command Line Options

```bash
python3 bookmarkBackup.py [options] [backup_path]

Options:
  -v, --verbose         Verbose output
  -l, --list           List available profiles
  -t, --test           Test mode (dry run)
  -m, --max-backups N  Maximum backups to keep (default: 30)
  --setup              Run initial setup
  --show-config        Show current configuration
  --configure-user     Configure Windows user only
  --configure-backup   Configure backup directory only
```

## 📅 Scheduling Options

Since cron doesn't work reliably in WSL, here are several scheduling alternatives:

### Option 1: Windows Task Scheduler (⭐ Recommended)

1. **Create batch file (`brave_backup.bat`):**
   ```batch
   @echo off
   wsl -d Ubuntu python3 /mnt/c/path/to/bookmarkBackup.py -v >> C:\logs\brave_backup.log 2>&1
   ```

2. **Setup Task Scheduler:**
   - Open Task Scheduler (`Win + R` → `taskschd.msc`)
   - Create Basic Task → "Brave Bookmark Backup"
   - Set trigger (Daily, Weekly, etc.)
   - Action: Start program → Point to your `.bat` file
   - Enable "Run whether user is logged on or not"

### Option 2: PowerShell Scheduled Job

**Create PowerShell script (`BraveBackup.ps1`):**
```powershell
$logFile = "C:\logs\brave_backup.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    $result = wsl python3 /mnt/c/path/to/bookmarkBackup.py -v 2>&1
    Add-Content -Path $logFile -Value "[$timestamp] SUCCESS: $result"
    
    # Optional: Email notification on success
    # Send-MailMessage -To "you@email.com" -Subject "Backup Success" -Body $result
} catch {
    Add-Content -Path $logFile -Value "[$timestamp] ERROR: $($_.Exception.Message)"
    
    # Optional: Email notification on failure
    # Send-MailMessage -To "you@email.com" -Subject "Backup Failed" -Body $_.Exception.Message
}
```

**Register scheduled task:**
```powershell
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Scripts\BraveBackup.ps1"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "BraveBookmarkBackup" -Trigger $trigger -Action $action -Settings $settings
```

### Option 3: systemd (WSL2 with systemd enabled)

**Service file (`~/.config/systemd/user/brave-backup.service`):**
```ini
[Unit]
Description=Brave Bookmark Backup
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/username/scripts/bookmarkBackup.py -v
User=%i
```

**Timer file (`~/.config/systemd/user/brave-backup.timer`):**
```ini
[Unit]
Description=Run Brave Bookmark Backup Daily
Requires=brave-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

**Enable timer:**
```bash
systemctl --user daemon-reload
systemctl --user enable brave-backup.timer
systemctl --user start brave-backup.timer

# Check status
systemctl --user list-timers
```

### Option 4: Startup Script

**For backup on login (`brave_backup_startup.bat`):**
```batch
@echo off
timeout /t 30 /nobreak >nul
wsl python3 /mnt/c/path/to/bookmarkBackup.py -v
```

Place in Windows startup folder: `Win + R` → `shell:startup`

## 📊 Usage Examples

### Basic Operations

```bash
# Show current configuration
python3 bookmarkBackup.py --show-config

# List available Brave profiles
python3 bookmarkBackup.py -l

# Test backup (no files created)
python3 bookmarkBackup.py -t

# Perform backup with detailed output
python3 bookmarkBackup.py -v

# Backup to specific location
python3 bookmarkBackup.py -v /mnt/c/MyBackups/brave

# Keep only 10 most recent backups
python3 bookmarkBackup.py -v -m 10
```

### Configuration Changes

```bash
# Change Windows user
python3 bookmarkBackup.py --configure-user

# Change backup directory
python3 bookmarkBackup.py --configure-backup

# Complete reconfiguration
python3 bookmarkBackup.py --setup
```

### Monitoring and Verification

```bash
# List recent backups
ls -la /mnt/c/Users/tameg/OneDrive/bookmarks/brave_bookmarks_*.json

# Check backup file integrity
python3 -c "
import json, sys
with open(sys.argv[1], 'r') as f:
    data = json.load(f)
    print(f'Backup contains {len(data.get(\"roots\", {}).get(\"bookmark_bar\", {}).get(\"children\", []))} bookmarks')
" /path/to/backup/file.json

# Verify OneDrive sync status (if using OneDrive)
```

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Permission denied** | Ensure WSL has access to Windows user directories |
| **No Brave profiles found** | Run `--configure-user` to select correct Windows user |
| **Backup directory not accessible** | Run `--configure-backup` to set valid path |
| **Task Scheduler not running** | Check Task Scheduler history and enable logging |
| **WSL not starting** | Restart WSL: `wsl --shutdown` then `wsl` |

### Debug Commands

```bash
# Test WSL access to Windows
wsl whoami
wsl ls /mnt/c/Users

# Test Python script
python3 bookmarkBackup.py --show-config

# Test Windows Task Scheduler
schtasks /run /tn "BraveBookmarkBackup"

# Check WSL version
wsl --list --verbose
```

### Log Analysis

```bash
# View recent backup logs (if using batch file logging)
tail -f /mnt/c/logs/brave_backup.log

# Check Windows Event Logs (PowerShell as Administrator)
Get-EventLog -LogName Application -Source "BraveBackup" -Newest 10
```

## 📂 File Structure

```
brave-backup-wsl/
├── bookmarkBackup.py          # Main backup script
├── brave_diagnostic.py        # Diagnostic tool
├── README.md                  # This file
├── examples/
│   ├── brave_backup.bat      # Windows batch file
│   ├── BraveBackup.ps1       # PowerShell script
│   └── brave-backup.service  # systemd service
└── logs/
    └── brave_backup.log       # Log file location
```

## 🎯 Best Practices

### Recommended Setup

1. **Use OneDrive backup location** for automatic cloud sync
2. **Schedule daily backups** at 2:00 AM when system is idle
3. **Keep 30 days of backups** (default) for recovery options
4. **Enable logging** to monitor backup success
5. **Test scheduling** before relying on automation

### Security Considerations

- **File permissions**: Ensure backup directory has appropriate permissions
- **Network paths**: Use encrypted connections for network backups
- **Sensitive bookmarks**: Consider encrypting backup files if they contain sensitive data
- **Access logs**: Monitor backup logs for unauthorized access

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/brave-backup-wsl.git
cd brave-backup-wsl

# Test installation
python3 bookmarkBackup.py --setup

# Run diagnostic
python3 brave_diagnostic.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Brave Software for the excellent browser
- Microsoft for WSL integration
- Python community for excellent libraries

---

**⭐ If this project helped you, please consider giving it a star!**

## 📞 Support

If you encounter any issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Run the diagnostic script: `python3 brave_diagnostic.py`
3. Open an issue with detailed error information
4. Include your WSL version and Python version

---

*Made with ❤️ for the WSL and Brave community*
