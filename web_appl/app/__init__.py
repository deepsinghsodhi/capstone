from flask import Flask
import os

def create_app():
    app = Flask(__name__,
                template_folder='../templates',  # Specify the correct template path
                static_folder='static')
    
    # Create necessary directories
    os.makedirs('app/static/extracted_tables', exist_ok=True)
    
    # Import and register routes
    from app.routes import main
    app.register_blueprint(main)
    
    return app