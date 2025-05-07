from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.db import get_connection
from models.user_model import load_user_by_id
import os
from models.db import get_connection
from flask_login import login_user
from models.calorie_model import get_today_calories




user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    entries = get_today_calories(current_user.id)
    
    totals = {
        "total_calories": sum(e['calories'] for e in entries),
        "total_protein": sum(e['protein'] for e in entries),
        "total_carbs": sum(e['carbs'] for e in entries),
        "total_fats": sum(e['fats'] for e in entries)
    }

    return render_template('dashboard.html', entries=entries, **totals)



@user_bp.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'GET':
        return render_template('update_profile.html', user=current_user)

    age = request.form.get('age')
    height = request.form.get('weight')  # <-- Megcserélve
    weight = request.form.get('height')  # <-- Megcserélve
    gender = request.form.get('gender')
    training_intensity = request.form.get('training_intensity')
    training_goal = request.form.get('training_goal')

    if not all([age, weight, height, gender, training_intensity, training_goal]):
        flash("Minden mező kitöltése kötelező", 'error')
        return redirect(url_for('user.update_profile'))

    conn = get_connection()
    conn.run("""
        UPDATE users SET age = :age, weight = :weight, height = :height, 
                         gender = :gender, training_intensity = :training_intensity, training_goal = :training_goal
        WHERE id = :id
    """, age=age, weight=weight, height=height, gender=gender, 
         training_intensity=training_intensity, training_goal=training_goal, id=current_user.id)
    conn.close()

    current_user.age = int(age)
    current_user.weight = float(weight)
    current_user.height = float(height)
    current_user.gender = gender
    current_user.training_intensity = training_intensity
    current_user.training_goal = training_goal

    flash("Az adatok frissítve!", "success")
    return redirect(url_for('user.dashboard'))




@user_bp.route('/get_training_plan')
@login_required
def get_training_plan():
    # Check if user has necessary profile data
    if not all([current_user.gender, current_user.training_intensity, current_user.training_goal]):
        return "Kérjük frissítse a profilját a megfelelő edzésterv generálásához."
    
    # Convert to string first, then strip and capitalize
    user_gender = str(current_user.gender).strip().capitalize()
    user_intensity = str(current_user.training_intensity).strip().capitalize() 
    user_goal = str(current_user.training_goal).strip().capitalize()
    
    # Debug statements
    print(f"Looking for plan with: Gender={user_gender}, Intensity={user_intensity}, Goal={user_goal}")
    
    # Create the search pattern (Capitalized format with commas)
    search_pattern = f"{user_gender}, {user_intensity}, {user_goal}"
    print(f"Search pattern: {search_pattern}")
    
    path = os.path.join('static', 'training_plans.txt')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            full_content = f.read()
        
        # Look for exact match at the start of a line
        for line in full_content.splitlines():
            if line.startswith(search_pattern):
                # Split at the first colon
                plan_data = line.split(':', 1)[1].strip()
                print(f"Found plan: {plan_data[:50]}...")  # Debug - print beginning of plan
                return plan_data
            
        # No direct match found, try case-insensitive search
        search_pattern_lower = search_pattern.lower()
        for line in full_content.splitlines():
            key_part = line.split(':', 1)[0].strip().lower()
            if key_part == search_pattern_lower:
                plan_data = line.split(':', 1)[1].strip()
                print(f"Found plan (case-insensitive): {plan_data[:50]}...")
                return plan_data
        
        # Still not found, check for whitespace issues
        for line in full_content.splitlines():
            if ':' in line:  # Ensure line has the expected format
                key_parts = [k.strip().lower() for k in line.split(':', 1)[0].split(',')]
                user_parts = [user_gender.lower(), user_intensity.lower(), user_goal.lower()]
                
                if len(key_parts) == len(user_parts) and all(k.strip() == u.strip() for k, u in zip(key_parts, user_parts)):
                    plan_data = line.split(':', 1)[1].strip()
                    print(f"Found plan (normalized): {plan_data[:50]}...")
                    return plan_data
                
        # If we've checked all lines and found no match
        print("No matching plan found for:", search_pattern)
        return "Nincs megfelelő edzésterv az ön paramétereihez. Kérjük, ellenőrizze profil adatait."

    except Exception as e:
        print(f"Hiba a fájl olvasásakor: {e}")
        return f"Edzésterv nem elérhető. Hiba: {str(e)}"

