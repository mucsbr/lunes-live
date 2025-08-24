# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a VPS monitoring and auto-recovery system for Pterodactyl game server panels. The system automatically monitors VPS status via WebSocket connections and restarts servers when they detect an offline state.

## Architecture

The system consists of a single Python application that handles:
- Pterodactyl panel authentication using Laravel Sanctum
- WebSocket connection for real-time server status monitoring
- Automatic server recovery when offline status is detected
- SSHX link extraction for remote access

## Key Components

### VPSMonitor Class (vps_monitor.py)
The main monitoring class that orchestrates the entire process:
- Authentication flow: CSRF token → login → session management
- WebSocket connection with automatic reconnection
- Status monitoring and auto-recovery logic
- SSHX link extraction from console output

### Authentication Flow
1. GET `/server/{server_id}` - Obtain initial cookies (XSRF-TOKEN and pterodactyl_session)
2. GET `/sanctum/csrf-cookie` - Update CSRF token with cookies from step 1
3. POST `/auth/login` - Authenticate with credentials, cookies, and XSRF-TOKEN
4. WebSocket connection - Uses authenticated session cookies

### WebSocket Protocol
- **Connection**: `wss://{node_host}:{ws_port}/api/servers/{server_uuid}/ws`
- **Status Events**: Monitor for `{"event":"status","args":["starting|offline"]}`
- **Control Commands**: Send `{"event":"set state","args":["start"]}` to restart
- **SSHX Extraction**: Parse console output for SSHX links

## Common Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run monitor (foreground)
python3 vps_monitor.py

# Run monitor (background)
./start_monitor.sh

# Stop monitor
./stop_monitor.sh

# View logs
tail -f vps_monitor.log
```

### Testing
```bash
# Install test dependencies
pip install -r test-requirements.txt

# Run all tests
./run_tests.sh

# Run specific test file
./run_tests.sh --file test_vps_monitor.py

# Run specific test class/method
./run_tests.sh --test TestVPSMonitor

# View test coverage
./run_tests.sh --coverage
```

### Configuration
Configuration is handled in the `VPSConfig` dataclass within `vps_monitor.py`. Key parameters:
- `panel_url`: Pterodactyl panel URL
- `server_id`/`server_uuid`: Server identifiers
- `node_host`/`ws_port`: WebSocket connection details
- `username`/`password`: Authentication credentials
- `check_interval`: Monitoring frequency in seconds

## Important Implementation Details

### Status Handling
- `starting` = Server is running (despite the name, this indicates active state)
- `offline` = Server is stopped and needs recovery
- System automatically sends restart command when offline detected

### Error Recovery
- Automatic reconnection on WebSocket disconnect
- Login re-authentication on session expiration
- Configurable retry limits and intervals

### WebSocket Message Processing
The system processes specific event types:
- `status` events for server state changes
- `console output` events for SSHX link extraction
- All other events are logged but not processed

### Security Considerations
- Uses secure WebSocket (wss://)
- Session-based authentication with automatic cookie management
- CSRF token handling for Laravel Sanctum
- No hardcoded credentials in version control