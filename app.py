from flask import Flask, render_template, redirect, url_for
from logic import home, resep, ai

app = Flask(__name__)

@app.route('/')
def index():
    return redirect(url_for('home_page'))

@app.route('/home')
def home_page():
    content = home.get_home_content()
    return render_template('home.html', active_tab='home', **content)

@app.route('/resep')
def resep_page():
    recipes = resep.get_all_recipes()
    return render_template('resep.html', active_tab='resep', recipes=recipes)

@app.route('/ai', methods=['GET', 'POST'])
def ai_page():
    return ai.handle_ai_request()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
