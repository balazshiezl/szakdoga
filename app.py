from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pg8000.native
import sys

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database connection function
def get_db_connection():
    try:
        return pg8000.native.Connection(
            user="hbalazs",
            password="krokodil1",
            host="localhost",
            port=5432,
            database="szakdolgozat"
        )
    except Exception as e:
        print(f"Database connection error: {e}", file=sys.stderr)
        return None

# Initialize database tables
def init_db():
    try:
        conn = get_db_connection()
        if conn:
            # Create users table if it doesn't exist
            conn.run("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    age INT,
                    weight DECIMAL(5, 2),
                    height DECIMAL(5, 2),
                    gender VARCHAR(10),
                    training_intensity VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.close()
            print("Database initialized successfully")
        else:
            print("Could not initialize database - connection failed")
    except Exception as e:
        print(f"Database initialization error: {e}", file=sys.stderr)

class User(UserMixin):
    def __init__(self, id, name, email, height=None, weight=None, gender=None, age=None, training_intensity=None):
        self.id = id
        self.name = name
        self.email = email
        self.height = height
        self.weight = weight
        self.gender = gender
        self.age = age
        self.training_intensity = training_intensity

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = get_db_connection()
        if conn:
            user_data = conn.run("""
                SELECT id, name, email, height, weight, gender, age, training_intensity
                FROM users
                WHERE id = :id
            """, id=int(user_id))
            conn.close()
            if user_data:
                return User(
                    id=user_data[0][0],
                    name=user_data[0][1],
                    email=user_data[0][2],
                    height=user_data[0][3],
                    weight=user_data[0][4],
                    gender=user_data[0][5],
                    age=user_data[0][6],
                    training_intensity=user_data[0][7]
                )
    except Exception as e:
        print(f"Error loading user: {e}", file=sys.stderr)
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        if not name or not email or not password:
            flash('Minden mező kitöltése kötelező', 'error')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('A jelszavak nem egyeznek', 'error')
            return redirect(url_for('register'))

        conn = get_db_connection()
        if not conn:
            flash('Szerverhiba történt', 'error')
            return redirect(url_for('register'))

        # Check if email already exists
        existing_user = conn.run(
            "SELECT id FROM users WHERE email = :email",
            email=email
        )
        
        if existing_user:
            conn.close()
            flash('Ez az email cím már regisztrálva van', 'error')
            return redirect(url_for('register'))

        # Hash password and insert user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        conn.run(
            """
            INSERT INTO users (name, email, password)
            VALUES (:name, :email, :password)
            """,
            name=name, email=email, password=hashed_password
        )
        conn.close()
        
        flash('Sikeres regisztráció!', 'success')
        return redirect(url_for('login'))

    except Exception as e:
        print(f"Registration error: {e}", file=sys.stderr)
        flash('Hiba történt a regisztráció során', 'error')
        return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        if not conn:
            flash('Szerverhiba történt', 'error')
            return redirect(url_for('login'))

        user_data = conn.run(
            "SELECT id, name, email, password FROM users WHERE email = :email",
            email=email
        )
        conn.close()

        if user_data and bcrypt.check_password_hash(user_data[0][3], password):
            user = User(user_data[0][0], user_data[0][1], user_data[0][2])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Hibás email vagy jelszó', 'error')
            return redirect(url_for('login'))

    except Exception as e:
        print(f"Login error: {e}", file=sys.stderr)
        flash('Bejelentkezési hiba történt', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'GET':
        return render_template('update_profile.html')

    try:
        age = request.form.get('age')
        weight = request.form.get('weight')
        height = request.form.get('height')
        gender = request.form.get('gender')
        training_intensity = request.form.get('training_intensity')

        if not age or not weight or not height or not gender or not training_intensity:
            flash('Minden mező kitöltése kötelező', 'error')
            return redirect(url_for('update_profile'))

        conn = get_db_connection()
        if not conn:
            flash('Szerverhiba történt', 'error')
            return redirect(url_for('dashboard'))

        # Update the user's profile in the database
        conn.run("""
            UPDATE users
            SET age = :age, weight = :weight, height = :height, gender = :gender, training_intensity = :training_intensity
            WHERE id = :id
        """, age=age, weight=weight, height=height, gender=gender, training_intensity=training_intensity, id=current_user.id)
        conn.close()

        # Refresh the current_user object
        user_data = load_user(current_user.id)
        if user_data:
            # Update current_user properties manually
            current_user.age = age
            current_user.weight = weight
            current_user.height = height
            current_user.gender = gender
            current_user.training_intensity = training_intensity

        flash('Az adatok sikeresen frissítve lettek!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"Update profile error: {e}", file=sys.stderr)
        flash('Hiba történt az adatok frissítése során', 'error')
        return redirect(url_for('update_profile'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
