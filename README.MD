Fitness AI App
The Fitness AI App is a Flask-based web application designed to provide personalized workout plans powered by AI. It helps users achieve their fitness goals by generating tailored workout routines, tracking progress, and offering a library of exercises.

Features
 AI-Powered Workouts
Generate personalized workout plans using Hugging Face's GPT-2 model.
Plans include warm-ups, main exercises, cool-downs, and health tips.

 Progress Tracking
Log completed workouts and monitor progress over time.
 User Profiles
Create and manage profiles with fitness goals, experience levels, and personal details.

Responsive Design
User-friendly interface built with Bootstrap for seamless use on any device.

Tech Stack

Backend
Flask: Web framework
Flask-SQLAlchemy: Database ORM
Flask-Login: User authentication
Flask-CORS: Cross-origin resource sharing 

AI Integration
Hugging Face Transformers: GPT-2 for AI-generated health tips
Torch: Deep learning framework 

Frontend
HTML, CSS, Bootstrap: Responsive UI design
Database
SQLite: Default database for local development and testing 

Development Features
Testing: Pytest with mocked AI pipelines for isolated testing.
CI/CD: GitHub Actions for automated linting and testing.
Environment Management: .env support via python-dotenv.