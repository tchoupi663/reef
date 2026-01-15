#!/bin/bash
# EMERGENCY CLEANUP SCRIPT
# Run this on the target machine (192.168.1.19) as root or with sudo

echo ">>> KEY STEP: REBOOT FIRST IF POSSIBLE TO CLEAR STUCK PROCESSES <<<"
echo "Starting Emergency Cleanup..."

set -x # Enable echo for visibility

# 1. Kill all Wazuh/Elastic related processes
echo "Killing processes..."
pkill -9 -f wazuh
pkill -9 -f elasticsearch
pkill -9 -f filebeat
pkill -9 -f dashboard
# Clear ports explicitly
lsof -ti:1514 | xargs -r kill -9
lsof -ti:1515 | xargs -r kill -9
lsof -ti:55000 | xargs -r kill -9
lsof -ti:9200 | xargs -r kill -9
lsof -ti:9300 | xargs -r kill -9

# 2. Fix Broken APT/DPKG State (The "needs to be reinstalled" error)
echo "Fixing DPKG database..."
# Remove corrupt status entries
sed -i '/Package: wazuh-manager/,/^$/d' /var/lib/dpkg/status
sed -i '/Package: wazuh-agent/,/^$/d' /var/lib/dpkg/status
sed -i '/Package: wazuh-indexer/,/^$/d' /var/lib/dpkg/status
sed -i '/Package: wazuh-dashboard/,/^$/d' /var/lib/dpkg/status
# Remove package metadata
rm -f /var/lib/dpkg/info/wazuh-*
# Clean locks
rm -f /var/lib/apt/lists/lock
rm -f /var/cache/apt/archives/lock
rm -f /var/lib/dpkg/lock*

# 2.1 Ensure UFW allows Dashboard and Manager traffic
ufw delete allow 443
ufw delete allow 1514
ufw delete allow 1515
ufw delete allow 55000

# 3. Force Remove Packages
echo "Removing packages..."
dpkg --remove --force-all wazuh-manager
dpkg --remove --force-all wazuh-agent
dpkg --remove --force-all wazuh-indexer
dpkg --remove --force-all wazuh-dashboard
dpkg --remove --force-all filebeat
apt-get purge -y wazuh* filebeat elasticsearch

# 4. Wipe Directories
echo "Wiping directories..."
rm -rf /var/ossec
rm -rf /etc/wazuh-indexer
rm -rf /etc/wazuh-dashboard
rm -rf /var/lib/wazuh-indexer
rm -rf /usr/share/wazuh-dashboard
rm -rf /opt/wazuh-docker

# 5. Clean Repository artifacts
rm -f /etc/apt/sources.list.d/wazuh.list
rm -f /usr/share/keyrings/wazuh-keyring.gpg

echo ">>> CLEANUP COMPLETE. Try running your Ansible playbook now. <<<"
