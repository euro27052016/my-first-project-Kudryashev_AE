#!/usr/bin/env python3
"""
Test Runner Script

Runs all tests with coverage reporting.
"""

import subprocess
import sys
import os

def run_tests():
    """Run tests with coverage."""
    
    # Change to project directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("=" * 60)
    print("Running Email Validator Tests with Coverage")
    print("=" * 60)
    
    # Install dependencies if needed
    print("\n[1/4] Checking dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", 
             "pytest", "pytest-cov", "coverage"],
            check=True
        )
        print("✓ Dependencies ready")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return 1
    
    # Run tests with coverage
    print("\n[2/4] Running tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         "tests/", 
         "-v", 
         "--cov=email_validator",
         "--cov-report=term-missing",
         "--cov-report=html",
         "--cov-fail-under=95",
         "-x"],
        cwd=script_dir
    )
    
    # Generate coverage report
    print("\n[3/4] Generating coverage report...")
    if result.returncode == 0:
        print("✓ All tests passed!")
        print("✓ Coverage requirement met (>95%)")
    else:
        # Check if it was a coverage failure
        coverage_result = subprocess.run(
            [sys.executable, "-m", "coverage", "report"],
            cwd=script_dir,
            capture_output=True,
            text=True
        )
        print(coverage_result.stdout)
    
    # Print summary
    print("\n[4/4] Test Summary")
    print("-" * 40)
    
    # Show detailed coverage
    coverage_result = subprocess.run(
        [sys.executable, "-m", "coverage", "report", "--precision=2"],
        cwd=script_dir,
        capture_output=True,
        text=True
    )
    print(coverage_result.stdout)
    
    print("\n" + "=" * 60)
    print("Coverage HTML report generated in: htmlcov/index.html")
    print("=" * 60)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
