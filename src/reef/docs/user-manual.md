# User Manual

## Accessing the Dashboard
1. Open your browser and navigate to `https://<MAIN_SERVER_IP>`.
2. Accept the self-signed certificate warning (for prototype).
3. Log in with the credentials.

## Checking Alerts
- Go to **Security events** module.
- You should see alerts related to SSH logins (success/failure) and system calls.

## Testing Security
1. **Pinging**: Try to ping the server.
2. **SSH Failures**: Try to SSH with wrong password 5 times. Fail2ban should ban you for 1 hour.
   - Check ban status: `sudo fail2ban-client status sshd`

## Troubleshooting
- **Wazuh not starting**: Check logs at `/var/ossec/logs/ossec.log`.
- **Dashboard error**: Ensure `wazuh-dashboard` service is running (`systemctl status wazuh-dashboard`).
