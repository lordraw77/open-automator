#!/usr/bin/env python3
"""
Open-Automator Wallet Management Tool
CLI per creare e gestire wallet cifrati e plain
"""

import argparse
import sys
import json
import os
from getpass import getpass

try:
    from wallet import Wallet, PlainWallet
except ImportError:
    print("ERROR: wallet.py module not found")
    sys.exit(1)


def create_wallet(args):
    """Crea un nuovo wallet"""
    print(f"🔐 Creating {'encrypted' if args.encrypted else 'plain'} wallet: {args.wallet_file}")

    # Conferma se il file esiste già
    if os.path.exists(args.wallet_file) and not args.force:
        print(f"❌ ERROR: File {args.wallet_file} already exists. Use --force to overwrite.")
        return False

    secrets = {}

    # Carica secrets da JSON file se specificato
    if args.secrets_file:
        print(f"📄 Loading secrets from {args.secrets_file}")
        with open(args.secrets_file, 'r') as f:
            secrets = json.load(f)
        print(f"✅ Loaded {len(secrets)} secrets")

    # Aggiungi secrets interattivi
    elif args.interactive:
        print("\n📝 Enter secrets (press Enter with empty key to finish):")
        while True:
            key = input("  Secret key: ").strip()
            if not key:
                break
            value = getpass(f"  Value for '{key}': ")
            secrets[key] = value
            print(f"  ✅ Added '{key}'")

    # Crea wallet
    try:
        if args.encrypted:
            password = args.password
            if not password:
                password = getpass("Enter master password: ")
                password_confirm = getpass("Confirm password: ")
                if password != password_confirm:
                    print("❌ ERROR: Passwords don't match")
                    return False

            wallet = Wallet(args.wallet_file, password)
            wallet.create_wallet(secrets, password)
            print(f"✅ Encrypted wallet created: {args.wallet_file}")
        else:
            with open(args.wallet_file, 'w') as f:
                json.dump(secrets, f, indent=2)
            print(f"✅ Plain wallet created: {args.wallet_file}")

        print(f"📊 Total secrets: {len(secrets)}")
        return True

    except Exception as e:
        print(f"❌ ERROR: Failed to create wallet: {e}")
        return False


def list_secrets(args):
    """Lista secrets nel wallet"""
    print(f"📋 Listing secrets in: {args.wallet_file}")

    try:
        wallet = load_wallet(args)
        if not wallet:
            return False

        secrets = list(wallet.secrets.keys())

        if not secrets:
            print("⚠️  No secrets found in wallet")
            return True

        print(f"\n🔑 Found {len(secrets)} secrets:")
        for i, key in enumerate(sorted(secrets), 1):
            if args.show_values:
                value = wallet.get_secret(key)
                print(f"  {i}. {key} = {value}")
            else:
                print(f"  {i}. {key}")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def add_secret(args):
    """Aggiunge un secret al wallet"""
    print(f"➕ Adding secret to: {args.wallet_file}")

    try:
        wallet = load_wallet(args)
        if not wallet:
            return False

        key = args.key
        value = args.value if args.value else getpass(f"Enter value for '{key}': ")

        if key in wallet.secrets and not args.force:
            print(f"⚠️  Secret '{key}' already exists. Use --force to overwrite.")
            return False

        wallet.secrets[key] = value
        save_wallet(wallet, args)

        print(f"✅ Secret '{key}' added successfully")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def remove_secret(args):
    """Rimuove un secret dal wallet"""
    print(f"➖ Removing secret from: {args.wallet_file}")

    try:
        wallet = load_wallet(args)
        if not wallet:
            return False

        if args.key not in wallet.secrets:
            print(f"⚠️  Secret '{args.key}' not found")
            return False

        del wallet.secrets[args.key]
        save_wallet(wallet, args)

        print(f"✅ Secret '{args.key}' removed successfully")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def get_secret(args):
    """Ottiene il valore di un secret"""
    try:
        wallet = load_wallet(args)
        if not wallet:
            return False

        value = wallet.get_secret(args.key)
        print(value)
        return True

    except KeyError:
        print(f"❌ ERROR: Secret '{args.key}' not found", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        return False


def change_password(args):
    """Cambia la password del wallet (solo encrypted)"""
    print(f"🔐 Changing password for: {args.wallet_file}")

    if not args.wallet_file.endswith('.enc'):
        print("❌ ERROR: Password change only supported for encrypted wallets")
        return False

    try:
        # Carica con vecchia password
        old_password = args.password if args.password else getpass("Enter current password: ")
        wallet = Wallet(args.wallet_file, old_password)
        wallet.load_wallet(old_password)

        # Nuova password
        new_password = getpass("Enter new password: ")
        new_password_confirm = getpass("Confirm new password: ")

        if new_password != new_password_confirm:
            print("❌ ERROR: Passwords don't match")
            return False

        # Salva con nuova password
        wallet.create_wallet(wallet.secrets, new_password)

        print("✅ Password changed successfully")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def export_secrets(args):
    """Esporta secrets in JSON"""
    print(f"📤 Exporting secrets from: {args.wallet_file}")

    try:
        wallet = load_wallet(args)
        if not wallet:
            return False

        output_file = args.output or "secrets-export.json"

        with open(output_file, 'w') as f:
            json.dump(wallet.secrets, f, indent=2)

        print(f"✅ Exported {len(wallet.secrets)} secrets to: {output_file}")
        print("⚠️  WARNING: Exported file contains plaintext secrets!")
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def info_wallet(args):
    """Mostra informazioni sul wallet"""
    print(f"ℹ️  Wallet information: {args.wallet_file}")

    try:
        if not os.path.exists(args.wallet_file):
            print(f"❌ ERROR: Wallet file not found: {args.wallet_file}")
            return False

        file_size = os.path.getsize(args.wallet_file)
        is_encrypted = args.wallet_file.endswith('.enc')

        print(f"\n📊 Wallet Info:")
        print(f"  File: {args.wallet_file}")
        print(f"  Size: {file_size} bytes")
        print(f"  Type: {'Encrypted' if is_encrypted else 'Plain'}")

        wallet = load_wallet(args)
        if wallet:
            print(f"  Secrets: {len(wallet.secrets)}")

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def load_wallet(args):
    """Helper per caricare un wallet"""
    if not os.path.exists(args.wallet_file):
        print(f"❌ ERROR: Wallet file not found: {args.wallet_file}")
        return None

    if args.wallet_file.endswith('.enc'):
        password = args.password if args.password else getpass("Enter password: ")
        wallet = Wallet(args.wallet_file, password)
        wallet.load_wallet(password)
    else:
        wallet = PlainWallet(args.wallet_file)
        wallet.load_wallet()

    return wallet


def save_wallet(wallet, args):
    """Helper per salvare un wallet"""
    if isinstance(wallet, Wallet):
        password = args.password if args.password else getpass("Enter password: ")
        wallet.create_wallet(wallet.secrets, password)
    else:
        with open(wallet.wallet_file, 'w') as f:
            json.dump(wallet.secrets, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Open-Automator Wallet Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create new wallet')
    create_parser.add_argument('wallet_file', help='Wallet file path')
    create_parser.add_argument('-e', '--encrypted', action='store_true', help='Create encrypted wallet')
    create_parser.add_argument('-p', '--password', help='Master password (for encrypted)')
    create_parser.add_argument('-s', '--secrets-file', help='JSON file with initial secrets')
    create_parser.add_argument('-i', '--interactive', action='store_true', help='Add secrets interactively')
    create_parser.add_argument('-f', '--force', action='store_true', help='Overwrite if exists')

    # List command
    list_parser = subparsers.add_parser('list', help='List secrets')
    list_parser.add_argument('wallet_file', help='Wallet file path')
    list_parser.add_argument('-p', '--password', help='Master password (for encrypted)')
    list_parser.add_argument('-v', '--show-values', action='store_true', help='Show secret values')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add secret')
    add_parser.add_argument('wallet_file', help='Wallet file path')
    add_parser.add_argument('key', help='Secret key')
    add_parser.add_argument('-v', '--value', help='Secret value (prompt if not provided)')
    add_parser.add_argument('-p', '--password', help='Master password (for encrypted)')
    add_parser.add_argument('-f', '--force', action='store_true', help='Overwrite if exists')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove secret')
    remove_parser.add_argument('wallet_file', help='Wallet file path')
    remove_parser.add_argument('key', help='Secret key to remove')
    remove_parser.add_argument('-p', '--password', help='Master password (for encrypted)')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get secret value')
    get_parser.add_argument('wallet_file', help='Wallet file path')
    get_parser.add_argument('key', help='Secret key')
    get_parser.add_argument('-p', '--password', help='Master password (for encrypted)')

    # Change password command
    passwd_parser = subparsers.add_parser('change-password', help='Change wallet password')
    passwd_parser.add_argument('wallet_file', help='Wallet file path (.enc)')
    passwd_parser.add_argument('-p', '--password', help='Current password')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export secrets to JSON')
    export_parser.add_argument('wallet_file', help='Wallet file path')
    export_parser.add_argument('-o', '--output', help='Output JSON file')
    export_parser.add_argument('-p', '--password', help='Master password (for encrypted)')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show wallet information')
    info_parser.add_argument('wallet_file', help='Wallet file path')
    info_parser.add_argument('-p', '--password', help='Master password (for encrypted)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Esegui comando
    commands = {
        'create': create_wallet,
        'list': list_secrets,
        'add': add_secret,
        'remove': remove_secret,
        'get': get_secret,
        'change-password': change_password,
        'export': export_secrets,
        'info': info_wallet
    }

    success = commands[args.command](args)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())



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
