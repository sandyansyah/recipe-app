import json
import os

def get_all_recipes():
    """Get all recipes from the JSON data"""
    data_path = os.path.join(os.path.dirname(__file__), 'model.json')
    
    try:
        with open(data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        return data['recipes']
    except Exception as e:
        print(f"Error loading recipes: {e}")
        return []
