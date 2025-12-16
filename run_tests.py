#!/usr/bin/env python3
"""
Test Runner per Open-Automator
Esegue test con opzioni configurabili
"""

import sys
import argparse
import subprocess
import os


def run_tests(args):
    """Esegue i test con le opzioni specificate"""

    cmd = ['pytest', 'tests/']

    # Verbosity
    if args.verbose:
        cmd.append('-vv')
    elif args.quiet:
        cmd.append('-q')
    else:
        cmd.append('-v')

    # Show output
    if args.show_output:
        cmd.append('-s')

    # Coverage
    if args.coverage:
        cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])

    # Markers
    if args.marker:
        cmd.extend(['-m', args.marker])

    # Specific test
    if args.test:
        cmd = ['pytest', f'tests/{args.test}', '-v']

    # Fail fast
    if args.failfast:
        cmd.append('-x')

    # Parallel
    if args.parallel:
        cmd.extend(['-n', 'auto'])

    # Durations
    if args.durations:
        cmd.extend(['--durations', str(args.durations)])

    print(f"Eseguendo: {' '.join(cmd)}")
    print()

    # Run pytest
    result = subprocess.run(cmd)

    if args.coverage and result.returncode == 0:
        print()
        print("Coverage report generato in: htmlcov/index.html")

        # Apri browser se richiesto
        if args.open_coverage:
            import webbrowser
            coverage_path = os.path.abspath('htmlcov/index.html')
            webbrowser.open(f'file://{coverage_path}')

    return result.returncode


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test Runner per Open-Automator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  %(prog)s                        # Esegue tutti i test
  %(prog)s --coverage             # Con coverage report
  %(prog)s --test test_logger_config.py  # Test specifico
  %(prog)s --marker unit          # Solo unit test
  %(prog)s --failfast -vv         # Fail fast con verbose output
  %(prog)s --parallel             # Esecuzione parallela
        """
    )

    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Output verbose')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Output minimale')
    parser.add_argument('-s', '--show-output', action='store_true',
                       help='Mostra print statements')
    parser.add_argument('-c', '--coverage', action='store_true',
                       help='Genera coverage report')
    parser.add_argument('-o', '--open-coverage', action='store_true',
                       help='Apri coverage report in browser')
    parser.add_argument('-m', '--marker', type=str,
                       help='Esegui solo test con marker specifico')
    parser.add_argument('-t', '--test', type=str,
                       help='Esegui test specifico (es: test_logger_config.py)')
    parser.add_argument('-x', '--failfast', action='store_true',
                       help='Ferma al primo errore')
    parser.add_argument('-p', '--parallel', action='store_true',
                       help='Esecuzione parallela (richiede pytest-xdist)')
    parser.add_argument('-d', '--durations', type=int, metavar='N',
                       help='Mostra N test più lenti')

    args = parser.parse_args()

    # Verifica che directory tests esista
    if not os.path.exists('tests'):
        print("ERRORE: Directory 'tests/' non trovata")
        print("Eseguire dalla root del progetto")
        return 1

    return run_tests(args)


if __name__ == '__main__':
    sys.exit(main())
