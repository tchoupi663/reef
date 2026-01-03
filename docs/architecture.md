# System Architecture

## Overview
This prototype deploys a single-node security stack tailored for a PME environment.

## Components

### Wazuh All-in-One
- **Wazuh Indexer**: Stores security alerts and events. Compatible with OpenSearch.
- **Wazuh Server**: Analyzes data received from agents.
- **Wazuh Dashboard**: Web interface for data visualization and management.
- **Wazuh Agent**: Installed on the manager itself to monitor the server.

### Fail2ban
- Monitors log files (e.g., `/var/log/auth.log`).
- Bans IPs that show malicious signs like too many password failures.
- Configured with `JAIL.LOCAL` to persist settings across updates.

### UFW (Uncomplicated Firewall)
- Default Deny Incoming.
- Allow SSH (Port 22) - Restricted to management IPs recommended.
- Allow HTTPS (Port 443) - For Wazuh Dashboard.
- Allow 1514/1515 - For future agent communication.

## Network Flow
[Internet/LAN] -> [UFW:443] -> [Wazuh Dashboard]
[Admin] -> [UFW:22] -> [SSH] -> [Fail2ban monitoring]
