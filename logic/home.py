from flask import render_template

def get_home_content():
    """Get content for the home page"""
    welcome_text = "Your Personal Recipe AI Assistant"
    description = "Discover delicious recipes based on the ingredients you already have. Our AI will analyze your available ingredients and recommend the perfect dishes to make."
    
    features = [
        {
            "title": "Natural Language Understanding",
            "description": "Simply tell the AI what ingredients you have in your kitchen, and it will understand what you're looking for."
        },
        {
            "title": "Intelligent Recipe Matching",
            "description": "Our AI analyzes your ingredients and finds the best recipe matches from our database."
        },
        {
            "title": "Interactive Experience",
            "description": "Explore recipes through a conversational interface similar to Claude AI."
        }
    ]
    
    return {
        'welcome_text': welcome_text,
        'description': description,
        'features': features
    }
