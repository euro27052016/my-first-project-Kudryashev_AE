"""
Email Validator Module

Contains the EmailValidator class for validating email addresses.
"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """
    Represents the result of an email validation.

    Attributes:
        is_valid: Whether the email is valid
        email: The email address that was validated
        errors: List of validation errors
        warnings: List of validation warnings
        mx_valid: Whether MX record exists (None if not checked)
    """
    is_valid: bool
    email: str
    errors: list
    warnings: list
    mx_valid: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'is_valid': self.is_valid,
            'email': self.email,
            'errors': self.errors,
            'warnings': self.warnings,
            'mx_valid': self.mx_valid
        }


class EmailValidator:
    """
    A comprehensive email validator that checks format and optionally DNS records.

    This validator performs multiple checks:
    - Basic format validation using regex
    - Length validation for local and domain parts
    - Optional MX record verification via DNS lookup

    Example:
        >>> validator = EmailValidator()
        >>> result = validator.validate('user@example.com')
        >>> print(result.is_valid)
        True
    """

    # RFC 5322 compliant email regex pattern
    # This pattern handles most common email formats while being reasonably strict
    # Local part cannot start or end with a dot, and cannot have consecutive dots
    # Also supports quoted local parts
    EMAIL_REGEX = re.compile(
        r"^(?P<local>"
        r'"(?:[^"\\]|\\.)*"'  # Quoted string
        r"|"
        r"[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"  # Unquoted
        r")"
        r"@"
        r"(?P<domain>(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"[a-zA-Z]{2,})$"
    )

    # Maximum lengths according to RFC 5321
    MAX_EMAIL_LENGTH = 254
    MAX_LOCAL_LENGTH = 64
    MAX_DOMAIN_LENGTH = 255

    def __init__(self, check_mx: bool = False, dns_service=None):
        """
        Initialize the EmailValidator.

        Args:
            check_mx: Whether to check MX records during validation
            dns_service: Optional DNS service for MX record checking
        """
        self.check_mx = check_mx
        self.dns_service = dns_service

    def _validate_format(self, email: str) -> tuple[bool, list, list]:
        """
        Validate the format of an email address using regex.

        Args:
            email: The email address to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Check if email is empty
        if not email:
            errors.append("Email address is empty")
            return False, errors, warnings

        # Check if email is a string
        if not isinstance(email, str):
            errors.append(f"Email must be a string, got {type(email).__name__}")
            return False, errors, warnings

        # Check total length
        if len(email) > self.MAX_EMAIL_LENGTH:
            errors.append(f"Email exceeds maximum length of {self.MAX_EMAIL_LENGTH} characters")

        # Check for leading/trailing whitespace
        stripped = email.strip()
        if stripped != email:
            warnings.append("Email contains leading or trailing whitespace")
            email = stripped

        # Check for consecutive dots
        if '..' in email:
            errors.append("Email contains consecutive dots")

        # Check for spaces within email
        if ' ' in email:
            errors.append("Email contains spaces")

        # Check for double @ symbols
        if email.count('@') > 1:
            errors.append("Email contains multiple '@' symbols")

        # Check for domain starting with dot
        if '@.' in email:
            errors.append("Domain cannot start with a dot")

        # Match against regex pattern
        match = self.EMAIL_REGEX.match(email)

        if not match:
            # Provide more specific error messages
            if '@' not in email:
                errors.append("Email is missing '@' symbol")
            elif email.count('@') > 1:
                # Already handled above
                pass
            else:
                parts = email.rsplit('@', 1)
                if len(parts) == 2:
                    local, domain = parts

                    # Check local part
                    if not local:
                        errors.append("Local part (before @) is empty")
                    elif len(local) > self.MAX_LOCAL_LENGTH:
                        errors.append(f"Local part exceeds maximum length of {self.MAX_LOCAL_LENGTH} characters")
                    elif local.startswith('.'):
                        errors.append("Local part starts with a dot")
                    elif local.endswith('.'):
                        errors.append("Local part ends with a dot")

                    # Check domain part
                    if not domain:
                        errors.append("Domain part (after @) is empty")
                    elif len(domain) > self.MAX_DOMAIN_LENGTH:
                        errors.append(f"Domain exceeds maximum length of {self.MAX_DOMAIN_LENGTH} characters")
                    elif not re.match(r'.+\.[a-zA-Z]{2,}$', domain):
                        if '.' not in domain:
                            errors.append("Domain is missing TLD (top-level domain)")
                        else:
                            errors.append("Domain has invalid format")
            return False, errors, warnings

        # Additional validation for matched email
        local = match.group('local')
        domain = match.group('domain')

        # Check local part length
        if len(local) > self.MAX_LOCAL_LENGTH:
            errors.append(f"Local part exceeds maximum length of {self.MAX_LOCAL_LENGTH} characters")

        # Check for quoted strings in local part
        if local.startswith('"') and local.endswith('"'):
            warnings.append("Quoted local part detected - may not be supported by all mail servers")

        # Check for plus addressing (subaddressing)
        if '+' in local:
            warnings.append("Plus addressing detected - ensure your system supports this")

        return len(errors) == 0, errors, warnings

    def _check_mx_record(self, email: str) -> tuple[Optional[bool], list]:
        """
        Check if MX record exists for the email's domain.

        Args:
            email: The email address to check

        Returns:
            Tuple of (mx_valid, errors)
        """
        errors = []

        if not self.dns_service:
            errors.append("DNS service not configured for MX record checking")
            return None, errors

        try:
            # Extract domain from email
            domain = email.rsplit('@', 1)[-1]
            mx_valid = self.dns_service.check_mx_record(domain)
            return mx_valid, errors
        except Exception as e:
            errors.append(f"DNS lookup failed: {str(e)}")
            return None, errors

    def validate(self, email: str) -> ValidationResult:
        """
        Validate an email address.

        Performs format validation and optionally MX record checking.

        Args:
            email: The email address to validate

        Returns:
            ValidationResult object with validation details
        """
        # First, validate the format
        format_valid, errors, warnings = self._validate_format(email)

        mx_valid = None

        # If format is valid and MX check is enabled, check MX records
        if format_valid and self.check_mx:
            mx_valid, mx_errors = self._check_mx_record(email)
            errors.extend(mx_errors)

            if mx_valid is False:
                # MX record not found is a warning, not an error
                # because the email might still be deliverable
                warnings.append("No MX record found for domain")

        # Determine overall validity
        is_valid = format_valid and (mx_valid is None or mx_valid is True)

        return ValidationResult(
            is_valid=is_valid,
            email=email,
            errors=errors,
            warnings=warnings,
            mx_valid=mx_valid
        )

    def validate_batch(self, emails: list) -> list:
        """
        Validate multiple email addresses.

        Args:
            emails: List of email addresses to validate

        Returns:
            List of ValidationResult objects
        """
        return [self.validate(email) for email in emails]

    def is_valid(self, email: str) -> bool:
        """
        Quick check if email is valid.

        Args:
            email: The email address to validate

        Returns:
            True if email is valid, False otherwise
        """
        return self.validate(email).is_valid
