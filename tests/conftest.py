import pytest
from app import app as flask_app, db, User
import os
from tests.config import TEST_CONFIG

@pytest.fixture(scope='session')
def app():
    # Update app config with test settings
    flask_app.config.update(TEST_CONFIG)
    
    # Create all tables in the test database
    with flask_app.app_context():
        db.create_all()
    
    yield flask_app
    
    # Clean up after tests
    with flask_app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            age=25,
            weight=70,
            fitness_goal='weight_loss',
            experience_level='intermediate'
        )
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        yield user
        
        # Cleanup
        db.session.delete(user)
        db.session.commit()
