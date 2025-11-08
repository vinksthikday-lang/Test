from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import logging
import os
import sys

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from bot.utils.config import config
from bot.utils.security import security

def create_app():
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY
    
    # Configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize extensions
    CORS(app)
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Routes
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Simple authentication (replace with proper user database)
            if username == 'admin' and security.verify_password(password, security.hash_password('admin')):
                session['user_id'] = 1
                session['username'] = username
                return redirect(url_for('dashboard'))
        
        return render_template('login.html')
    
    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        return render_template('dashboard.html', user=session)
    
    @app.route('/api/stats')
    @limiter.limit("10 per minute")
    def api_stats():
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Return mock stats (replace with real data)
        return jsonify({
            'servers': 5,
            'users': 1250,
            'uptime': '24 hours',
            'commands': 3421
        })
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'timestamp': 'now'})
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app.run(
        host=config.WEB_HOST,
        port=config.WEB_PORT,
        debug=False
    )