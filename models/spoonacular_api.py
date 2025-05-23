import requests
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("SPOONACULAR_API")
BASE_URL = "https://api.spoonacular.com"

def get_recipe_by_ingredients(ingredients):
    print(API_KEY)
    """
    Fetches recipes based on available ingredients.
    """
    url = f"{BASE_URL}/recipes/findByIngredients"
    params = {
        "ingredients": ",".join(ingredients),
        "number": 5,
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None

def get_recipe_details(recipe_id):
    """
    Fetches detailed information for a recipe.
    """
    url = f"{BASE_URL}/recipes/{recipe_id}/information"
    params = {"apiKey": API_KEY}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None

def get_food_nutrition(food_name, amount=100):
   
    url = f"{BASE_URL}/food/ingredients/search"
    params = {"query": food_name, "number": 1, "apiKey": API_KEY}
    response = requests.get(url, params=params).json()

    if "results" in response and response["results"]:
        food_id = response["results"][0]["id"]
        return get_nutrition_by_id(food_id, amount)
    return None

def get_nutrition_by_id(food_id, amount):
    """
    Fetches detailed nutrition data for a food item by its ID and specified amount in grams.
    """
    url = f"{BASE_URL}/food/ingredients/{food_id}/information"
    params = {
        "amount": amount,  
        "unit": "g",
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params).json()

    nutrients = {nutrient["name"]: nutrient["amount"] for nutrient in response["nutrition"]["nutrients"]}

    return {
        "name": response.get("name", "Ismeretlen étel"),
        "calories": round(nutrients.get("Calories", 0), 2),
        "protein": round(nutrients.get("Protein", 0), 2),
        "carbs": round(nutrients.get("Carbohydrates", 0), 2),
        "fats": round(nutrients.get("Fat", 0), 2)
    }
