"""
Unit Tests per oa-pg.py
Test operazioni PostgreSQL
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestOaPg(unittest.TestCase):
    """Test per modulo oa-pg"""

    def setUp(self):
        """Setup prima di ogni test"""
        # Import dinamico
        import importlib.util
        spec = importlib.util.spec_from_file_location("oa_pg", "./modules/oa-pg.py")
        self.oa_pg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.oa_pg)

        self.oa_pg.gdict = {'_wallet': None}
        self.mock_self = Mock()
        self.mock_self.gdict = self.oa_pg.gdict

    @patch('psycopg2.connect')
    def test_executeFatchAll_success(self, mock_connect):
        """Test esecuzione SELECT con fetchall"""
        # Mock connessione e cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock risultati
        mock_cursor.description = [('id',), ('name',), ('age',)]
        mock_cursor.fetchall.return_value = [
            (1, 'Alice', 30),
            (2, 'Bob', 25)
        ]

        rows, columns = self.oa_pg.executeFatchAll(
            'testdb', 'localhost', 'user', 'pass', 5432,
            'SELECT * FROM users'
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(columns, ['id', 'name', 'age'])
        self.assertEqual(rows[0][1], 'Alice')
        mock_cursor.execute.assert_called_once()

    @patch('psycopg2.connect')
    def test_executeStatement_insert(self, mock_connect):
        """Test esecuzione INSERT"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        rows_affected = self.oa_pg.executeStatement(
            'testdb', 'localhost', 'user', 'pass', 5432,
            "INSERT INTO users (name) VALUES ('Test')"
        )

        self.assertEqual(rows_affected, 1)
        mock_conn.commit.assert_called_once()

    @patch('psycopg2.connect')
    def test_select_success(self, mock_connect):
        """Test funzione select"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = [('id',), ('name',)]
        mock_cursor.fetchall.return_value = [
            (1, 'Test User')
        ]

        param = {
            'pgdatabase': 'testdb',
            'pgdbhost': 'localhost',
            'pgdbusername': 'user',
            'pgdbpassword': 'pass',
            'pgdbport': '5432',
            'statement': 'SELECT * FROM users',
            'format': 'dict'
        }

        success, output = self.oa_pg.select(self.mock_self, param)

        self.assertTrue(success)
        self.assertIn('rows', output)
        self.assertEqual(len(output['rows']), 1)
        self.assertEqual(output['rows'][0]['name'], 'Test User')
        self.assertEqual(output['row_count'], 1)

    @patch('psycopg2.connect')
    def test_select_format_json(self, mock_connect):
        """Test select con formato JSON"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.description = [('id',), ('value',)]
        mock_cursor.fetchall.return_value = [(1, 100)]

        param = {
            'pgdatabase': 'testdb',
            'pgdbhost': 'localhost',
            'pgdbusername': 'user',
            'pgdbpassword': 'pass',
            'pgdbport': '5432',
            'statement': 'SELECT * FROM data',
            'format': 'json'
        }

        success, output = self.oa_pg.select(self.mock_self, param)

        self.assertTrue(success)
        self.assertIsInstance(output['rows'], str)  # JSON string
        self.assertIn('"id"', output['rows'])

    @patch('psycopg2.connect')
    def test_execute_update(self, mock_connect):
        """Test funzione execute per UPDATE"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 3

        param = {
            'pgdatabase': 'testdb',
            'pgdbhost': 'localhost',
            'pgdbusername': 'user',
            'pgdbpassword': 'pass',
            'pgdbport': '5432',
            'statement': 'UPDATE users SET active=true'
        }

        success, output = self.oa_pg.execute(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['rows_affected'], 3)
        mock_conn.commit.assert_called_once()

    @patch('psycopg2.connect')
    def test_execute_fail_on_zero(self, mock_connect):
        """Test execute con fail_on_zero quando nessuna riga affetta"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 0

        param = {
            'pgdatabase': 'testdb',
            'pgdbhost': 'localhost',
            'pgdbusername': 'user',
            'pgdbpassword': 'pass',
            'pgdbport': '5432',
            'statement': 'DELETE FROM users WHERE id=-1',
            'fail_on_zero': True
        }

        success, output = self.oa_pg.execute(self.mock_self, param)

        self.assertFalse(success)
        self.assertEqual(output['rows_affected'], 0)

    @patch('psycopg2.connect')
    def test_insert_single_row(self, mock_connect):
        """Test insert helper con singola riga"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        param = {
            'pgdatabase': 'testdb',
            'pgdbhost': 'localhost',
            'pgdbusername': 'user',
            'pgdbpassword': 'pass',
            'pgdbport': '5432',
            'table': 'users',
            'data': {'name': 'John', 'email': 'john@test.com'}
        }

        success, output = self.oa_pg.insert(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['rows_inserted'], 1)
        self.assertEqual(output['table'], 'users')

    @patch('psycopg2.connect')
    def test_insert_multiple_rows(self, mock_connect):
        """Test insert con righe multiple"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 3

        param = {
            'pgdatabase': 'testdb',
            'pgdbhost': 'localhost',
            'pgdbusername': 'user',
            'pgdbpassword': 'pass',
            'pgdbport': '5432',
            'table': 'products',
            'data': [
                {'name': 'Product1', 'price': 10.0},
                {'name': 'Product2', 'price': 20.0},
                {'name': 'Product3', 'price': 30.0}
            ]
        }

        success, output = self.oa_pg.insert(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['rows_inserted'], 3)

    @patch('psycopg2.connect')
    def test_insert_from_input(self, mock_connect):
        """Test insert con data da input precedente"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 2

        param = {
            'pgdatabase': 'testdb',
            'pgdbhost': 'localhost',
            'pgdbusername': 'user',
            'pgdbpassword': 'pass',
            'pgdbport': '5432',
            'table': 'logs',
            'input': {
                'rows': [
                    {'message': 'Log1', 'level': 'INFO'},
                    {'message': 'Log2', 'level': 'ERROR'}
                ]
            }
        }

        success, output = self.oa_pg.insert(self.mock_self, param)

        self.assertTrue(success)
        self.assertEqual(output['rows_inserted'], 2)

    @patch('psycopg2.connect')
    def test_select_connection_error(self, mock_connect):
        """Test gestione errore di connessione"""
        import psycopg2
        mock_connect.side_effect = psycopg2.OperationalError('Connection refused')

        param = {
            'pgdatabase': 'testdb',
            'pgdbhost': 'unreachable',
            'pgdbusername': 'user',
            'pgdbpassword': 'pass',
            'pgdbport': '5432',
            'statement': 'SELECT 1'
        }

        success, output = self.oa_pg.select(self.mock_self, param)

        self.assertFalse(success)

    @patch('psycopg2.connect')
    def test_execute_syntax_error(self, mock_connect):
        """Test gestione errore di sintassi SQL"""
        import psycopg2
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = psycopg2.ProgrammingError('syntax error')

        param = {
            'pgdatabase': 'testdb',
            'pgdbhost': 'localhost',
            'pgdbusername': 'user',
            'pgdbpassword': 'pass',
            'pgdbport': '5432',
            'statement': 'INVALID SQL'
        }

        success, output = self.oa_pg.execute(self.mock_self, param)

        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
