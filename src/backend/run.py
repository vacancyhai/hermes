"""
Backend Flask Application Entry Point
"""
from app import create_app
from config.settings import get_config

# Create Flask app instance
app = create_app()

if __name__ == '__main__':
    config = get_config()
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
