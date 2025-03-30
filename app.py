from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pg8000.native
import sys
from spoonacular_api import get_recipe_by_ingredients, get_recipe_details
from spoonacular_api import get_food_nutrition
import stripe

app = Flask(__name__, template_folder='templates')

app.secret_key = 'your-secret-key-here'
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

            # Create a table for logging calorie intake
            conn.run("""
                CREATE TABLE IF NOT EXISTS calorie_log (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id) ON DELETE CASCADE,
                    food_name VARCHAR(255) NOT NULL,
                    calories DECIMAL(5, 2) NOT NULL,
                    protein DECIMAL(5, 2) NOT NULL,
                    carbs DECIMAL(5, 2) NOT NULL,
                    fats DECIMAL(5, 2) NOT NULL,
                    log_date DATE DEFAULT CURRENT_DATE
                );
            """)
            conn.close()
            print("Database initialized successfully")
        else:
            print("Could not initialize database - connection failed")
    except Exception as e:
        print(f"Database initialization error: {e}", file=sys.stderr)


class User(UserMixin):
    def __init__(self, id, name, email, height=None, weight=None, gender=None, age=None, training_intensity=None, training_goal=None, is_subscribed=False):
        self.id = id
        self.name = name
        self.email = email
        self.height = height
        self.weight = weight
        self.gender = gender
        self.age = age
        self.training_intensity = training_intensity
        self.training_goal = training_goal
        self.is_subscribed = is_subscribed  # új mező


@login_manager.user_loader
def load_user(user_id):
    try:
        conn = get_db_connection()
        if conn:
            user_data = conn.run("""
                SELECT id, name, email, height, weight, gender, age, training_intensity, training_goal, is_subscribed
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
                    training_intensity=user_data[0][7],
                    training_goal=user_data[0][8],
                    is_subscribed=user_data[0][9]
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
        training_goal = request.form.get('training_goal')  # ÚJ MEZŐ

        if not age or not weight or not height or not gender or not training_intensity or not training_goal:
            flash('Minden mező kitöltése kötelező', 'error')
            return redirect(url_for('update_profile'))

        conn = get_db_connection()
        if not conn:
            flash('Szerverhiba történt', 'error')
            return redirect(url_for('dashboard'))

        # Update the user's profile in the database
        conn.run("""
            UPDATE users
            SET age = :age, weight = :weight, height = :height, gender = :gender, 
                training_intensity = :training_intensity, training_goal = :training_goal
            WHERE id = :id
        """, age=age, weight=weight, height=height, gender=gender, 
            training_intensity=training_intensity, training_goal=training_goal, id=current_user.id)
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
            current_user.training_goal = training_goal  # ÚJ MEZŐ

        flash('Az adatok sikeresen frissítve lettek!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"Update profile error: {e}", file=sys.stderr)
        flash('Hiba történt az adatok frissítése során', 'error')
        return redirect(url_for('update_profile'))




@app.route('/get_training_plan')
@login_required
def get_training_plan():
    user_key = (current_user.gender, current_user.training_intensity, current_user.training_goal)
    print(f"🔍 Felhasználói kulcs: {user_key}")  # Debug kiírás

    # Betöltjük az edzésterveket a fájlból
    try:
        with open("/Users/balazshiezl/Downloads/szakdoga/training_plans.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(": ")
                if len(parts) == 2:
                    key, plan = parts
                    key_parts = tuple(key.split(", "))
                    
                    print(f"Beolvasott kulcs: {key_parts}")  # Debug kiírás
                    if key_parts == user_key:
                        print(f"Talált edzésterv: {plan}")
                        return plan  # Visszaadjuk a megfelelő edzéstervet
    except Exception as e:
        print(f"⚠️ Hiba az edzéstervek beolvasásakor: {e}")
        return "Edzésterv nem elérhető."

    print("🚫 Nincs megfelelő edzésterv az adatbázisban.")
    return "Nincs megfelelő edzésterv az adatbázisban."


@app.route('/recipes', methods=['GET'])
def recipes():
    ingredients = request.args.get('ingredients')
    if not ingredients:
        return jsonify({"error": "Please provide ingredients"}), 400

    ingredients_list = ingredients.split(",")
    recipes = get_recipe_by_ingredients(ingredients_list)
    return jsonify(recipes)

@app.route('/recipe/<int:recipe_id>', methods=['GET'])
def recipe_details(recipe_id):
    recipe_info = get_recipe_details(recipe_id)
    return jsonify(recipe_info)

@app.route('/calorie_counter')
@login_required
def calorie_counter():
    return render_template('calorie_counter.html')

@app.route('/calories', methods=['POST'])
@login_required
def add_calories():
    try:
        data = request.json
        food = data.get('food')
        amount = data.get('amount', 100)  # Default to 100g if not specified

        if not food:
            return jsonify({"error": "No food provided"}), 400

        nutrition = get_food_nutrition(food, amount)
        if not nutrition:
            return jsonify({"error": "Food not found"}), 404

        conn = get_db_connection()
        if conn:
            conn.run("""
                INSERT INTO calorie_log (user_id, food_name, calories, protein, carbs, fats)
                VALUES (:user_id, :food_name, :calories, :protein, :carbs, :fats)
            """, 
            user_id=current_user.id,
            food_name=nutrition['name'],
            calories=nutrition['calories'],
            protein=nutrition['protein'],
            carbs=nutrition['carbs'],
            fats=nutrition['fats'])
            conn.close()

        return jsonify(nutrition)

    except Exception as e:
        print(f"Error adding calories: {e}", file=sys.stderr)
        return jsonify({"error": "Server error"}), 500


@app.route('/get_calories', methods=['GET'])
@login_required
def get_calorie_log():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection error"}), 500

        today_entries = conn.run("""
            SELECT food_name, calories, protein, carbs, fats 
            FROM calorie_log 
            WHERE user_id = :user_id AND log_date = CURRENT_DATE
        """, user_id=current_user.id)
        conn.close()

        total_calories = sum(row[1] for row in today_entries)
        total_protein = sum(row[2] for row in today_entries)
        total_carbs = sum(row[3] for row in today_entries)
        total_fats = sum(row[4] for row in today_entries)

        return jsonify({
            "entries": [{"name": row[0], "calories": row[1], "protein": row[2], "carbs": row[3], "fats": row[4]} for row in today_entries],
            "total_calories": total_calories,
            "total_protein": total_protein,
            "total_carbs": total_carbs,
            "total_fats": total_fats
        })
    except Exception as e:
        print(f"Error fetching calorie log: {e}", file=sys.stderr)
        return jsonify({"error": "Server error"}), 500


from datetime import datetime
import schedule
import time

def reset_calories():
    try:
        conn = get_db_connection()
        if conn:
            conn.run("DELETE FROM calorie_log WHERE log_date < CURRENT_DATE;")
            conn.close()
            print(f"Calorie log reset at {datetime.now()}")
    except Exception as e:
        print(f"Error resetting calorie log: {e}", file=sys.stderr)

schedule.every().day.at("00:00").do(reset_calories)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start the scheduler in a separate thread
import threading
threading.Thread(target=run_scheduler, daemon=True).start()





# Stripe konfiguráció
stripe.api_key = 'sk_test_51R8HlIR7HJHOCBgmVRbSUTiZXIhSKDD07WSCeLzJBgIfa4HsuavSZRAFVXpj5kNzv6cUIF7fuvb0WZYIzNSRyE5J00tgVWFUy3'

@app.route('/create-checkout-session/<plan>', methods=['POST'])
@login_required
def create_checkout_session(plan):
    price_lookup = {
        'halado': 'price_1R8I2DR7HJHOCBgm532K337H',  # Stripe ár ID (Price ID)
        'profi': 'price_1R8I4sR7HJHOCBgmDtA05EGP'
    }

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_lookup.get(plan),
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('dashboard', _external=True),
            cancel_url=url_for('index', _external=True),
            customer_email=current_user.email
        )
        return jsonify({'id': session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403
    

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = 'whsec_ebdf92e2ce3281bd06ee88769fc07b02b6a242cc0fdfe6d8e44c87dc1778a04f'  # Ezt a Stripe webhook setupnál kapod

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except stripe.error.SignatureVerificationError:
        return '', 400

    # Ha sikeres fizetés történt
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get('customer_email')

        # Frissítsük az előfizetői státuszt
        conn = get_db_connection()
        if conn:
            conn.run("UPDATE users SET is_subscribed = TRUE WHERE email = :email", email=email)
            conn.close()

    return '', 200   


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
