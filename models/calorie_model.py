from models.db import get_connection

def save_calorie_entry(user_id, nutrition):
    conn = get_connection()
    conn.run("""
        INSERT INTO calorie_log (user_id, food_name, calories, protein, carbs, fats, log_date)
        VALUES (:user_id, :food_name, :calories, :protein, :carbs, :fats, CURRENT_DATE)
    """, 
    user_id=user_id,
    food_name=nutrition['name'],
    calories=nutrition['calories'],
    protein=nutrition['protein'],
    carbs=nutrition['carbs'],
    fats=nutrition['fats'])
    conn.close()

def get_today_calories(user_id):
    conn = get_connection()
    results = conn.run("""
        SELECT food_name, calories, protein, carbs, fats 
        FROM calorie_log 
        WHERE user_id = :user_id AND log_date = CURRENT_DATE
    """, user_id=user_id)
    conn.close()

    return [
        {
            "name": row[0],
            "calories": float(row[1]),
            "protein": float(row[2]),
            "carbs": float(row[3]),
            "fats": float(row[4])
        }
        for row in results
    ]

