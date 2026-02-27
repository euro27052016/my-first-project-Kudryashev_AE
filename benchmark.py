#!/usr/bin/env python3
"""
Performance Benchmark for Email Validator

Simple benchmark to measure RPS without external dependencies.
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_validator import EmailValidator

# Test emails
VALID_EMAILS = [
    "user@example.com",
    "john.doe@company.org",
    "alice123@gmail.com",
    "bob_smith@yahoo.com",
    "charlie.brown@outlook.com",
]

INVALID_EMAILS = [
    "plainaddress",
    "@missing-local.com",
    "user@",
    "user@@domain.com",
    "user@.com",
]

ALL_EMAILS = VALID_EMAILS + INVALID_EMAILS


def benchmark(validator, emails, iterations=10000):
    """Run benchmark and return statistics."""
    start_time = time.perf_counter()
    
    for _ in range(iterations):
        for email in emails:
            validator.validate(email)
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    total_requests = iterations * len(emails)
    rps = total_requests / total_time
    
    return {
        'total_time': total_time,
        'total_requests': total_requests,
        'rps': rps,
        'avg_time_ms': (total_time / total_requests) * 1000
    }


def main():
    print("=" * 60)
    print("Email Validator Performance Benchmark")
    print("=" * 60)
    
    validator = EmailValidator(check_mx=False)
    
    # Warmup
    print("\n[Warmup] Running 1000 iterations...")
    benchmark(validator, ALL_EMAILS, iterations=1000)
    
    # Benchmark 1: Valid emails only
    print("\n[Benchmark 1] Valid emails only (10,000 iterations)...")
    result = benchmark(validator, VALID_EMAILS, iterations=10000)
    print(f"  Total time: {result['total_time']:.3f}s")
    print(f"  Total requests: {result['total_requests']}")
    print(f"  RPS: {result['rps']:,.0f} requests/second")
    print(f"  Avg time: {result['avg_time_ms']:.4f}ms")
    
    # Benchmark 2: Invalid emails only
    print("\n[Benchmark 2] Invalid emails only (10,000 iterations)...")
    result = benchmark(validator, INVALID_EMAILS, iterations=10000)
    print(f"  Total time: {result['total_time']:.3f}s")
    print(f"  Total requests: {result['total_requests']}")
    print(f"  RPS: {result['rps']:,.0f} requests/second")
    print(f"  Avg time: {result['avg_time_ms']:.4f}ms")
    
    # Benchmark 3: Mixed emails
    print("\n[Benchmark 3] Mixed emails (10,000 iterations)...")
    result = benchmark(validator, ALL_EMAILS, iterations=10000)
    print(f"  Total time: {result['total_time']:.3f}s")
    print(f"  Total requests: {result['total_requests']}")
    print(f"  RPS: {result['rps']:,.0f} requests/second")
    print(f"  Avg time: {result['avg_time_ms']:.4f}ms")
    
    # Benchmark 4: Batch validation
    print("\n[Benchmark 4] Batch validation (100 emails per batch, 1000 iterations)...")
    start = time.perf_counter()
    for _ in range(1000):
        validator.validate_batch(ALL_EMAILS * 10)  # 100 emails
    end = time.perf_counter()
    total_time = end - start
    total_requests = 1000 * 100
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Total requests: {total_requests}")
    print(f"  RPS: {total_requests / total_time:,.0f} requests/second")
    print(f"  Avg time per email: {(total_time / total_requests) * 1000:.4f}ms")
    
    # Benchmark 5: Quick validation (is_valid method)
    print("\n[Benchmark 5] Quick validation with is_valid() (50,000 iterations)...")
    start = time.perf_counter()
    for _ in range(50000):
        for email in ALL_EMAILS:
            validator.is_valid(email)
    end = time.perf_counter()
    total_time = end - start
    total_requests = 50000 * len(ALL_EMAILS)
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Total requests: {total_requests}")
    print(f"  RPS: {total_requests / total_time:,.0f} requests/second")
    print(f"  Avg time: {(total_time / total_requests) * 1000:.4f}ms")
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Expected RPS for Flask API: ~{result['rps'] * 0.1:,.0f} - {result['rps'] * 0.3:,.0f}")
    print("(Accounting for HTTP overhead and JSON serialization)")
    print("=" * 60)


if __name__ == "__main__":
    main()
