from app import create_app  # If you added __init__.py in root

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)