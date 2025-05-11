from flask import Blueprint, request, jsonify
from models.spoonacular_api import get_recipe_by_ingredients, get_recipe_details
from models.db import get_connection
from dotenv import load_dotenv
import os
load_dotenv()
spoonacalular_api_key = os.getenv('SPROUTACULAR_API_KEY')


recipe_bp = Blueprint('recipe', __name__)

@recipe_bp.route('/recipes', methods=['GET'])
def recipes():
    ingredients = request.args.get('ingredients')
    if not ingredients:
        return jsonify({"error": "Kérem adjon meg hozzávalókat"}), 400

    ingredients_list = [i.strip() for i in ingredients.split(",")]
    recipes = get_recipe_by_ingredients(ingredients_list)

    if recipes is None:
        return jsonify({"error": "Nem sikerült recepteket lekérni"}), 500

    return jsonify(recipes)

@recipe_bp.route('/recipe/<int:recipe_id>', methods=['GET'])
def recipe_details(recipe_id):
    details = get_recipe_details(recipe_id)
    if details is None:
        return jsonify({"error": "A recept nem található"}), 404

    return jsonify(details)
