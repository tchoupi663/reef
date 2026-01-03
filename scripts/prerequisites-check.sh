#!/bin/bash
# Check if the system meets requirements for PME Security Automation

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "---------------------------------------"

echo -e "${BLUE}Checking prerequisites...${NC}"

# 1. Check OS
if grep -q "Debian GNU/Linux 12" /etc/os-release 2>/dev/null; then
    echo -e "${GREEN}[OK]${NC} OS is Debian 12"
elif grep -q "Ubuntu" /etc/os-release 2>/dev/null && grep -qE '22\.|24\.' /etc/os-release 2>/dev/null; then
    echo -e "${GREEN}[OK]${NC} OS is Ubuntu (22/24)"
elif grep -q "Debian GNU/Linux 11" /etc/os-release 2>/dev/null; then
    echo -e "${YELLOW}[WARN]${NC} OS is Debian 11. Proceed with caution."
else
    echo -e "${RED}[ERROR]${NC} OS is not supported (Requires Debian 12 or Ubuntu 22/24)."
fi

# 2. Check RAM (Min 4GB recommended for Wazuh AIO)
TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -ge 4000 ]; then
    echo -e "${GREEN}[OK]${NC} Memory: ${TOTAL_MEM}MB (>= 4GB)"
elif [ "$TOTAL_MEM" -ge 1800 ]; then
    echo -e "${YELLOW}[WARN]${NC} Memory: ${TOTAL_MEM}MB (< 4GB). Wazuh might be slow."
else
    echo -e "${RED}[ERROR]${NC} Memory: ${TOTAL_MEM}MB (< 1.8GB). Wazuh will not run. (or be very very slow)"
fi

# 3. Check Disk Space (Min 20GB free recommended)
FREE_DISK=$(df -h / | awk 'NR==2 {print $4}')
echo -e "${BLUE}[INFO]${NC} Free Disk Space on /: $FREE_DISK"

# 4. Check Root
if [ "$(id -u)" -ne 0 ]; then 
    echo -e "${YELLOW}[WARN]${NC} Script not running as root. Ansible requires sudo/root."
else
    echo -e "${GREEN}[OK]${NC} Running as root"
fi

echo -e "${BLUE}Prerequisites check complete.${NC}"

echo -e "---------------------------------------"
