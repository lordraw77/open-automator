"""
Unit Tests per oa-notify.py
Test notifiche (Telegram, Email)
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestOaNotify(unittest.TestCase):
    """Test per modulo oa-notify"""

    def setUp(self):
        """Setup prima di ogni test"""
        # Import dinamico
        import importlib.util
        spec = importlib.util.spec_from_file_location("oa_notify", "./modules/oa-notify.py")
        self.oa_notify = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.oa_notify)

        self.oa_notify.gdict = {'_wallet': None}
        self.mock_self = Mock()
        self.mock_self.gdict = self.oa_notify.gdict

    @patch('requests.get')
    def test_sendtelegramnotify_success(self, mock_get):
        """Test invio notifica Telegram con successo"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True, 'result': {}}
        mock_get.return_value = mock_response

        param = {
            'tokenid': 'fake_bot_token',
            'chatid': ['123456789'],
            'message': 'Test message'
        }

        success, output = self.oa_notify.sendtelegramnotify(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['total_chats'], 1)
        self.assertEqual(output['successful'], 1)
        self.assertEqual(output['failed'], 0)

    @patch('requests.get')
    def test_sendtelegramnotify_multiple_chats(self, mock_get):
        """Test invio a chat multiple"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_get.return_value = mock_response

        param = {
            'tokenid': 'bot_token',
            'chatid': ['chat1', 'chat2', 'chat3'],
            'message': 'Broadcast message'
        }

        success, output = self.oa_notify.sendtelegramnotify(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['total_chats'], 3)
        self.assertEqual(output['successful'], 3)
        self.assertEqual(mock_get.call_count, 3)

    @patch('requests.get')
    def test_sendtelegramnotify_partial_failure(self, mock_get):
        """Test invio con alcuni fallimenti"""
        # Prima chiamata successo, seconda fallimento
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'ok': True}

        mock_response_fail = Mock()
        mock_response_fail.status_code = 400
        mock_response_fail.reason = 'Bad Request'

        mock_get.side_effect = [mock_response_success, mock_response_fail]

        param = {
            'tokenid': 'bot_token',
            'chatid': ['valid_chat', 'invalid_chat'],
            'message': 'Test'
        }

        success, output = self.oa_notify.sendtelegramnotify(self.mock_self, param)

        self.assertFalse(success)  # Almeno un fallimento = task failed
        self.assertEqual(output['successful'], 1)
        self.assertEqual(output['failed'], 1)

    @patch('requests.get')
    def test_sendtelegramnotify_from_input(self, mock_get):
        """Test invio con messaggio da input precedente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_get.return_value = mock_response

        param = {
            'tokenid': 'token',
            'chatid': ['12345'],
            'input': {
                'content': 'Message from previous task'
            }
        }

        success, output = self.oa_notify.sendtelegramnotify(self.mock_self, param)

        self.assertTrue(success)
        # Verifica che il messaggio sia stato preso dall'input
        call_args = str(mock_get.call_args)
        self.assertIn('Message from previous task', call_args)

    @patch('requests.get')
    def test_sendtelegramnotify_dict_to_json(self, mock_get):
        """Test conversione dict a JSON per messaggio"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_get.return_value = mock_response

        param = {
            'tokenid': 'token',
            'chatid': ['12345'],
            'input': {
                'status': 'completed',
                'items': 42,
                'duration': 10.5
            }
        }

        success, output = self.oa_notify.sendtelegramnotify(self.mock_self, param)

        self.assertTrue(success)

    @patch('smtplib.SMTP_SSL')
    def test_sendmailbygmail_success(self, mock_smtp):
        """Test invio email Gmail con successo"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        param = {
            'senderemail': 'sender@gmail.com',
            'receiveremail': 'receiver@gmail.com',
            'senderpassword': 'app_password',
            'subject': 'Test Subject',
            'messagetext': 'Plain text message'
        }

        success, output = self.oa_notify.sendmailbygmail(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['from'], 'sender@gmail.com')
        self.assertEqual(output['to'], 'receiver@gmail.com')
        self.assertEqual(output['message_type'], 'plain')
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()

    @patch('smtplib.SMTP_SSL')
    def test_sendmailbygmail_html(self, mock_smtp):
        """Test invio email HTML"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        param = {
            'senderemail': 'sender@gmail.com',
            'receiveremail': 'receiver@gmail.com',
            'senderpassword': 'password',
            'subject': 'HTML Email',
            'messagehtml': '<h1>HTML Content</h1>'
        }

        success, output = self.oa_notify.sendmailbygmail(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['message_type'], 'html')

    @patch('smtplib.SMTP_SSL')
    def test_sendmailbygmail_multipart(self, mock_smtp):
        """Test invio email multipart (text + HTML)"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        param = {
            'senderemail': 'sender@gmail.com',
            'receiveremail': 'receiver@gmail.com',
            'senderpassword': 'password',
            'subject': 'Multipart',
            'messagetext': 'Plain text',
            'messagehtml': '<p>HTML version</p>'
        }

        success, output = self.oa_notify.sendmailbygmail(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['message_type'], 'multipart')
        self.assertGreater(output['text_length'], 0)
        self.assertGreater(output['html_length'], 0)

    @patch('smtplib.SMTP_SSL')
    def test_sendmailbygmail_auth_failure(self, mock_smtp):
        """Test fallimento autenticazione"""
        import smtplib
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, 'Auth failed')
        mock_smtp.return_value.__enter__.return_value = mock_server

        param = {
            'senderemail': 'sender@gmail.com',
            'receiveremail': 'receiver@gmail.com',
            'senderpassword': 'wrong_password',
            'subject': 'Test',
            'messagetext': 'Message'
        }

        success, output = self.oa_notify.sendmailbygmail(self.mock_self, param)

        self.assertFalse(success)

    def test_formatmessage_text_format(self):
        """Test formattazione messaggio in formato text"""
        param = {
            'data': {
                'key1': 'value1',
                'key2': 'value2',
                'key3': 123
            },
            'format': 'text'
        }

        success, output = self.oa_notify.formatmessage(self.mock_self, param)

        self.assertTrue(success)
        self.assertIn('content', output)
        self.assertIn('key1: value1', output['content'])
        self.assertIn('key2: value2', output['content'])

    def test_formatmessage_json_format(self):
        """Test formattazione in JSON"""
        param = {
            'data': {
                'status': 'success',
                'count': 42
            },
            'format': 'json'
        }

        success, output = self.oa_notify.formatmessage(self.mock_self, param)

        self.assertTrue(success)
        self.assertIsInstance(output['content'], str)
        # Verifica che sia JSON valido
        parsed = json.loads(output['content'])
        self.assertEqual(parsed['status'], 'success')
        self.assertEqual(parsed['count'], 42)

    def test_formatmessage_markdown_format(self):
        """Test formattazione in Markdown"""
        param = {
            'data': {
                'title': 'Report',
                'items': 10,
                'status': 'OK'
            },
            'format': 'markdown'
        }

        success, output = self.oa_notify.formatmessage(self.mock_self, param)

        self.assertTrue(success)
        self.assertIn('**', output['content'])  # Bold markers
        self.assertIn('•', output['content'])  # Bullet points

    def test_formatmessage_with_template(self):
        """Test formattazione con template"""
        param = {
            'data': {
                'name': 'John',
                'age': 30,
                'city': 'Rome'
            },
            'template': 'User {name} is {age} years old from {city}'
        }

        success, output = self.oa_notify.formatmessage(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['content'], 'User John is 30 years old from Rome')

    def test_formatmessage_from_input(self):
        """Test formattazione con data da input"""
        param = {
            'input': {
                'result': 'completed',
                'total': 100
            },
            'format': 'text'
        }

        success, output = self.oa_notify.formatmessage(self.mock_self, param)

        self.assertTrue(success)
        self.assertIn('result', output['content'])

if __name__ == '__main__':
    unittest.main()
