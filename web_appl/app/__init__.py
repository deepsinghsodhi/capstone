from flask import Flask
import os

def create_app():
    app = Flask(__name__,
                template_folder='../templates',  # Points to the templates folder
                static_folder='static')
    
    # Create necessary directories
    os.makedirs('app/static/extracted_tables', exist_ok=True)
    
    # Import and register routes
    from .routes import main
    app.register_blueprint(main, url_prefix='/')  # Add url_prefix
    
    return app