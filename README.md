# PME Security Automation Prototype

This project automates the deployment of a security stack on an Ubuntu 22.04+ server using Ansible.

## Components
- **Wazuh All-in-One**: SIEM/XDR (Manager, Agent, Indexer, Dashboard).
- **Fail2ban**: Intrusion prevention for SSH.
- **UFW**: Host-based firewall.

## Prerequisites
- **Control Node**: Machine running Ansible (e.g., macOS, Linux).
- **Target Node**: server running Ubuntu 22.04 or later (x86_64).
- **Access**: SSH access to target node with sudo privileges.

## Setup
1.  **Configure Inventory**:
    Edit `ansible/inventory/hosts.ini` and replace the IP with your target server's IP.
    ```ini
    [security_server]
    <TARGET_IP> ansible_user=<USER>
    ```

2.  **Configure Variables**:
    Review `ansible/inventory/group_vars/all.yml` to set passwords and allowed IPs.

3.  **Run Deployment**:
    ```bash
    cd ansible
    ansible-playbook playbooks/deploy-prototype.yml
    ```

## Usage
- **Wazuh Dashboard**: `https://<TARGET_IP>`
    - Default Port: 443
    - Credentials: `admin` / `<wazuh_admin_password>` (Default: StrongPassword123!)
