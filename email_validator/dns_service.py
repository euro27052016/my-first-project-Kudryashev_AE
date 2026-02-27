"""
DNS Service Module

Provides DNS lookup functionality for email validation.
"""

import socket
from typing import Optional, List
from abc import ABC, abstractmethod


class DNSServiceBase(ABC):
    """Abstract base class for DNS services."""

    @abstractmethod
    def check_mx_record(self, domain: str) -> bool:
        """
        Check if MX record exists for a domain.

        Args:
            domain: The domain to check

        Returns:
            True if MX record exists, False otherwise
        """
        pass

    @abstractmethod
    def get_mx_records(self, domain: str) -> List[tuple]:
        """
        Get all MX records for a domain.

        Args:
            domain: The domain to check

        Returns:
            List of (priority, server) tuples
        """
        pass


class DNSService(DNSServiceBase):
    """
    Real DNS service that performs actual DNS lookups.

    Uses the dns.resolver library for DNS queries.
    Falls back to socket-based resolution if dns is not available.
    """

    def __init__(self, timeout: int = 5):
        """
        Initialize the DNS service.

        Args:
            timeout: DNS query timeout in seconds
        """
        self.timeout = timeout
        self._use_dnspython = False

        try:
            import dns.resolver
            self._resolver = dns.resolver.Resolver()
            self._resolver.timeout = timeout
            self._resolver.lifetime = timeout
            self._use_dnspython = True
        except ImportError:
            self._resolver = None

    def check_mx_record(self, domain: str) -> bool:
        """
        Check if MX record exists for a domain.

        Args:
            domain: The domain to check

        Returns:
            True if MX record exists, False otherwise
        """
        if self._use_dnspython:
            return self._check_mx_dnspython(domain)
        else:
            return self._check_mx_socket(domain)

    def _check_mx_dnspython(self, domain: str) -> bool:
        """Check MX record using dnspython library."""
        try:
            import dns.resolver
            import dns.exception

            answers = self._resolver.resolve(domain, 'MX')
            return len(answers) > 0
        except dns.resolver.NXDOMAIN:
            # Domain does not exist
            return False
        except dns.resolver.NoAnswer:
            # No MX record for this domain
            return False
        except dns.resolver.NoNameservers:
            # No nameservers available
            return False
        except dns.exception.Timeout:
            # DNS query timed out
            return False
        except Exception:
            # Any other error
            return False

    def _check_mx_socket(self, domain: str) -> bool:
        """
        Fallback MX check using socket and basic DNS queries.

        This is a simplified check that may not work for all cases.
        """
        try:
            # Try to resolve the domain as a fallback
            # If the domain resolves, it might accept mail
            socket.setdefaulttimeout(self.timeout)
            socket.getaddrinfo(domain, None)
            return True
        except socket.gaierror:
            return False
        except socket.timeout:
            return False
        except Exception:
            return False

    def get_mx_records(self, domain: str) -> List[tuple]:
        """
        Get all MX records for a domain.

        Args:
            domain: The domain to check

        Returns:
            List of (priority, server) tuples
        """
        if not self._use_dnspython:
            return []

        try:
            import dns.resolver
            import dns.exception

            answers = self._resolver.resolve(domain, 'MX')
            records = []
            for rdata in answers:
                records.append((rdata.preference, str(rdata.exchange)))
            return sorted(records, key=lambda x: x[0])
        except Exception:
            return []


class MockDNSService(DNSServiceBase):
    """
    Mock DNS service for testing purposes.

    Allows configuring predefined responses for specific domains.
    """

    def __init__(self, responses: Optional[dict] = None):
        """
        Initialize the mock DNS service.

        Args:
            responses: Dictionary mapping domains to their MX record status
                      e.g., {'gmail.com': True, 'invalid.fake': False}
        """
        self.responses = responses or {}
        self.call_history = []

    def set_response(self, domain: str, has_mx: bool):
        """
        Set the response for a specific domain.

        Args:
            domain: The domain to configure
            has_mx: Whether the domain has an MX record
        """
        self.responses[domain] = has_mx

    def check_mx_record(self, domain: str) -> bool:
        """
        Check if MX record exists for a domain (mocked).

        Args:
            domain: The domain to check

        Returns:
            Configured response or False if not configured
        """
        self.call_history.append(('check_mx_record', domain))
        return self.responses.get(domain, False)

    def get_mx_records(self, domain: str) -> List[tuple]:
        """
        Get all MX records for a domain (mocked).

        Args:
            domain: The domain to check

        Returns:
            Mock MX records if domain is configured with True
        """
        self.call_history.append(('get_mx_records', domain))
        if self.responses.get(domain, False):
            return [(10, f'mail.{domain}')]
        return []

    def reset_history(self):
        """Reset the call history."""
        self.call_history = []
