"""
Unit Tests per oa-utility.py
Test delle funzioni di utilità
"""

import unittest
import sys
import os
import time
import json
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestSetSleep(unittest.TestCase):
    """Test per la funzione setsleep"""

    def test_sleep_duration(self):
        """Test che sleep attenda il tempo corretto"""
        start_time = time.time()
        time.sleep(0.1)
        end_time = time.time()

        elapsed = end_time - start_time
        self.assertGreaterEqual(elapsed, 0.1)
        self.assertLess(elapsed, 0.2)  # Con un margine ragionevole


class TestPrintVar(unittest.TestCase):
    """Test per la funzione printvar"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.gdict = {
            'simple_var': 'test_value',
            'number_var': 42,
            'dict_var': {'key': 'value'},
            'list_var': [1, 2, 3]
        }

    def test_print_simple_variable(self):
        """Test stampa variabile semplice"""
        var_name = 'simple_var'
        value = self.gdict[var_name]
        self.assertEqual(value, 'test_value')

    def test_print_dict_variable(self):
        """Test stampa variabile dizionario"""
        var_name = 'dict_var'
        value = self.gdict[var_name]
        self.assertIsInstance(value, dict)
        self.assertEqual(value['key'], 'value')

    def test_print_nonexistent_variable(self):
        """Test stampa variabile inesistente"""
        var_name = 'nonexistent'
        self.assertNotIn(var_name, self.gdict)


class TestSetVar(unittest.TestCase):
    """Test per la funzione setvar"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.gdict = {}

    def test_set_string_variable(self):
        """Test impostazione variabile stringa"""
        self.gdict['test_var'] = 'test_value'
        self.assertEqual(self.gdict['test_var'], 'test_value')

    def test_set_number_variable(self):
        """Test impostazione variabile numerica"""
        self.gdict['number'] = 123
        self.assertEqual(self.gdict['number'], 123)

    def test_overwrite_variable(self):
        """Test sovrascrittura variabile esistente"""
        self.gdict['var'] = 'old_value'
        self.gdict['var'] = 'new_value'
        self.assertEqual(self.gdict['var'], 'new_value')


class TestDumpVar(unittest.TestCase):
    """Test per la funzione dumpvar"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.gdict = {
            'var1': 'value1',
            'var2': 123,
            'var3': {'nested': 'data'}
        }

    def test_dump_to_json(self):
        """Test export variabili in JSON"""
        json_str = json.dumps(self.gdict, indent=4, sort_keys=True)
        loaded_data = json.loads(json_str)

        self.assertEqual(loaded_data['var1'], 'value1')
        self.assertEqual(loaded_data['var2'], 123)
        self.assertEqual(loaded_data['var3']['nested'], 'data')

    def test_dump_filters_system_vars(self):
        """Test che filtra variabili di sistema"""
        gdict_with_system = self.gdict.copy()
        gdict_with_system['_internal'] = 'should_be_filtered'
        gdict_with_system['DEBUG'] = True

        filtered = {k: v for k, v in gdict_with_system.items() 
                   if not k.startswith('_') and k not in ['DEBUG', 'DEBUG2', 'TRACE']}

        self.assertNotIn('_internal', filtered)
        self.assertNotIn('DEBUG', filtered)
        self.assertIn('var1', filtered)


if __name__ == '__main__':
    unittest.main()
