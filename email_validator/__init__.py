"""
Email Validator Package

Provides email validation with format checking and DNS MX record verification.
"""

from .validator import EmailValidator
from .dns_service import DNSService

__all__ = ['EmailValidator', 'DNSService']
__version__ = '1.0.0'
