import firebase_admin
import requests
from firebase_admin import credentials, firestore, auth
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import os

# Initialize Flask and Firebase
app = Flask(__name__)
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Firestore Database Reference
db = firestore.client()

# Set the path for your HTML files directory
# Adjust this to where your HTML files are stored
HTML_FOLDER = os.path.join(os.getcwd(), 'html_files')

# Commenting out Spoonacular functions since we're not using them anymore
'''
def fetch_recipes_from_spoonacular():
    api_key = "eca8f74b082b4b09ba4c5764eb377330"
    url = f"https://api.spoonacular.com/recipes/complexSearch?apiKey={api_key}&number=10"
    response = requests.get(url)
    if response.status_code == 200:
        recipes = response.json()['results']
        print("Fetched recipes:", recipes)
        for recipe in recipes:
            # Save the recipe and its ingredients
            recipe_id = recipe['id']
            save_recipe_to_firestore(recipe, recipe_id)
            # Fetch full recipe details (including ingredients)
            fetch_recipe_details_and_save(recipe_id)
    else:
        print("Error fetching data:", response.status_code)

def fetch_recipe_details_and_save(recipe_id):
    # Fetch detailed recipe information using recipe ID
    api_key = "eca8f74b082b4b09ba4c5764eb377330"
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        recipe_details = response.json()
        # Get ingredients for the recipe
        ingredients = recipe_details.get('extendedIngredients', [])
        for ingredient in ingredients:
            ingredient_id = ingredient['id']
            # Save detailed ingredient data
            save_ingredient_to_firestore(ingredient)
    else:
        print(f"Error fetching recipe details for recipe ID {recipe_id}: {response.status_code}")

def save_ingredient_to_firestore(ingredient):
    # Fetch additional details like allergens, nutrition (if available)
    api_key = "eca8f74b082b4b09ba4c5764eb377330"
    ingredient_id = ingredient['id']
    url = f"https://api.spoonacular.com/food/ingredients/{ingredient_id}/information?apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        ingredient_info = response.json()
        # Store detailed ingredient information in Firestore
        ingredient_name = ingredient.get('name', 'unknown')
        ingredient_ref = db.collection('ingredients').document(ingredient_name)
        ingredient_ref.set({
            'name': ingredient_name,
            # Optional field
            'allergens': ingredient_info.get('allergens', []),
            # Nutrition facts
            'nutrition': ingredient_info.get('nutrition', {}),
        })
        print(f"Ingredient saved: {ingredient_name}")
    else:
        print(f"Error fetching ingredient info for {ingredient['name']}: {response.status_code}")
'''


def fetch_and_update_recipes():
    # Fetch all recipes from the Firestore 'recipes' collection
    recipes_ref = db.collection('recipes')
    recipes = recipes_ref.stream()

    for recipe in recipes:
        recipe_data = recipe.to_dict()
        print(f"Fetched Recipe: {recipe_data['title']}")

        # Check if 'cooking_time' exists and convert it to 'cooking_minutes' and 'cooking_hours'
        if 'cooking_time' in recipe_data:
            cooking_time = recipe_data['cooking_time']
            cooking_minutes = cooking_time
            cooking_hours = cooking_minutes // 60
            cooking_remaining_minutes = cooking_minutes % 60

            # Remove 'cooking_time' field and add new cooking hours and minutes
            recipe_ref = db.collection('recipes').document(recipe.id)
            recipe_ref.update({
                'cooking_hours': cooking_hours,
                'cooking_minutes': cooking_remaining_minutes,
            })
            recipe_ref.update({
                'cooking_time': firestore.DELETE_FIELD  # Remove the old 'cooking_time' field
            })
            print(f"Updated Recipe: {
                  recipe_data['title']} with cooking hours and minutes")

# Flask routes to handle login and sign-up


@app.route('/')
def home():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    # Adjust the HTML file location
    return send_from_directory(HTML_FOLDER, 'home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Authenticate with Firebase
            user = auth.get_user_by_email(email)

            # Here you would validate the password (if using Firebase Auth for authentication)
            # Assuming authentication is successful:
            # Store the Firebase user ID in session
            session['user_id'] = user.uid
            # Redirect to home page on successful login
            return redirect(url_for('home'))

        except auth.AuthError as e:
            flash('Login failed: ' + str(e))
            # Redirect to login page on failure
            return redirect(url_for('login'))

    # Adjust the HTML file location
    return send_from_directory(HTML_FOLDER, 'login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user session
    return redirect(url_for('login'))  # Redirect to login page


if __name__ == '__main__':
    app.run(debug=True)

# Call this function to fetch and update recipes
fetch_and_update_recipes()
