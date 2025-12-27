"""
Flask Web Application for Azure Web App
Python 3.14 compatible
"""
from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', title='Home')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html', title='About')

@app.route('/api/health')
def health():
    """Health check endpoint for Azure"""
    return jsonify({
        'status': 'healthy',
        'message': 'Application is running'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html', title='Page Not Found'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html', title='Server Error'), 500

if __name__ == '__main__':
    # For local development
    app.run(host='0.0.0.0', port=8000, debug=True)
