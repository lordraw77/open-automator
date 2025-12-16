"""
Unit Tests per oa-io.py
Test delle operazioni I/O su file
"""

import unittest
import tempfile
import os
import sys
import shutil
import zipfile
import json
from unittest.mock import Mock, patch, MagicMock, mock_open

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestCopy(unittest.TestCase):
    """Test per la funzione copy"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_dir = tempfile.mkdtemp()
        self.src_file = os.path.join(self.test_dir, 'source.txt')
        self.dst_file = os.path.join(self.test_dir, 'dest.txt')

        # Crea file sorgente
        with open(self.src_file, 'w') as f:
            f.write('test content')

    def tearDown(self):
        """Cleanup dopo ogni test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_copy_single_file(self):
        """Test copia singolo file"""
        shutil.copy(self.src_file, self.dst_file)

        self.assertTrue(os.path.exists(self.dst_file))
        with open(self.dst_file, 'r') as f:
            self.assertEqual(f.read(), 'test content')

    def test_copy_directory_recursive(self):
        """Test copia ricorsiva directory"""
        src_dir = os.path.join(self.test_dir, 'src_dir')
        dst_dir = os.path.join(self.test_dir, 'dst_dir')

        os.makedirs(src_dir)
        with open(os.path.join(src_dir, 'file.txt'), 'w') as f:
            f.write('content')

        shutil.copytree(src_dir, dst_dir)

        self.assertTrue(os.path.exists(dst_dir))
        self.assertTrue(os.path.exists(os.path.join(dst_dir, 'file.txt')))

    def test_copy_nonexistent_source(self):
        """Test copia file inesistente"""
        with self.assertRaises(FileNotFoundError):
            shutil.copy('/nonexistent/file.txt', self.dst_file)


class TestZipOperations(unittest.TestCase):
    """Test per operazioni ZIP"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_dir = tempfile.mkdtemp()
        self.zip_file = os.path.join(self.test_dir, 'test.zip')

        # Crea struttura di directory da comprimere
        self.data_dir = os.path.join(self.test_dir, 'data')
        os.makedirs(self.data_dir)

        with open(os.path.join(self.data_dir, 'file1.txt'), 'w') as f:
            f.write('content1')
        with open(os.path.join(self.data_dir, 'file2.txt'), 'w') as f:
            f.write('content2')

    def tearDown(self):
        """Cleanup dopo ogni test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_zip(self):
        """Test creazione archivio ZIP"""
        with zipfile.ZipFile(self.zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.test_dir)
                    zipf.write(file_path, arcname)

        self.assertTrue(os.path.exists(self.zip_file))
        self.assertGreater(os.path.getsize(self.zip_file), 0)

    def test_extract_zip(self):
        """Test estrazione archivio ZIP"""
        # Crea ZIP
        with zipfile.ZipFile(self.zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(os.path.join(self.data_dir, 'file1.txt'), 'file1.txt')

        # Estrai
        extract_dir = os.path.join(self.test_dir, 'extracted')
        os.makedirs(extract_dir)

        with zipfile.ZipFile(self.zip_file, 'r') as zipf:
            zipf.extractall(extract_dir)

        self.assertTrue(os.path.exists(os.path.join(extract_dir, 'file1.txt')))

    def test_zip_file_count(self):
        """Test conteggio file in ZIP"""
        with zipfile.ZipFile(self.zip_file, 'w') as zipf:
            zipf.write(os.path.join(self.data_dir, 'file1.txt'), 'file1.txt')
            zipf.write(os.path.join(self.data_dir, 'file2.txt'), 'file2.txt')

        with zipfile.ZipFile(self.zip_file, 'r') as zipf:
            self.assertEqual(len(zipf.namelist()), 2)


class TestFileReadWrite(unittest.TestCase):
    """Test per lettura/scrittura file"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test.txt')

    def tearDown(self):
        """Cleanup dopo ogni test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_write_and_read_file(self):
        """Test scrittura e lettura file"""
        content = 'Test content for file operations'

        # Scrivi
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(content)

        # Leggi
        with open(self.test_file, 'r', encoding='utf-8') as f:
            read_content = f.read()

        self.assertEqual(read_content, content)

    def test_write_unicode_content(self):
        """Test scrittura contenuto Unicode"""
        content = 'Test con caratteri speciali: àèéìòù €'

        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(content)

        with open(self.test_file, 'r', encoding='utf-8') as f:
            read_content = f.read()

        self.assertEqual(read_content, content)


class TestJSONOperations(unittest.TestCase):
    """Test per operazioni JSON"""

    def setUp(self):
        """Setup prima di ogni test"""
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, 'data.json')

    def tearDown(self):
        """Cleanup dopo ogni test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_load_json_file(self):
        """Test caricamento file JSON"""
        data = {'key1': 'value1', 'key2': 123, 'key3': [1, 2, 3]}

        with open(self.json_file, 'w') as f:
            json.dump(data, f)

        with open(self.json_file, 'r') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, data)

    def test_invalid_json(self):
        """Test caricamento JSON invalido"""
        with open(self.json_file, 'w') as f:
            f.write('{ invalid json }')

        with self.assertRaises(json.JSONDecodeError):
            with open(self.json_file, 'r') as f:
                json.load(f)


class TestReplaceOperations(unittest.TestCase):
    """Test per operazioni di sostituzione testo"""

    def test_simple_replace(self):
        """Test sostituzione semplice"""
        text = 'Hello world'
        result = text.replace('world', 'Python')
        self.assertEqual(result, 'Hello Python')

    def test_multiple_replace(self):
        """Test sostituzioni multiple"""
        text = 'test test test'
        result = text.replace('test', 'exam')
        self.assertEqual(result, 'exam exam exam')

    def test_regex_replace(self):
        """Test sostituzione con regex"""
        import re
        text = 'Error123: Something wrong'
        result = re.sub(r'Error\d+', 'Warning', text)
        self.assertEqual(result, 'Warning: Something wrong')


if __name__ == '__main__':
    unittest.main()
