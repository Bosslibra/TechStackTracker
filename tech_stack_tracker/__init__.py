""" Iniitialize Flask app and register blueprints. """

from flask import Flask


def create_app():
    """Create the Flask app."""
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.config.from_object("config.Config")

    with app.app_context():
        # Import the parts of the application

        ## Page-serving blueprints
        from .home import home

        ## API blueprints
        from .app.api import auth, health_check

        # Register the blueprints
        app.register_blueprint(home.home_blueprint)
        app.register_blueprint(health_check.health_check_blueprint)
        app.register_blueprint(auth.auth_blueprint)

    return app
