# System Control Features

## Overview
The MANGO TREE Monitor now includes comprehensive system control features that allow remote administration of the monitored computer.

## Features

### 🔧 System Control
- **Power Off System**: Remotely power off the computer
- **Restart System**: Remotely restart the computer
- **Put to Sleep**: Put the system to sleep mode
- **Force Logout**: Log out the current user

### 🔒 Security Control
- **Lock System**: Lock the system with password protection
- **Unlock System**: Unlock the system remotely
- **Kill WiFi**: Disable WiFi connection
- **Enable WiFi**: Re-enable WiFi connection

### 📋 Process Management
- **View Processes**: See all running processes with CPU and memory usage
- **Kill Process**: Terminate specific processes remotely
- **Real-time Monitoring**: Live updates of process information

### 🚫 Application Blocking
- **Block Applications**: Block specific applications from running
- **Unblock Applications**: Remove applications from the blocked list
- **Password Protection**: Applications can be temporarily unblocked with admin password
- **Real-time Blocking**: Blocked applications are immediately terminated

### 📁 File Management
- **Browse Files**: Navigate through the file system
- **Download Files**: Download files from the remote system
- **Delete Files**: Delete files and folders remotely
- **Upload Files**: Upload files to the remote system

## Security

### Passwords
- **System Lock/Unlock Password**: `yeshaswigod`
- **Application Unblock Password**: `yeshaswigod`

### Authentication
- All system control features require web login
- Actions are logged for audit purposes
- Confirmation dialogs prevent accidental operations

## Usage

### Accessing System Control
1. Navigate to the monitoring web interface
2. Click on "System Control" in the sidebar
3. Use the various control panels to manage the system

### Locking the System
1. Click "Lock System" in Security Control
2. The system will show a fullscreen lock overlay
3. Users must enter the password `yeshaswigod` to unlock
4. Can also be unlocked remotely via the web interface

### Blocking Applications
1. Enter the application name (e.g., `chrome.exe`) in the Application Blocking section
2. Click "Block" to add it to the blocked list
3. When users try to run the blocked application:
   - It will be immediately terminated
   - A warning dialog will appear
   - Users can temporarily unblock with the password `yeshaswigod`

### Process Management
1. View real-time process information in the Process Management section
2. Click "Kill" next to any process to terminate it
3. Use "Refresh" to update the process list

### File Management
1. Browse the file system using the File Manager
2. Click folder names to navigate
3. Use "Download" to get files from the remote system
4. Use "Delete" to remove files or folders

## Logging

All system control actions are logged to:
- `logs/remote_control_log.txt` - General system control actions
- `logs/app_blocker_log.txt` - Application blocking activities

## Technical Details

### Components
- `system_lock_overlay.py` - Fullscreen lock overlay application
- `app_blocker.py` - Application blocking service
- System control API routes in `run_monitor.py`
- JavaScript frontend in `templates/index.html`

### Requirements
- Windows operating system
- Administrator privileges for system operations
- Python modules: `psutil`, `tkinter`, `subprocess`

## Troubleshooting

### System Lock Not Working
- Ensure `system_lock_overlay.py` is in the same directory
- Check that Python and tkinter are properly installed
- Verify the lock flag files are being created in the `logs` directory

### Application Blocking Not Working
- Verify the Application Blocker is started (check console output)
- Ensure proper permissions for process termination
- Check `logs/app_blocker_log.txt` for debugging information

### WiFi Control Not Working
- Ensure the computer has a WiFi adapter named "Wi-Fi"
- Some systems may use different adapter names
- Run as administrator for network interface control

## Security Warning

These features provide significant control over the monitored system. Use responsibly and ensure:
- Proper authentication is in place
- Actions are authorized by system owners
- Logging is monitored for security purposes
- Passwords are kept secure and changed regularly
