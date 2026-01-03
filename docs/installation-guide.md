# Installation Guide

## 1. Prepare Target Machine
- Install Debian 12 (Bookworm).
- Ensure SSH access is enabled.
- Ensure the user has sudo privileges (or use root).
- Recommended: 4GB RAM, 2 CPUs.

## 2. Configure Ansible Control Node
- clone this repository.
- Install Ansible (`apt install ansible` or `pip install ansible`).
- Edit `ansible/inventory/hosts.ini`:
  ```ini
  [security_server]
  192.168.1.10 ansible_user=admin
  ```
- Edit `ansible/inventory/group_vars/all.yml` to set your preferences.

## 3. Deployment
Run the main playbook:
```bash
cd ansible
ansible-playbook playbooks/deploy-prototype.yml
```

## 4. Verification
- Access `https://<TARGET_IP>`
- Login with `admin` / `<YOUR_PASSWORD>`
- Check `scripts/test-security.sh` for automated checks.
