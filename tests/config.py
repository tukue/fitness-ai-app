import os
import secrets

# Test-specific secret key - different from production
TEST_SECRET_KEY = 'test-only-not-for-production-' + secrets.token_hex(16)

# Test configuration
TEST_CONFIG = {
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  # Use in-memory database for testing
    'SECRET_KEY': TEST_SECRET_KEY,
    'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
    'LOGIN_DISABLED': False     # Enable login functionality in tests
}
