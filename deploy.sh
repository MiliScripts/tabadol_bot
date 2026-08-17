#!/bin/bash
set -e

BID_DIR="/root/bid"
cd "$BID_DIR"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}==========================================${NC}"
echo -e "${GREEN}🚀 FULL DOCKER DEPLOYMENT FROM SCRATCH${NC}"
echo -e "${CYAN}==========================================${NC}"

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}🐳 Installing Docker CE...${NC}"
    apt-get update -y && apt-get install -y ca-certificates curl gnupg
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sh /tmp/get-docker.sh
    rm -f /tmp/get-docker.sh
fi

systemctl start docker || service docker start
systemctl enable docker || true

# Stop conflicting systemd units
SERVICES=("bid_bot" "bid_backuper" "bid_transactions_report" "navasan-to-bale" "order-book" "parachi-auth-bot" "parachi-price-story-image" "parachi-price-updates" "update_handler")
for s in "${SERVICES[@]}"; do
    systemctl stop "$s" 2>/dev/null || true
    systemctl disable "$s" 2>/dev/null || true
done

echo -e "${CYAN}🔨 Building images and starting containers...${NC}"
DOCKER_BUILDKIT=1 docker compose up -d --build

echo -e "${YELLOW}⏳ Waiting 6 seconds for containers to initialize...${NC}"
sleep 6

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}📊 CONTAINER HEALTH STATUS${NC}"
echo -e "${GREEN}==========================================${NC}"
docker compose ps
