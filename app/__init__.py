import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from .config import config
from .extensions import db, migrate

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from .routes.main import main_bp
    from .routes.health import health_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(health_bp, url_prefix='/api')

    # Register error handlers
    from . import errors
    errors.register_error_handlers(app)

    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/cccgj.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CCC Gen Jong startup')

    return app
