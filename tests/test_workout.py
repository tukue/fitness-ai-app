import pytest
from app import User, get_ai_workout

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
            
def test_workout_adaptation():
    """Test workout adaptation based on user profile"""
    advanced_user = User(
        username='advanced',
        email='advanced@test.com',
        age=30,
        weight=75,
        fitness_goal='muscle_gain',
        experience_level='advanced'
    )
    
    workout = get_ai_workout(advanced_user)
    
    # Check if workout is adapted for advanced users
    main_exercises = [ex for ex in workout 
                     if not any(marker in ex['name'] 
                              for marker in ['🔥 Warm-up', '❄️ Cool-down', '💡 Health Tip'])]
    
    for exercise in main_exercises:
        # Advanced users should have more sets
        assert exercise['sets'] >= 3
