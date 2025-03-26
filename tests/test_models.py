import pytest
from app import User, db

def test_new_user(app):
    """Test creating a new user"""
    with app.app_context():
        user = User(
            username='testuser2',
            email='test2@example.com',
            age=30,
            weight=75,
            fitness_goal='muscle_gain',
            experience_level='beginner'
        )
        assert user.username == 'testuser2'
        assert user.email == 'test2@example.com'
        assert user.age == 30
        assert user.weight == 75
        assert user.fitness_goal == 'muscle_gain'
        assert user.experience_level == 'beginner'

def test_password_hashing(app):
    """Test password hashing"""
    with app.app_context():
        user = User(username='test', email='test@test.com')
        user.set_password('cat')
        assert user.check_password('cat')
        assert not user.check_password('dog')
        assert user.password_hash != 'cat'  # Password should be hashed

def test_user_creation_and_query(app):
    """Test user creation and database query"""
    with app.app_context():
        user = User(
            username='dbtest',
            email='dbtest@example.com',
            age=25,
            weight=70,
            fitness_goal='weight_loss',
            experience_level='intermediate'
        )
        user.set_password('password123')
        
        # Add user to database
        db.session.add(user)
        db.session.commit()
        
        # Query user from database
        queried_user = User.query.filter_by(username='dbtest').first()
        assert queried_user is not None
        assert queried_user.email == 'dbtest@example.com'
        assert queried_user.check_password('password123')
        
        # Clean up
        db.session.delete(user)
        db.session.commit()
