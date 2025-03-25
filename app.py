from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import json
from datetime import datetime
from transformers import pipeline

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer)
    weight = db.Column(db.Float)
    fitness_goal = db.Column(db.String(50))
    experience_level = db.Column(db.String(50))
    workouts = db.relationship('Workout', backref='user', lazy=True)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    exercises = db.relationship('Exercise', backref='workout', lazy=True)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    weight = db.Column(db.Float)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Exercise database organized by categories
EXERCISE_DATABASE = {
    'cardio': [
        {'name': 'Jumping Jacks', 'sets': 3, 'reps': 20},
        {'name': 'High Knees', 'sets': 3, 'reps': 30},
        {'name': 'Mountain Climbers', 'sets': 3, 'reps': 20},
        {'name': 'Burpees', 'sets': 3, 'reps': 10},
        {'name': 'Jump Rope', 'sets': 3, 'reps': 50}
    ],
    'bodyweight': [
        {'name': 'Push-ups', 'sets': 3, 'reps': 12},
        {'name': 'Squats', 'sets': 3, 'reps': 15},
        {'name': 'Lunges', 'sets': 3, 'reps': 12},
        {'name': 'Plank Hold', 'sets': 3, 'reps': 30},
        {'name': 'Mountain Climbers', 'sets': 3, 'reps': 20}
    ],
    'strength': [
        {'name': 'Dumbbell Rows', 'sets': 3, 'reps': 12},
        {'name': 'Dumbbell Press', 'sets': 3, 'reps': 10},
        {'name': 'Goblet Squats', 'sets': 3, 'reps': 12},
        {'name': 'Shoulder Press', 'sets': 3, 'reps': 10},
        {'name': 'Bicep Curls', 'sets': 3, 'reps': 12}
    ],
    'core': [
        {'name': 'Crunches', 'sets': 3, 'reps': 20},
        {'name': 'Russian Twists', 'sets': 3, 'reps': 20},
        {'name': 'Leg Raises', 'sets': 3, 'reps': 15},
        {'name': 'Plank', 'sets': 3, 'reps': 30},
        {'name': 'Side Planks', 'sets': 3, 'reps': 20}
    ],
    'warm_up': [
        {'name': 'Arm Circles', 'sets': 2, 'reps': 10},
        {'name': 'Leg Swings', 'sets': 2, 'reps': 10},
        {'name': 'Hip Rotations', 'sets': 2, 'reps': 10},
        {'name': 'Light Jogging', 'sets': 1, 'reps': 2},
        {'name': 'Jumping Jacks', 'sets': 2, 'reps': 20}
    ],
    'cool_down': [
        {'name': 'Standing Forward Bend', 'sets': 1, 'reps': 30},
        {'name': 'Quad Stretch', 'sets': 1, 'reps': 30},
        {'name': 'Child\'s Pose', 'sets': 1, 'reps': 30},
        {'name': 'Cat-Cow Stretch', 'sets': 1, 'reps': 10},
        {'name': 'Deep Breathing', 'sets': 1, 'reps': 10}
    ]
}

def get_ai_workout(user):
    # Initialize the text generation pipeline
    generator = pipeline('text-generation', model='gpt2-medium')
    
    # Select exercises based on user's profile
    workout_exercises = []
    
    # Add warm-up exercises
    warm_up = EXERCISE_DATABASE['warm_up'][:3]  # Select first 3 warm-up exercises
    for exercise in warm_up:
        workout_exercises.append({
            'name': f"🔥 Warm-up: {exercise['name']}",
            'sets': exercise['sets'],
            'reps': exercise['reps']
        })
    
    # Select main exercises based on fitness goal
    if user.fitness_goal.lower() == 'weight_loss':
        # Focus on cardio and bodyweight
        main_exercises = (
            EXERCISE_DATABASE['cardio'][:2] +  # 2 cardio exercises
            EXERCISE_DATABASE['bodyweight'][:2] +  # 2 bodyweight exercises
            EXERCISE_DATABASE['core'][:1]  # 1 core exercise
        )
    elif user.fitness_goal.lower() == 'muscle_gain':
        # Focus on strength and core
        main_exercises = (
            EXERCISE_DATABASE['strength'][:3] +  # 3 strength exercises
            EXERCISE_DATABASE['bodyweight'][:1] +  # 1 bodyweight exercise
            EXERCISE_DATABASE['core'][:1]  # 1 core exercise
        )
    else:  # maintenance
        # Balanced mix
        main_exercises = (
            EXERCISE_DATABASE['cardio'][:1] +  # 1 cardio exercise
            EXERCISE_DATABASE['bodyweight'][:2] +  # 2 bodyweight exercises
            EXERCISE_DATABASE['strength'][:1] +  # 1 strength exercise
            EXERCISE_DATABASE['core'][:1]  # 1 core exercise
        )
    
    # Adjust sets and reps based on experience level
    for exercise in main_exercises:
        adjusted_exercise = exercise.copy()
        if user.experience_level.lower() == 'beginner':
            adjusted_exercise['sets'] = min(exercise['sets'], 2)
            adjusted_exercise['reps'] = int(exercise['reps'] * 0.7)
        elif user.experience_level.lower() == 'advanced':
            adjusted_exercise['sets'] = exercise['sets'] + 1
            adjusted_exercise['reps'] = int(exercise['reps'] * 1.3)
        
        workout_exercises.append(adjusted_exercise)
    
    # Add cool-down exercises
    cool_down = EXERCISE_DATABASE['cool_down'][:3]  # Select first 3 cool-down exercises
    for exercise in cool_down:
        workout_exercises.append({
            'name': f"❄️ Cool-down: {exercise['name']}",
            'sets': exercise['sets'],
            'reps': exercise['reps']
        })
    
    # Generate a health tip using AI
    prompt = f"""As a fitness trainer, give a short health tip for a {user.age} year old person with {user.fitness_goal} goal."""
    try:
        tip_response = generator(prompt, max_length=100, num_return_sequences=1)[0]['generated_text']
        # Extract a reasonable tip from the response
        tip = tip_response.split('\n')[0][:100]  # Take first line, limit to 100 chars
        workout_exercises.append({
            'name': f"💡 Health Tip: {tip}",
            'sets': 0,
            'reps': 0
        })
    except Exception as e:
        print(f"Error generating health tip: {str(e)}")
        # Add a default tip
        workout_exercises.append({
            'name': "💡 Health Tip: Remember to stay hydrated and maintain proper form throughout your workout.",
            'sets': 0,
            'reps': 0
        })
    
    return workout_exercises

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        age = request.form.get('age')
        weight = request.form.get('weight')
        fitness_goal = request.form.get('fitness_goal')
        experience_level = request.form.get('experience_level')

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            age=age,
            weight=weight,
            fitness_goal=fitness_goal,
            experience_level=experience_level
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/generate_workout', methods=['POST'])
@login_required
def generate_workout():
    try:
        # Generate AI-based workout
        print("Starting workout generation for user:", current_user.username)
        workout_exercises = get_ai_workout(current_user)
        print("Successfully generated workout:", workout_exercises)
        return jsonify(workout_exercises)
    except Exception as e:
        print(f"Error generating workout: {str(e)}")
        import traceback
        print("Full error:", traceback.format_exc())
        # Fallback to basic workout if AI generation fails
        basic_workout = [
            {'name': 'Push-ups', 'sets': 3, 'reps': 10},
            {'name': 'Squats', 'sets': 3, 'reps': 15},
            {'name': 'Plank', 'sets': 3, 'reps': 30}
        ]
        return jsonify(basic_workout)

@app.route('/log_workout', methods=['POST'])
@login_required
def log_workout():
    data = request.json
    workout = Workout(user_id=current_user.id)
    db.session.add(workout)
    
    for exercise_data in data['exercises']:
        exercise = Exercise(
            workout_id=workout.id,
            name=exercise_data['name'],
            sets=exercise_data['sets'],
            reps=exercise_data['reps'],
            weight=exercise_data.get('weight', 0)
        )
        db.session.add(exercise)
    
    db.session.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
