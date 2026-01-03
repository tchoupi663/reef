#!/bin/bash
# Wrapper to run Ansible playbook and then the test script

echo "Running Ansible Playbook..."
cd ../ansible
ansible-playbook playbooks/deploy-prototype.yml

if [ $? -eq 0 ]; then
    echo "Playbook finished successfully. Running tests..."
    cd ../scripts
    # Assuming local test for now, can be adapted for remote
    bash test-security.sh 192.168.64.7
else
    echo "Playbook failed."
    exit 1
fi
