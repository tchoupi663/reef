# Reef

Reef is a comprehensive infrastructure management tool designed to deploy secure, reproducible, and automated IT environments for Small and Medium Enterprises (SMEs). It leverages Infrastructure as Code (IaC) principles using Terraform and Ansible to ensure reliability and maintainability.

## Key Features

*   **Automated Deployment**: One-click provisioning of VMs and network components.
*   **Security First**: Built-in hardening, deny-by-default firewall policies, and encrypted communications via WireGuard and SSH.
*   **Core Services**:
    *   **Network**: DNS, NTP, Firewall.
    *   **Access**: VPN (WireGuard), SSH (Key-based).
    *   **Application**: Nginx Web Server, Docker support.
    *   **Data**: PostgreSQL/MariaDB, Encrypted Backups.
    *   **Monitoring**: Grafana, Loki (Log Centralization).
*   **Flexible Interface**: Integrated CLI and Web-based Dashboard.

## Requirements

*   **Operating System**: Linux (Ubuntu 22.04+ Recommended) or macOS.
*   **Dependencies**: Python 3.8+, Terraform, Ansible, Libvirt/QEMU.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd reef
    ```

2.  Install the package and dependencies:
    ```bash
    pip install -e .
    ```

## Usage

### Web Dashboard

Launch the graphical interface for easy management and visualization:

```bash
reef
```
Access the dashboard at `http://localhost:8080`.

### Command Line Interface (CLI)

Use the CLI for headless operations and advanced configuration:

```bash
reef --cli [COMMAND]
```

**Common Commands:**
*   `reef --cli deploy`: Start the deployment process.
*   `reef --cli config`: View or modify configuration.
*   `reef --help`: Display available commands and options.

## Architecture

The system follows a segmented network architecture to maximize security:
*   **Management Network**: Restricted access via VPN.
*   **Internal Network**: Isolated critical services (Database, Backups, Monitoring).
*   **DMZ**: Public-facing services (Web Server).
