"""
Configurazione Test Suite per Open-Automator
"""

import unittest
import sys
import os

# Aggiungi directory del progetto al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def run_all_tests():
    """Esegue tutti i test della suite"""
    # Discover tutti i test
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Esegui i test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Ritorna exit code appropriato
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
