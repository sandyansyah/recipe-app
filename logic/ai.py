import json
import numpy as np
import pandas as pd
from flask import render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import string
import joblib
import os
import re

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Path to the model and data files
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.joblib')
DATA_PATH = os.path.join(os.path.dirname(__file__), 'model.json')

def preprocess_text(text):
    """Preprocess text for NLP tasks"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation
    text = ''.join([char for char in text if char not in string.punctuation])
    
    # Simple tokenize by splitting on whitespace instead of using nltk.word_tokenize
    # This avoids the punkt_tab issue
    tokens = text.split()
    
    # Remove stopwords and lemmatize
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
    
    return ' '.join(tokens)

def train_model():
    """Train the NLM recommendation model using the data from model.json"""
    # Load the JSON data
    with open(DATA_PATH, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Create a DataFrame
    recipes_df = pd.DataFrame(data['recipes'])
    
    # Preprocess ingredients and combine into a single string for each recipe
    recipes_df['ingredients_text'] = recipes_df['ingredients'].apply(
        lambda x: ' '.join([preprocess_text(ingredient) for ingredient in x])
    )
    
    # Create recipe descriptions that combine name and ingredients for better context
    recipes_df['recipe_context'] = recipes_df.apply(
        lambda x: f"{preprocess_text(x['name'])} {x['ingredients_text']}", axis=1
    )
    
    # Create TF-IDF vectors with advanced parameters
    tfidf_vectorizer = TfidfVectorizer(
        min_df=1,
        max_df=0.95,
        max_features=None,
        ngram_range=(1, 2),
        use_idf=True,
        smooth_idf=True,
        sublinear_tf=True
    )
    tfidf_matrix = tfidf_vectorizer.fit_transform(recipes_df['recipe_context'])
    
    # Create a model dictionary with all necessary components
    model = {
        'vectorizer': tfidf_vectorizer,
        'tfidf_matrix': tfidf_matrix,
        'recipes': recipes_df,
        'ingredients_vocab': tfidf_vectorizer.get_feature_names_out()
    }
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Save the model
    joblib.dump(model, MODEL_PATH)
    print("NLM model trained and saved successfully.")

def load_model():
    """Load the trained model"""
    if not os.path.exists(MODEL_PATH):
        train_model()
    
    return joblib.load(MODEL_PATH)

def parse_user_query(query):
    """Parse natural language query to extract ingredients"""
    # Convert to lowercase and clean up
    query = query.lower()
    
    # Common phrases indicating ingredients
    ingredient_indicators = [
        "i have", "we have", "got", "using", "with", "use", 
        "ingredients:", "ingredients are", "ingredients include",
        "saya punya", "aku punya", "bahan:", "bahan-bahan:"
    ]
    
    # Remove these phrases
    for indicator in ingredient_indicators:
        query = query.replace(indicator, "")
    
    # Extract individual ingredients
    ingredients = []
    
    # Split by common separators
    for item in re.split(r'[,;.]|and|dan', query):
        item = item.strip()
        if item and len(item) > 1:  # Avoid empty or single-letter entries
            ingredients.append(item)
    
    return ingredients

def extract_ingredients_from_text(text):
    """Extract ingredients from natural language text input"""
    # Try to parse ingredients from query
    parsed_ingredients = parse_user_query(text)
    
    # Load model to get ingredient vocabulary
    model = load_model()
    all_ingredients = get_all_ingredients()
    
    # Match parsed ingredients against known ingredients
    confirmed_ingredients = []
    
    for parsed_item in parsed_ingredients:
        parsed_item = preprocess_text(parsed_item)
        
        # Check for exact matches
        for known_ingredient in all_ingredients:
            if parsed_item in preprocess_text(known_ingredient) or preprocess_text(known_ingredient) in parsed_item:
                confirmed_ingredients.append(known_ingredient)
                break
    
    return confirmed_ingredients

def get_recommendations(input_text, num_recommendations=5):
    """Get recipe recommendations based on natural language input"""
    model = load_model()
    vectorizer = model['vectorizer']
    tfidf_matrix = model['tfidf_matrix']
    recipes_df = model['recipes']
    
    # Extract ingredients from input text
    ingredients_list = extract_ingredients_from_text(input_text)
    
    # If no ingredients were extracted, try processing the raw input
    if not ingredients_list:
        # Preprocess the input text directly
        preprocessed_input = preprocess_text(input_text)
        
        # Transform the preprocessed input to TF-IDF vector
        input_vector = vectorizer.transform([preprocessed_input])
    else:
        # Convert extracted ingredients to a string
        ingredients_text = ' '.join([preprocess_text(ing) for ing in ingredients_list])
        
        # Transform the input ingredients to TF-IDF vector
        input_vector = vectorizer.transform([ingredients_text])
    
    # Calculate cosine similarity between input and all recipes
    cosine_similarities = cosine_similarity(input_vector, tfidf_matrix).flatten()
    
    # Get top recommendations
    recommended_indices = cosine_similarities.argsort()[-num_recommendations:][::-1]
    
    # Get recommended recipes
    recommendations = []
    for idx in recommended_indices:
        recipe = recipes_df.iloc[idx]
        
        # Only include recipes with a similarity score above threshold
        similarity_score = float(cosine_similarities[idx])
        if similarity_score > 0.05:  # Threshold to ensure some relevance
            recommendations.append({
                'name': recipe['name'],
                'ingredients': recipe['ingredients'],
                'instructions': recipe['instructions'],
                'similarity_score': similarity_score,
                'extracted_ingredients': ingredients_list
            })
    
    return recommendations, ingredients_list

def get_all_ingredients():
    """Get a list of all available ingredients"""
    model = load_model()
    recipes_df = model['recipes']
    
    # Extract unique ingredients from all recipes
    all_ingredients = set()
    for ingredients in recipes_df['ingredients']:
        all_ingredients.update(ingredients)
    
    return sorted(list(all_ingredients))

def handle_ai_request():
    """Handle AI recommendation requests"""
    recommendations = []
    user_input = ""
    extracted_ingredients = []
    
    if request.method == 'POST':
        if request.is_json:
            # Handle AJAX request for recommendations
            data = request.get_json()
            user_input = data.get('query', '')
            recommendations, extracted_ingredients = get_recommendations(user_input)
            
            # Format response for JSON
            response = {
                'recommendations': recommendations,
                'extracted_ingredients': extracted_ingredients
            }
            return jsonify(response)
        else:
            # Handle form submission
            user_input = request.form.get('query', '')
            if user_input:
                recommendations, extracted_ingredients = get_recommendations(user_input)
    
    # For both GET requests and form submissions
    return render_template('ai.html', 
                          active_tab='ai', 
                          recommendations=recommendations, 
                          user_input=user_input,
                          extracted_ingredients=extracted_ingredients,
                          all_ingredients=get_all_ingredients())

# When this script is run directly, train the model
if __name__ == "__main__":
    train_model()
