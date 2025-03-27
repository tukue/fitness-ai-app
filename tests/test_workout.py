import pytest
from app import User, get_ai_workout
from unittest.mock import patch, Mock

def test_workout_generation():
    """Test workout generation"""
    test_user = User(
        username='workouttest',
        email='workout@test.com',
        age=25,
        weight=70,
        fitness_goal='weight_loss',
        experience_level='beginner'
    )
    
    workout = get_ai_workout(test_user)
    
    # Test workout structure
    assert isinstance(workout, list)
    assert len(workout) > 0
    
    # Test workout content
    for exercise in workout:
        assert 'name' in exercise
        assert 'sets' in exercise
        assert 'reps' in exercise
        
        # Check exercise categories
        if '🔥 Warm-up' in exercise['name']:
            assert exercise['sets'] <= 2  # Warm-up exercises should have fewer sets
        elif '❄️ Cool-down' in exercise['name']:
            assert exercise['sets'] == 1  # Cool-down exercises should have 1 set
        elif '💡 Health Tip' in exercise['name']:
            assert exercise['sets'] == 0  # Tips don't have sets/reps
            assert exercise['reps'] == 0
        else:
            # Main workout exercises
            if test_user.experience_level == 'beginner':
                assert exercise['sets'] <= 3  # Beginners should have fewer sets
            
def test_workout_adaptation(client, app, test_user):
    """Test workout adaptation logic."""
    with app.app_context():
        # Log in the test user
        client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass'
        })

        # Mock the AI pipeline
        with patch('transformers.pipeline') as mock_pipeline:
            mock_pipeline.return_value = Mock()
            mock_pipeline.return_value.return_value = [{
                'generated_text': '1. Push-Ups: 3 sets of 10 reps\n2. Squats: 3 sets of 15 reps'
            }]

            # Call the workout adaptation endpoint with valid input
            response = client.post('/adapt_workout', json={
                'workout': {
                    'exercises': [
                        {'name': 'Push-Ups', 'sets': 2, 'reps': 10},
                        {'name': 'Squats', 'sets': 2, 'reps': 15}
                    ]
                }
            }, follow_redirects=True)

            assert response.status_code == 200
            data = response.get_json()
            assert data is not None, "Response data is None"
            assert 'workout' in data, "Response does not contain 'workout'"
            assert 'exercises' in data['workout'], "Response does not contain 'exercises' in 'workout'"

            # Validate the adapted workout
            for exercise in data['workout']['exercises']:
                assert exercise['sets'] >= 1  # Ensure sets are valid
                assert exercise['reps'] >= 1  # Ensure reps are valid