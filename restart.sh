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
    echo -e "${PURPLE} 🔄 DOCKER SERVICE RESTART MENU${NC}"
    echo -e "${CYAN}==========================================${NC}"
    echo -e "${YELLOW}0) ALL SERVICES${NC}"
    for i in "${!SERVICES[@]}"; do
        echo -e "${GREEN}$((i+1))) ${SERVICES[$i]}${NC}"
    done
    echo -e "${CYAN}==========================================${NC}"
    read -p "Select service numbers (e.g. '1 6' or '0' for all): " -a CHOICES

    if [ ${#CHOICES[@]} -eq 0 ] || [[ " ${CHOICES[*]} " =~ " 0 " ]] || [[ " ${CHOICES[*]} " =~ "all" ]] || [[ " ${CHOICES[*]} " =~ "ALL" ]]; then
        SELECTED=("${SERVICES[@]}")
    else
        for num in "${CHOICES[@]}"; do
            if [[ "$num" =~ ^[1-9]$ ]]; then
                idx=$((num-1))
                if [ $idx -lt ${#SERVICES[@]} ]; then
                    SELECTED+=("${SERVICES[$idx]}")
                fi
            fi
        done
    fi
fi

echo -e "${CYAN}🔄 Restarting selected services: ${GREEN}${SELECTED[*]}${NC}"
docker compose restart "${SELECTED[@]}"
echo -e "${GREEN}✅ Restart completed!${NC}"
