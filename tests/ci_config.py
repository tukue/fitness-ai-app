import os

# CI-specific test configuration
CI_CONFIG = {
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SECRET_KEY': 'github-actions-test-key',
    'WTF_CSRF_ENABLED': False,
    'LOGIN_DISABLED': False
}

# Override config with environment variables if present
if 'DATABASE_URL' in os.environ:
    CI_CONFIG['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
if 'SECRET_KEY' in os.environ:
    CI_CONFIG['SECRET_KEY'] = os.environ['SECRET_KEY']
