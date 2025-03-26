from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from transformers import pipeline
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///fitness.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'media', 'exercises')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    fitness_goal = db.Column(db.String(50), nullable=False)
    experience_level = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

class ExerciseMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255))
    video_filename = db.Column(db.String(255))
    category = db.Column(db.String(50), nullable=False)  # e.g., 'strength', 'cardio', 'flexibility'
    difficulty = db.Column(db.String(20), nullable=False)  # 'beginner', 'intermediate', 'advanced'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image_url': url_for('static', filename=f'media/exercises/images/{self.image_filename}') if self.image_filename else None,
            'video_url': url_for('static', filename=f'media/exercises/videos/{self.video_filename}') if self.video_filename else None,
            'category': self.category,
            'difficulty': self.difficulty
        }

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to list all exercises
@app.route('/exercises', methods=['GET'])
def list_exercises():
    exercises = ExerciseMedia.query.all()
    return render_template('exercises.html', exercises=[ex.to_dict() for ex in exercises])

# Route to view an exercise
@app.route('/exercises/<int:id>', methods=['GET'])
def view_exercise(id):
    exercise = ExerciseMedia.query.get_or_404(id)
    return render_template('exercise_detail.html', exercise=exercise.to_dict())

# Route to create a new exercise
@app.route('/exercises/new', methods=['GET', 'POST'])
@login_required
def new_exercise():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            category = request.form.get('category')
            difficulty = request.form.get('difficulty')

            # Handle image upload
            image_file = request.files.get('image')
            image_filename = None
            if image_file and allowed_file(image_file.filename):
                image_filename = secure_filename(image_file.filename)
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'images', image_filename))

            # Handle video upload
            video_file = request.files.get('video')
            video_filename = None
            if video_file and allowed_file(video_file.filename):
                video_filename = secure_filename(video_file.filename)
                video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'videos', video_filename))

            exercise = ExerciseMedia(
                name=name,
                description=description,
                image_filename=image_filename,
                video_filename=video_filename,
                category=category,
                difficulty=difficulty
            )

            db.session.add(exercise)
            db.session.commit()
            flash('Exercise created successfully!', 'success')
            return redirect(url_for('list_exercises'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating exercise: {str(e)}")
            flash('Error creating exercise. Please try again.', 'danger')
            return redirect(url_for('new_exercise'))

    return render_template('exercise_form.html')

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_ai_workout(user):
    # Initialize the text generation pipeline with API key
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    if not api_key:
        raise ValueError("Hugging Face API key not found. Please set HUGGINGFACE_API_KEY in your .env file")
    
    generator = pipeline('text-generation', model='gpt2-medium', token=api_key)
    
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
        try:
            # Get form data
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Log received data (excluding password)
            logger.debug(f"Registration attempt - Username: {username}, Email: {email}")
            
            # Validate required fields
            if not all([username, email, password]):
                flash('All fields are required', 'danger')
                return redirect(url_for('register'))
            
            try:
                age = int(request.form.get('age', 0))
                weight = float(request.form.get('weight', 0))
            except ValueError:
                flash('Age and weight must be valid numbers', 'danger')
                return redirect(url_for('register'))
            
            fitness_goal = request.form.get('fitness_goal', 'maintenance')
            experience_level = request.form.get('experience_level', 'beginner')
            
            # Check if username exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))
            
            # Check if email exists
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
            
            # Create new user
            user = User(
                username=username,
                email=email,
                age=age,
                weight=weight,
                fitness_goal=fitness_goal,
                experience_level=experience_level
            )
            user.set_password(password)
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"Successfully registered user: {username}")
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
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
