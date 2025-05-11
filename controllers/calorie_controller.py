from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.calorie_model import save_calorie_entry, get_today_calories
from models.spoonacular_api import get_food_nutrition
from models.db import get_connection
from dotenv import load_dotenv
load_dotenv()

calorie_bp = Blueprint('calorie', __name__)

@calorie_bp.route('/calorie_counter')
@login_required
def calorie_counter():
    entries = get_today_calories(current_user.id)
    
    totals = {
        "total_calories": sum(e['calories'] for e in entries),
        "total_protein": sum(e['protein'] for e in entries),
        "total_carbs": sum(e['carbs'] for e in entries),
        "total_fats": sum(e['fats'] for e in entries)
    }

    return render_template('dashboard.html', entries=entries, **totals)


@calorie_bp.route('/calories', methods=['POST'])
@login_required
def add_calories():
    print("----- FORM ADATOK -----")
    for key, value in request.form.items():
        print(f"{key}: {value}")
    print("------------------------")

    try:
        food = request.form.get('food')
        amount_raw = request.form.get('amount')
        print(f"Kapott étel: {food}, amount: {amount_raw}")  # <- debug
        
        try:
            amount = int(amount_raw)
        except (TypeError, ValueError):
            amount = 100  # fallback érték


        if not food:
            flash('Étel megadása kötelező!', 'danger')
            return redirect(url_for('user.dashboard'))  # ← ide térj vissza!

        nutrition = get_food_nutrition(food, amount)
        if not nutrition:
            flash('Az étel nem található!', 'warning')
            return redirect(url_for('user.dashboard'))

        save_calorie_entry(current_user.id, nutrition)
        flash('Étel sikeresen hozzáadva!', 'success')
        return redirect(url_for('user.dashboard'))  # ← ide térj vissza!

    except Exception as e:
        print(f"Hiba kalória mentés közben: {e}")
        flash('Szerverhiba történt.', 'danger')
        return redirect(url_for('user.dashboard'))



@calorie_bp.route('/get_calories', methods=['GET'])
@login_required
def get_calorie_log():
    try:
        entries = get_today_calories(current_user.id)

        totals = {
            "total_calories": sum(e['calories'] for e in entries),
            "total_protein": sum(e['protein'] for e in entries),
            "total_carbs": sum(e['carbs'] for e in entries),
            "total_fats": sum(e['fats'] for e in entries)
        }

        return jsonify({"entries": entries, **totals})
    except Exception as e:
        print(f"Hiba kalória lekérés közben: {e}")
        return jsonify({"error": "Szerverhiba"}), 500


@calorie_bp.route('/calorie_stats', methods=['GET'])
@login_required
def calorie_stats():
    try:
        entries = get_today_calories(current_user.id)
        total_calories = sum(e['calories'] for e in entries)

        # Alapadatok a felhasználótól
        weight = float(current_user.weight)
        height = float(current_user.height)
        age = int(current_user.age)
        gender = (current_user.gender or "").lower()
        intensity = (current_user.training_intensity or "").lower()
        goal = (current_user.training_goal or "").lower()

        # BMR számítás
        if gender == 'férfi':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        # Aktivitási szorzók
        multiplier_map = {
            'alacsony': 1.2,
            'közepes': 1.3,
            'magas': 1.5
        }
        multiplier = multiplier_map.get(intensity, 1.2)

        daily_need = bmr * multiplier

        # 🎯 Célnak megfelelő módosítás
        if goal == 'tömegelés':
            daily_need *= 1.15  # +15% kalória
        elif goal == 'szálkásítás':
            daily_need *= 0.85  # -20% kalória

        daily_need = round(daily_need)

        return jsonify({
            "consumed": total_calories,
            "required": daily_need
        })

    except Exception as e:
        print(f"[HIBA] Kalória statisztika: {e}")
        return jsonify({"error": "Hiba a statisztika lekérdezésekor."}), 500

