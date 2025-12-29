#!/bin/bash
# Wrapper script per wallet-tool Docker

set -e

IMAGE_NAME="open-automator-wallet"
DATA_DIR="./data"

# Colori
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Assicura che data directory esista
mkdir -p "$DATA_DIR"

# Funzione helper
run_wallet_tool() {
    docker run --rm -it \
        -v "$(pwd)/$DATA_DIR:/data:rw" \
        -e TERM=xterm-256color \
        "$IMAGE_NAME" "$@"
}

# Se nessun argomento, mostra help
if [ $# -eq 0 ]; then
    echo -e "${GREEN}🔐 Open-Automator Wallet Tool${NC}"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  create    - Create new wallet"
    echo "  list      - List secrets"
    echo "  add       - Add secret"
    echo "  remove    - Remove secret"
    echo "  get       - Get secret value"
    echo "  export    - Export secrets to JSON"
    echo "  info      - Show wallet info"
    echo "  shell     - Interactive shell"
    echo ""
    echo "Examples:"
    echo "  $0 create /data/wallet.enc --encrypted --interactive"
    echo "  $0 list /data/wallet.enc"
    echo "  $0 add /data/wallet.enc API_KEY"
    echo ""
    exit 0
fi

# Comando speciale: shell interattiva
if [ "$1" = "shell" ]; then
    echo -e "${GREEN}🐚 Opening interactive shell...${NC}"
    docker run --rm -it \
        -v "$(pwd)/$DATA_DIR:/data:rw" \
        -e TERM=xterm-256color \
        --entrypoint /bin/bash \
        "$IMAGE_NAME"
    exit $?
fi

# Esegui comando wallet-tool
run_wallet_tool "$@"
