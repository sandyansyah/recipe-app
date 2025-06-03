from flask import Flask, render_template, redirect, url_for, request, jsonify
from logic import home, diskusi, ai  # Updated import
from datetime import timedelta, datetime
import os

app = Flask(__name__)

# Configure session
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this to a secure secret key
app.permanent_session_lifetime = timedelta(days=7)  # Session lasts 7 days

# Configure file uploads
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create upload directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Middleware to make current_user available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=home.get_current_user())

# Custom datetime filter
@app.template_filter('datetime')
def format_datetime(value):
    """Format a datetime string to a human-readable format"""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%d %b %Y, %H:%M')
    except (ValueError, TypeError):
        return value

@app.route('/')
def index():
    return redirect(url_for('home_page'))

@app.route('/home')
def home_page():
    return home.render_home_page()

@app.route('/diskusi', methods=['GET', 'POST'])
def diskusi_page():
    return diskusi.handle_diskusi_request()

@app.route('/api/diskusi/messages')
def api_diskusi_messages():
    after_id = request.args.get('after_id')
    return diskusi.api_get_new_messages(after_id)

@app.route('/ai', methods=['GET', 'POST'])
def ai_page():
    return ai.handle_ai_request()

# Traditional Authentication routes
@app.route('/login-page')
def login_page():
    return home.render_login_page()

@app.route('/register-page')
def register_page():
    return home.render_register_page()

@app.route('/login', methods=['POST'])
def login():
    return home.handle_login()

@app.route('/register', methods=['POST'])
def register():
    return home.handle_register()

# Web3 Authentication routes
@app.route('/web3-login')
def web3_login_page():
    return home.render_web3_login_page()

@app.route('/web3-auth', methods=['POST'])
def web3_auth():
    return home.handle_web3_auth()

@app.route('/web3-verify', methods=['POST'])
def web3_verify():
    return home.handle_web3_verify()

# Logout route (works for both traditional and Web3 users)
@app.route('/logout')
def logout():
    return home.handle_logout()

# API endpoint to get current user info (useful for frontend)
@app.route('/api/user')
def api_user():
    current_user = home.get_current_user()
    if current_user:
        return jsonify({
            'logged_in': True,
            'user': current_user
        })
    else:
        return jsonify({
            'logged_in': False,
            'user': None
        })

# API endpoint to check Web3 support
@app.route('/api/web3-support')
def api_web3_support():
    return jsonify({
        'web3_enabled': True,
        'supported_networks': ['mainnet', 'goerli', 'sepolia', 'polygon', 'bsc'],
        'message': 'Web3 authentication is available'
    })

# API endpoint to get chat database info
@app.route('/api/diskusi/info')
def api_diskusi_info():
    return jsonify(diskusi.get_chat_database_info())

# Error handlers
@app.errorhandler(413)
def too_large(e):
    return redirect(url_for('diskusi_page', 
                          message="File terlalu besar. Maksimal 5MB.",
                          type="error"))

@app.errorhandler(404)
def not_found(e):
    return redirect(url_for('home_page'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)