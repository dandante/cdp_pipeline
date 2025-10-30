#!/usr/bin/env python3

"""
Test runner for cdp_pipeline library.

Discovers and runs all unit tests in the project.
"""

import sys
import unittest


def run_all_tests(verbosity=2):
    """
    Discover and run all tests.

    Args:
        verbosity: Level of output detail (0=quiet, 1=normal, 2=verbose)

    Returns:
        True if all tests passed, False otherwise
    """
    # Discover all test files matching pattern test*.py
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='.', pattern='test*.py')

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


def run_specific_test(test_module, verbosity=2):
    """
    Run tests from a specific module.

    Args:
        test_module: Name of test module (e.g., 'test_basic')
        verbosity: Level of output detail

    Returns:
        True if all tests passed, False otherwise
    """
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_module)

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result.wasSuccessful()


def main():
    """Main entry point for test runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run cdp_pipeline unit tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py test_basic         # Run specific test module
  python run_tests.py -v                 # Run all tests with verbose output
  python run_tests.py -q                 # Run all tests quietly
        """
    )

    parser.add_argument(
        'test_module',
        nargs='?',
        help='Specific test module to run (e.g., test_basic, test_breakpoint)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_const',
        const=2,
        default=2,
        dest='verbosity',
        help='Verbose output (default)'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_const',
        const=0,
        dest='verbosity',
        help='Quiet output (minimal)'
    )

    args = parser.parse_args()

    # Print header
    print("=" * 70)
    print("CDP Pipeline Test Suite")
    print("=" * 70)
    print()

    # Run tests
    if args.test_module:
        print(f"Running tests from: {args.test_module}")
        print("-" * 70)
        success = run_specific_test(args.test_module, args.verbosity)
    else:
        print("Running all tests...")
        print("-" * 70)
        success = run_all_tests(args.verbosity)

    print()
    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
