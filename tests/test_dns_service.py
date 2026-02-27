"""
Unit Tests for DNS Service

Tests for real and mock DNS service implementations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import socket

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_validator.dns_service import DNSService, MockDNSService, DNSServiceBase


class TestDNSServiceInitialization:
    """Tests for DNSService initialization."""

    def test_init_without_dnspython(self):
        """Test initialization when dnspython is not available."""
        with patch.dict('sys.modules', {'dns': None, 'dns.resolver': None}):
            service = DNSService(timeout=10)
            assert service.timeout == 10
            assert service._use_dnspython is False
            assert service._resolver is None

    def test_init_with_timeout(self):
        """Test initialization with custom timeout."""
        service = DNSService(timeout=30)
        assert service.timeout == 30

    def test_init_default_timeout(self):
        """Test default timeout value."""
        service = DNSService()
        assert service.timeout == 5


class TestDNSServiceWithSocketFallback:
    """Tests for DNSService using socket fallback."""

    def setup_method(self):
        """Set up test fixtures."""
        # Force socket fallback by setting _use_dnspython to False
        self.service = DNSService(timeout=5)
        self.service._use_dnspython = False
        self.service._resolver = None

    def test_check_mx_socket_valid_domain(self):
        """Test MX check using socket for valid domain."""
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [(2, 1, 6, '', ('93.184.216.34', 0))]
            result = self.service._check_mx_socket('example.com')
            assert result is True

    def test_check_mx_socket_invalid_domain(self):
        """Test MX check using socket for invalid domain."""
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.side_effect = socket.gaierror('Domain not found')
            result = self.service._check_mx_socket('nonexistent.invalid')
            assert result is False

    def test_check_mx_socket_timeout(self):
        """Test MX check using socket with timeout."""
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.side_effect = socket.timeout('DNS timeout')
            result = self.service._check_mx_socket('timeout.domain')
            assert result is False

    def test_check_mx_socket_general_exception(self):
        """Test MX check using socket with general exception."""
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.side_effect = Exception('Unexpected error')
            result = self.service._check_mx_socket('error.domain')
            assert result is False

    def test_check_mx_record_fallback(self):
        """Test check_mx_record falls back to socket when dnspython unavailable."""
        with patch.object(self.service, '_check_mx_socket', return_value=True) as mock_socket:
            result = self.service.check_mx_record('test.com')
            assert result is True
            mock_socket.assert_called_once_with('test.com')

    def test_get_mx_records_without_dnspython(self):
        """Test get_mx_records returns empty list without dnspython."""
        result = self.service.get_mx_records('example.com')
        assert result == []


class TestDNSServiceWithDnspython:
    """Tests for DNSService using dnspython."""

    def setup_method(self):
        """Set up test fixtures with mocked resolver."""
        self.service = DNSService(timeout=5)

    def test_check_mx_dnspython_success(self):
        """Test MX check with dnspython success."""
        # Mock the resolver
        mock_resolver = MagicMock()
        mock_answer = [MagicMock()]
        mock_resolver.resolve.return_value = mock_answer
        self.service._resolver = mock_resolver
        self.service._use_dnspython = True

        result = self.service._check_mx_dnspython('gmail.com')
        assert result is True
        mock_resolver.resolve.assert_called_once_with('gmail.com', 'MX')

    def test_check_mx_dnspython_nxdomain(self):
        """Test MX check when domain does not exist."""
        import dns.resolver
        
        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = dns.resolver.NXDOMAIN()
        self.service._resolver = mock_resolver
        self.service._use_dnspython = True

        result = self.service._check_mx_dnspython('nonexistent.invalid')
        assert result is False

    def test_check_mx_dnspython_no_answer(self):
        """Test MX check when no MX record exists."""
        import dns.resolver
        
        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = dns.resolver.NoAnswer()
        self.service._resolver = mock_resolver
        self.service._use_dnspython = True

        result = self.service._check_mx_dnspython('no-mx.com')
        assert result is False

    def test_check_mx_dnspython_no_nameservers(self):
        """Test MX check when no nameservers available."""
        import dns.resolver
        
        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = dns.resolver.NoNameservers()
        self.service._resolver = mock_resolver
        self.service._use_dnspython = True

        result = self.service._check_mx_dnspython('no-ns.com')
        assert result is False

    def test_check_mx_dnspython_timeout(self):
        """Test MX check with DNS timeout."""
        import dns.exception
        
        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = dns.exception.Timeout()
        self.service._resolver = mock_resolver
        self.service._use_dnspython = True

        result = self.service._check_mx_dnspython('timeout.com')
        assert result is False

    def test_check_mx_dnspython_general_exception(self):
        """Test MX check with general exception."""
        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = Exception('Unexpected error')
        self.service._resolver = mock_resolver
        self.service._use_dnspython = True

        result = self.service._check_mx_dnspython('error.com')
        assert result is False

    def test_get_mx_records_success(self):
        """Test getting MX records successfully."""
        # Mock MX record
        mock_rdata1 = MagicMock()
        mock_rdata1.preference = 10
        mock_rdata1.exchange = 'mail1.example.com'

        mock_rdata2 = MagicMock()
        mock_rdata2.preference = 20
        mock_rdata2.exchange = 'mail2.example.com'

        mock_answer = [mock_rdata1, mock_rdata2]

        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = mock_answer
        self.service._resolver = mock_resolver
        self.service._use_dnspython = True

        records = self.service.get_mx_records('example.com')
        assert len(records) == 2
        assert records[0] == (10, 'mail1.example.com')
        assert records[1] == (20, 'mail2.example.com')

    def test_get_mx_records_exception(self):
        """Test getting MX records with exception."""
        mock_resolver = MagicMock()
        mock_resolver.resolve.side_effect = Exception('DNS error')
        self.service._resolver = mock_resolver
        self.service._use_dnspython = True

        records = self.service.get_mx_records('error.com')
        assert records == []

    def test_check_mx_record_with_dnspython(self):
        """Test check_mx_record with dnspython."""
        mock_resolver = MagicMock()
        mock_answer = [MagicMock()]
        mock_resolver.resolve.return_value = mock_answer
        self.service._resolver = mock_resolver
        self.service._use_dnspython = True

        result = self.service.check_mx_record('gmail.com')
        assert result is True


class TestMockDNSServiceDetailed:
    """Detailed tests for MockDNSService."""

    def test_inheritance(self):
        """Test that MockDNSService inherits from DNSServiceBase."""
        service = MockDNSService()
        assert isinstance(service, DNSServiceBase)

    def test_multiple_domains(self):
        """Test configuring multiple domains."""
        service = MockDNSService(responses={
            'gmail.com': True,
            'yahoo.com': True,
            'invalid.fake': False,
        })

        assert service.check_mx_record('gmail.com') is True
        assert service.check_mx_record('yahoo.com') is True
        assert service.check_mx_record('invalid.fake') is False
        assert service.check_mx_record('unknown.com') is False  # Default False

    def test_dynamic_response_changes(self):
        """Test changing responses dynamically."""
        service = MockDNSService()
        
        service.set_response('test.com', True)
        assert service.check_mx_record('test.com') is True
        
        service.set_response('test.com', False)
        assert service.check_mx_record('test.com') is False

    def test_get_mx_records_returns_sorted(self):
        """Test that get_mx_records returns sorted by priority."""
        service = MockDNSService()
        service.set_response('test.com', True)
        
        records = service.get_mx_records('test.com')
        assert len(records) == 1
        # Check that it contains the domain
        assert 'test.com' in records[0][1]

    def test_get_mx_records_for_false_domain(self):
        """Test get_mx_records for domain without MX."""
        service = MockDNSService()
        service.set_response('no-mx.com', False)
        
        records = service.get_mx_records('no-mx.com')
        assert records == []

    def test_call_history_with_get_mx_records(self):
        """Test that get_mx_records is tracked in history."""
        service = MockDNSService()
        service.check_mx_record('domain1.com')
        service.get_mx_records('domain2.com')
        
        assert len(service.call_history) == 2
        assert service.call_history[0] == ('check_mx_record', 'domain1.com')
        assert service.call_history[1] == ('get_mx_records', 'domain2.com')


class TestDNSServiceBase:
    """Tests for DNSServiceBase abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that DNSServiceBase cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DNSServiceBase()

    def test_abstract_methods(self):
        """Test that subclass must implement abstract methods."""
        class IncompleteService(DNSServiceBase):
            pass

        with pytest.raises(TypeError):
            IncompleteService()

    def test_complete_implementation(self):
        """Test that complete implementation works."""
        class CompleteService(DNSServiceBase):
            def check_mx_record(self, domain):
                return True
            
            def get_mx_records(self, domain):
                return [(10, 'mail.test.com')]

        service = CompleteService()
        assert service.check_mx_record('test.com') is True
        assert service.get_mx_records('test.com') == [(10, 'mail.test.com')]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
