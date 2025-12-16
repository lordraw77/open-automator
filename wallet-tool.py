#!/usr/bin/env python3
"""
Tool CLI per gestire il wallet Open-Automator
"""

import argparse
import json
import sys
from wallet import Wallet, PlainWallet


def create_encrypted_wallet(args):
    """Crea un wallet criptato"""
    # Leggi segreti da JSON o interattivo
    if args.from_json:
        with open(args.from_json, 'r') as f:
            secrets = json.load(f)
    else:
        secrets = {}
        print("Enter secrets (empty key to finish):")
        while True:
            key = input("Secret key: ").strip()
            if not key:
                break
            value = input(f"Value for '{key}': ").strip()
            secrets[key] = value
    
    if not secrets:
        print("✗ No secrets provided")
        sys.exit(1)
    
    wallet = Wallet(args.output)
    wallet.create_wallet(secrets, master_password=args.password)
    print(f"✓ Encrypted wallet created: {args.output}")
    print(f"  Secrets stored: {len(secrets)}")


def create_plain_wallet(args):
    """Crea un wallet in chiaro (JSON)"""
    if args.from_json:
        with open(args.from_json, 'r') as f:
            secrets = json.load(f)
    else:
        secrets = {}
        print("Enter secrets (empty key to finish):")
        while True:
            key = input("Secret key: ").strip()
            if not key:
                break
            value = input(f"Value for '{key}': ").strip()
            secrets[key] = value
    
    if not secrets:
        print("✗ No secrets provided")
        sys.exit(1)
    
    with open(args.output, 'w') as f:
        json.dump(secrets, f, indent=2)
    
    print(f"✓ Plain wallet created: {args.output}")
    print(f"  Secrets stored: {len(secrets)}")
    print("⚠ WARNING: This wallet is NOT encrypted!")


def list_secrets(args):
    """Lista le chiavi nel wallet (senza mostrare i valori)"""
    try:
        if args.encrypted:
            wallet = Wallet(args.wallet)
            wallet.load_wallet(master_password=args.password)
        else:
            wallet = PlainWallet(args.wallet)
            wallet.load_wallet()
        
        print(f"Secrets in {args.wallet}:")
        for key in sorted(wallet.secrets.keys()):
            print(f"  - {key}")
        print(f"\nTotal: {len(wallet.secrets)} secrets")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def get_secret(args):
    """Recupera un segreto specifico"""
    try:
        if args.encrypted:
            wallet = Wallet(args.wallet)
            wallet.load_wallet(master_password=args.password)
        else:
            wallet = PlainWallet(args.wallet)
            wallet.load_wallet()
        
        value = wallet.get_secret(args.key)
        if args.show:
            print(f"{args.key}: {value}")
        else:
            print(f"{args.key}: {'*' * min(len(str(value)), 20)}")
    except KeyError:
        print(f"✗ Secret '{args.key}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Open-Automator Wallet Tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Comando: create
    create_parser = subparsers.add_parser('create', help='Create a new wallet')
    create_parser.add_argument('--encrypted', action='store_true', help='Create encrypted wallet')
    create_parser.add_argument('--from-json', type=str, help='Load secrets from JSON file')
    create_parser.add_argument('--output', type=str, default='wallet.json', help='Output file')
    create_parser.add_argument('--password', type=str, help='Master password (for encrypted)')
    
    # Comando: list
    list_parser = subparsers.add_parser('list', help='List secrets in wallet')
    list_parser.add_argument('--wallet', type=str, default='wallet.json', help='Wallet file')
    list_parser.add_argument('--encrypted', action='store_true', help='Wallet is encrypted')
    list_parser.add_argument('--password', type=str, help='Master password')
    
    # Comando: get
    get_parser = subparsers.add_parser('get', help='Get a secret from wallet')
    get_parser.add_argument('key', type=str, help='Secret key')
    get_parser.add_argument('--wallet', type=str, default='wallet.json', help='Wallet file')
    get_parser.add_argument('--encrypted', action='store_true', help='Wallet is encrypted')
    get_parser.add_argument('--password', type=str, help='Master password')
    get_parser.add_argument('--show', action='store_true', help='Show value in clear')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        if args.encrypted:
            create_encrypted_wallet(args)
        else:
            create_plain_wallet(args)
    elif args.command == 'list':
        list_secrets(args)
    elif args.command == 'get':
        get_secret(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()



# # Crea wallet in chiaro (per sviluppo)
# python3.12 wallet-tool.py create --output wallet.json

# # Crea wallet criptato
# python3.12 wallet-tool.py create --encrypted --output wallet.enc

# # Lista segreti
# python3.12 wallet-tool.py list --wallet wallet.json

# # Recupera un segreto
# python3.12 wallet-tool.py get db_password --wallet wallet.json --show

# # Esegui automator con wallet
# python3.12 ./automator.py ./mywf.yaml

# # Con wallet criptato, passa password via env
# export OA_WALLET_PASSWORD="your_master_password"
# python3.12 ./automator.py ./mywf.yaml
