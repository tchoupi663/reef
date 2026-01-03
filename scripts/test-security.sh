#!/bin/bash
# Basic validation of the security deployment

TARGET_IP="192.168.64.7"

echo "Testing Security Deployment on $TARGET_IP..."

# 1. Check UFW Status
if command -v ufw >/dev/null; then
    echo "--- UFW Status ---"
    sudo ufw status verbose
else
    echo "[FAIL] UFW is not installed"
fi

# 2. Check Fail2ban Status
if systemctl is-active --quiet fail2ban; then
    echo "[OK] Fail2ban is running"
    echo "--- Fail2ban Jails ---"
    sudo fail2ban-client status
    sudo fail2ban-client status sshd
else
    echo "[FAIL] Fail2ban is not running"
fi

# 3. Check Wazuh Services
echo "--- Wazuh Services ---"
for service in wazuh-manager wazuh-indexer wazuh-dashboard; do
    if systemctl is-active --quiet $service; then
        echo "[OK] $service is running"
    else
        echo "[FAIL] $service is NOT running"
    fi
done

# 4. Check Dashboard Access (HTTPS)
echo "--- Dashboard Accessibility ---"
HTTP_CODE=$(curl -k -o /dev/null -s -w "%{http_code}\n" https://$TARGET_IP:443)
if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "302" ]; then
    echo "[OK] Dashboard accessible at https://$TARGET_IP:443 (HTTP $HTTP_CODE)"
else
    echo "[FAIL] Dashboard not accessible (HTTP $HTTP_CODE)"
fi

echo "Test complete."
