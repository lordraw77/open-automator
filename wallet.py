"""
Open-Automator Wallet Module

Gestisce password e segreti in modo sicuro
"""

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import getpass
import logging
from logger_config import AutomatorLogger

logger = AutomatorLogger.get_logger('oa-wallet')


class Wallet:
    """Gestisce un wallet di password criptato"""
    
    def __init__(self, wallet_file='wallet.enc', master_password=None):
        self.wallet_file = wallet_file
        self.master_password = master_password
        self.secrets = {}
        self.loaded = False
        
    def _derive_key(self, password, salt):
        """Deriva una chiave di cifratura dalla password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def create_wallet(self, secrets_dict, master_password=None):
        """
        Crea un nuovo wallet criptato
        
        Args:
            secrets_dict: dizionario {key: value} di segreti
            master_password: password master per criptare (se None, chiede interattivamente)
        """
        if master_password is None:
            master_password = getpass.getpass("Enter master password for wallet: ")
            confirm = getpass.getpass("Confirm master password: ")
            if master_password != confirm:
                raise ValueError("Passwords do not match")
        
        # Genera salt casuale
        salt = os.urandom(16)
        
        # Deriva chiave
        key = self._derive_key(master_password, salt)
        fernet = Fernet(key)
        
        # Cripta i segreti
        data = json.dumps(secrets_dict).encode()
        encrypted = fernet.encrypt(data)
        
        # Salva salt + dati criptati
        wallet_data = {
            'salt': base64.b64encode(salt).decode(),
            'data': encrypted.decode()
        }
        
        with open(self.wallet_file, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        
        logger.info(f"Wallet created: {self.wallet_file}")
        return True
    
    def load_wallet(self, master_password=None):
        """
        Carica il wallet criptato
        
        Args:
            master_password: password master (se None, chiede interattivamente)
        """
        if not os.path.exists(self.wallet_file):
            raise FileNotFoundError(f"Wallet file not found: {self.wallet_file}")
        
        if master_password is None:
            master_password = self.master_password
        
        if master_password is None:
            master_password = getpass.getpass(f"Enter master password for {self.wallet_file}: ")
        
        # Leggi wallet
        with open(self.wallet_file, 'r') as f:
            wallet_data = json.load(f)
        
        salt = base64.b64decode(wallet_data['salt'])
        encrypted_data = wallet_data['data'].encode()
        
        # Deriva chiave e decripta
        try:
            key = self._derive_key(master_password, salt)
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted_data)
            self.secrets = json.loads(decrypted.decode())
            self.loaded = True
            logger.info(f"Wallet loaded: {len(self.secrets)} secrets available")
            return True
        except Exception as e:
            logger.error(f"Failed to decrypt wallet: {e}")
            raise ValueError("Invalid master password or corrupted wallet")
    
    def get_secret(self, key):
        """Recupera un segreto dal wallet"""
        if not self.loaded:
            raise RuntimeError("Wallet not loaded")
        
        if key not in self.secrets:
            raise KeyError(f"Secret '{key}' not found in wallet")
        
        return self.secrets[key]
    
    def has_secret(self, key):
        """Verifica se un segreto esiste nel wallet"""
        return self.loaded and key in self.secrets


class PlainWallet:
    """Wallet non criptato (per sviluppo/test)"""
    
    def __init__(self, wallet_file='wallet.json'):
        self.wallet_file = wallet_file
        self.secrets = {}
        self.loaded = False
    
    def load_wallet(self):
        """Carica wallet JSON in chiaro"""
        if not os.path.exists(self.wallet_file):
            raise FileNotFoundError(f"Wallet file not found: {self.wallet_file}")
        
        with open(self.wallet_file, 'r') as f:
            self.secrets = json.load(f)
        
        self.loaded = True
        logger.warning(f"Plain wallet loaded (INSECURE): {len(self.secrets)} secrets")
        return True
    
    def get_secret(self, key):
        """Recupera un segreto dal wallet"""
        if not self.loaded:
            raise RuntimeError("Wallet not loaded")
        
        if key not in self.secrets:
            raise KeyError(f"Secret '{key}' not found in wallet")
        
        return self.secrets[key]
    
    def has_secret(self, key):
        """Verifica se un segreto esiste"""
        return self.loaded and key in self.secrets


def resolve_placeholders(value, wallet=None):
    """
    Risolve i placeholder in una stringa
    
    Supporta:
    - ${WALLET:key} - dal wallet
    - ${ENV:VAR} - da variabile d'ambiente
    - ${VAULT:key} - alias per WALLET
    
    Args:
        value: stringa con placeholder
        wallet: istanza Wallet o PlainWallet
    
    Returns:
        stringa con placeholder risolti
    """
    import re
    
    if not isinstance(value, str):
        return value
    
    # Pattern per placeholder
    pattern = r'\$\{(WALLET|VAULT|ENV):([^}]+)\}'
    
    def replace_placeholder(match):
        source = match.group(1)
        key = match.group(2)
        
        if source in ['WALLET', 'VAULT']:
            if wallet is None:
                logger.warning(f"Placeholder ${{{source}:{key}}} found but no wallet loaded")
                return match.group(0)  # lascia invariato
            
            try:
                return wallet.get_secret(key)
            except KeyError:
                logger.error(f"Secret '{key}' not found in wallet")
                return match.group(0)
        
        elif source == 'ENV':
            env_value = os.environ.get(key)
            if env_value is None:
                logger.warning(f"Environment variable '{key}' not found")
                return match.group(0)
            return env_value
        
        return match.group(0)
    
    return re.sub(pattern, replace_placeholder, value)


def resolve_dict_placeholders(data, wallet=None):
    """
    Risolve i placeholder in un dizionario ricorsivamente
    
    Args:
        data: dizionario con potenziali placeholder
        wallet: istanza Wallet
    
    Returns:
        dizionario con placeholder risolti
    """
    if isinstance(data, dict):
        return {k: resolve_dict_placeholders(v, wallet) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_dict_placeholders(item, wallet) for item in data]
    elif isinstance(data, str):
        return resolve_placeholders(data, wallet)
    else:
        return data