#!/bin/bash
BID_DIR="/root/bid"
cd "$BID_DIR"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

SERVICES=(
    "bid_bot"
    "bid_backuper"
    "bid_transactions_report"
    "navasan-to-bale"
    "order-book"
    "parachi-auth-bot"
    "parachi-price-story-image"
    "parachi-price-updates"
    "update_handler"
)

SELECTED=()

if [ $# -gt 0 ] && [ "$1" != "all" ] && [ "$1" != "ALL" ] && [ "$1" != "0" ]; then
    SELECTED=("$@")
else
    echo -e "${CYAN}==========================================${NC}"
    echo -e "${PURPLE} 📋 DOCKER LIVE LOG VIEWER MENU${NC}"
    echo -e "${CYAN}==========================================${NC}"
    echo -e "${YELLOW}0) ALL SERVICES (Combined Stream)${NC}"
    for i in "${!SERVICES[@]}"; do
        echo -e "${GREEN}$((i+1))) ${SERVICES[$i]}${NC}"
    done
    echo -e "${CYAN}==========================================${NC}"
    read -p "Select service number to stream live logs (e.g. '1' or '0' for all): " CHOICE

    if [ -z "$CHOICE" ] || [ "$CHOICE" -eq 0 ]; then
        SELECTED=()
    elif [[ "$CHOICE" =~ ^[1-9]$ ]]; then
        idx=$((CHOICE-1))
        if [ $idx -lt ${#SERVICES[@]} ]; then
            SELECTED=("${SERVICES[$idx]}")
        fi
    fi
fi

if [ ${#SELECTED[@]} -eq 0 ]; then
    echo -e "${CYAN}📡 Streaming live logs for ${GREEN}ALL SERVICES${CYAN}... (Press Ctrl+C to exit)${NC}\n"
    docker compose logs -f --tail=30
else
    echo -e "${CYAN}📡 Streaming live logs for: ${GREEN}${SELECTED[*]}${CYAN}... (Press Ctrl+C to exit)${NC}\n"
    docker compose logs -f --tail=30 "${SELECTED[@]}"
fi
