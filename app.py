"""
Flask Application for Email Validation API

Provides REST API endpoints for email validation.
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from email_validator import EmailValidator, DNSService

# Create Flask application
app = Flask(__name__)
CORS(app)

# Configuration
CHECK_MX = os.environ.get('CHECK_MX', 'false').lower() == 'true'

# Initialize validator
dns_service = None
if CHECK_MX:
    dns_service = DNSService(timeout=5)

validator = EmailValidator(check_mx=CHECK_MX, dns_service=dns_service)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'email-validator',
        'check_mx': CHECK_MX
    }), 200


@app.route('/validate', methods=['POST'])
def validate_email():
    """
    Validate an email address.

    Request Body:
        {
            "email": "user@example.com"
        }

    Returns:
        JSON response with validation result:
        {
            "is_valid": true,
            "email": "user@example.com",
            "errors": [],
            "warnings": [],
            "mx_valid": null
        }
    """
    # Check content type
    if not request.is_json:
        return jsonify({
            'error': 'Content-Type must be application/json'
        }), 415

    # Get request data
    data = request.get_json()

    if data is None:
        return jsonify({
            'error': 'Invalid JSON body'
        }), 400

    # Get email from request
    email = data.get('email')

    if email is None:
        return jsonify({
            'error': 'Missing required field: email'
        }), 400

    # Validate email
    result = validator.validate(email)

    return jsonify(result.to_dict()), 200


@app.route('/validate/batch', methods=['POST'])
def validate_batch():
    """
    Validate multiple email addresses.

    Request Body:
        {
            "emails": ["user1@example.com", "user2@example.com"]
        }

    Returns:
        JSON response with validation results:
        {
            "results": [...],
            "total": 2,
            "valid_count": 2,
            "invalid_count": 0
        }
    """
    # Check content type
    if not request.is_json:
        return jsonify({
            'error': 'Content-Type must be application/json'
        }), 415

    # Get request data
    data = request.get_json()

    if data is None:
        return jsonify({
            'error': 'Invalid JSON body'
        }), 400

    # Get emails from request
    emails = data.get('emails')

    if emails is None:
        return jsonify({
            'error': 'Missing required field: emails'
        }), 400

    if not isinstance(emails, list):
        return jsonify({
            'error': 'emails must be an array'
        }), 400

    if len(emails) == 0:
        return jsonify({
            'error': 'emails array cannot be empty'
        }), 400

    # Validate emails
    results = validator.validate_batch(emails)

    # Count valid and invalid
    valid_count = sum(1 for r in results if r.is_valid)
    invalid_count = len(results) - valid_count

    return jsonify({
        'results': [r.to_dict() for r in results],
        'total': len(results),
        'valid_count': valid_count,
        'invalid_count': invalid_count
    }), 200


@app.route('/quick-check', methods=['GET'])
def quick_check():
    """
    Quick email validation check via GET request.

    Query Parameters:
        email: Email address to validate

    Returns:
        JSON response with simple valid/invalid status.
    """
    email = request.args.get('email')

    if email is None:
        return jsonify({
            'error': 'Missing required query parameter: email'
        }), 400

    # Simple validation
    is_valid = validator.is_valid(email)

    return jsonify({
        'email': email,
        'is_valid': is_valid
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'error': 'Method not allowed'
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    print(f"Starting Email Validator API on port {port}")
    print(f"MX Check enabled: {CHECK_MX}")

    app.run(host='0.0.0.0', port=port, debug=debug)
