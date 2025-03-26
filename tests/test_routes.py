import pytest
from flask_login import current_user
from app import app

def test_home_page(client):
    """Test that home page loads"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Fitness AI' in response.data

def test_register(client, app):
    """Test user registration"""
    with app.app_context():
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass',
            'age': '25',
            'weight': '70',
            'fitness_goal': 'weight_loss',
            'experience_level': 'beginner'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data  # Should redirect to login page

def test_login_logout(client, test_user):
    """Test login and logout functionality"""
    # Test login with correct credentials
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data
    
    # Test that user is logged in
    with client.session_transaction() as session:
        assert '_user_id' in session
    
    # Test logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data
    
    # Test that user is logged out
    with client.session_transaction() as session:
        assert '_user_id' not in session

def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials"""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data

def test_protected_route(client):
    """Test accessing protected route without login"""
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page' in response.data
