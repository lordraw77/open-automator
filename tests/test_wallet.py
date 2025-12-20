"""
Unit Tests per wallet.py
Test del sistema di gestione password/segreti
"""
import unittest
import tempfile
import os
import sys
import json
from unittest.mock import Mock, patch, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wallet import Wallet, PlainWallet, resolve_placeholders, resolve_dict_placeholders

class TestWallet(unittest.TestCase):
    """Test per la classe Wallet (criptato)"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_dir = tempfile.mkdtemp()
        self.wallet_file = os.path.join(self.test_dir, 'test_wallet.enc')
        self.master_password = 'test_password_123'

    def tearDown(self):
        """Cleanup dopo ogni test"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_wallet(self):
        """Test creazione wallet criptato"""
        secrets = {
            'db_password': 'secret123',
            'api_key': 'abc-def-ghi'
        }

        wallet = Wallet(self.wallet_file, self.master_password)
        result = wallet.create_wallet(secrets, self.master_password)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.wallet_file))

    def test_load_wallet(self):
        """Test caricamento wallet"""
        secrets = {
            'username': 'admin',
            'password': 'pass123'
        }

        # Crea wallet
        wallet = Wallet(self.wallet_file, self.master_password)
        wallet.create_wallet(secrets, self.master_password)

        # Carica wallet
        wallet2 = Wallet(self.wallet_file, self.master_password)
        wallet2.load_wallet(self.master_password)

        self.assertTrue(wallet2.loaded)
        self.assertEqual(wallet2.secrets, secrets)

    def test_get_secret(self):
        """Test recupero segreto"""
        secrets = {'api_token': 'xyz-token'}

        wallet = Wallet(self.wallet_file, self.master_password)
        wallet.create_wallet(secrets, self.master_password)
        wallet.load_wallet(self.master_password)

        token = wallet.get_secret('api_token')
        self.assertEqual(token, 'xyz-token')

    def test_get_secret_not_found(self):
        """Test recupero segreto inesistente"""
        secrets = {'key1': 'value1'}

        wallet = Wallet(self.wallet_file, self.master_password)
        wallet.create_wallet(secrets, self.master_password)
        wallet.load_wallet(self.master_password)

        with self.assertRaises(KeyError):
            wallet.get_secret('nonexistent_key')

    def test_has_secret(self):
        """Test verifica esistenza segreto"""
        secrets = {'key1': 'value1', 'key2': 'value2'}

        wallet = Wallet(self.wallet_file, self.master_password)
        wallet.create_wallet(secrets, self.master_password)
        wallet.load_wallet(self.master_password)

        self.assertTrue(wallet.has_secret('key1'))
        self.assertFalse(wallet.has_secret('key3'))

    def test_load_wallet_wrong_password(self):
        """Test caricamento con password errata"""
        secrets = {'key': 'value'}

        wallet = Wallet(self.wallet_file, self.master_password)
        wallet.create_wallet(secrets, self.master_password)

        # Prova a caricare con password errata
        wallet2 = Wallet(self.wallet_file, 'wrong_password')

        with self.assertRaises(ValueError):
            wallet2.load_wallet('wrong_password')

class TestPlainWallet(unittest.TestCase):
    """Test per PlainWallet (non criptato)"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_dir = tempfile.mkdtemp()
        self.wallet_file = os.path.join(self.test_dir, 'plain_wallet.json')

    def tearDown(self):
        """Cleanup dopo ogni test"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_load_plain_wallet(self):
        """Test caricamento wallet plain JSON"""
        secrets = {
            'username': 'testuser',
            'password': 'testpass'
        }

        # Crea file JSON
        with open(self.wallet_file, 'w') as f:
            json.dump(secrets, f)

        wallet = PlainWallet(self.wallet_file)
        wallet.load_wallet()

        self.assertTrue(wallet.loaded)
        self.assertEqual(wallet.secrets, secrets)

    def test_get_secret_plain(self):
        """Test recupero segreto da plain wallet"""
        secrets = {'db_host': 'localhost', 'db_port': '5432'}

        with open(self.wallet_file, 'w') as f:
            json.dump(secrets, f)

        wallet = PlainWallet(self.wallet_file)
        wallet.load_wallet()

        self.assertEqual(wallet.get_secret('db_host'), 'localhost')
        self.assertEqual(wallet.get_secret('db_port'), '5432')

    def test_has_secret_plain(self):
        """Test has_secret su plain wallet"""
        secrets = {'key1': 'val1'}

        with open(self.wallet_file, 'w') as f:
            json.dump(secrets, f)

        wallet = PlainWallet(self.wallet_file)
        wallet.load_wallet()

        self.assertTrue(wallet.has_secret('key1'))
        self.assertFalse(wallet.has_secret('key2'))

class TestPlaceholderResolution(unittest.TestCase):
    """Test per risoluzione placeholder"""

    def test_resolve_wallet_placeholder(self):
        """Test risoluzione ${WALLET:key}"""
        mock_wallet = Mock()
        mock_wallet.get_secret.return_value = 'secret_value'

        result = resolve_placeholders('${WALLET:db_password}', mock_wallet)
        self.assertEqual(result, 'secret_value')
        mock_wallet.get_secret.assert_called_once_with('db_password')

    def test_resolve_vault_placeholder(self):
        """Test risoluzione ${VAULT:key} (alias di WALLET)"""
        mock_wallet = Mock()
        mock_wallet.get_secret.return_value = 'vault_secret'

        result = resolve_placeholders('${VAULT:api_key}', mock_wallet)
        self.assertEqual(result, 'vault_secret')

    @patch.dict(os.environ, {'TEST_VAR': 'env_value'})
    def test_resolve_env_placeholder(self):
        """Test risoluzione ${ENV:VAR}"""
        result = resolve_placeholders('${ENV:TEST_VAR}', None)
        self.assertEqual(result, 'env_value')

    def test_resolve_multiple_placeholders(self):
        """Test risoluzione placeholder multipli"""
        mock_wallet = Mock()
        mock_wallet.get_secret.side_effect = lambda k: {'user': 'admin', 'pass': 'secret'}[k]

        result = resolve_placeholders('User: ${WALLET:user}, Pass: ${WALLET:pass}', mock_wallet)
        self.assertEqual(result, 'User: admin, Pass: secret')

    def test_resolve_dict_placeholders_recursive(self):
        """Test risoluzione ricorsiva in dizionario"""
        mock_wallet = Mock()
        mock_wallet.get_secret.return_value = 'db_secret'

        data = {
            'database': {
                'host': 'localhost',
                'password': '${WALLET:db_pass}'
            },
            'list': ['item1', '${WALLET:db_pass}']
        }

        result = resolve_dict_placeholders(data, mock_wallet)
        self.assertEqual(result['database']['password'], 'db_secret')
        self.assertEqual(result['list'][1], 'db_secret')

    def test_resolve_no_wallet_provided(self):
        """Test risoluzione senza wallet (placeholder non risolto)"""
        result = resolve_placeholders('${WALLET:key}', None)
        # Dovrebbe restituire la stringa invariata
        self.assertEqual(result, '${WALLET:key}')

    def test_resolve_non_string_value(self):
        """Test risoluzione su valore non-stringa"""
        result = resolve_placeholders(123, None)
        self.assertEqual(result, 123)

    @patch.dict(os.environ, {}, clear=True)
    def test_resolve_env_not_found(self):
        """Test risoluzione ENV inesistente"""
        result = resolve_placeholders('${ENV:NONEXISTENT}', None)
        # Dovrebbe restituire invariato
        self.assertEqual(result, '${ENV:NONEXISTENT}')

if __name__ == '__main__':
    unittest.main()
