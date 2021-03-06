"""
This  file contains the flask factory function which will create an app.
"""

from flask import Flask
from app.config import Config
from app.database_client import DatabaseClient


def create_app(conf=Config):
    """
    Function to create an app.
    Using a factory function like this allows for better test handling (
    creating apps with certain parameters for testing and other parameters
    for production, without changing the code inbetween).

    :param conf: The configuration class
    :return: The app
    """
    # Initialise the flask app:
    app = Flask(__name__)

    # Load app configuration from the conf class:
    app.config.from_object(conf)

    # Load app into Flask's app_context
    app.app_context().push()

    # Register blueprints:
    from app.user import bp as user_bp
    app.register_blueprint(user_bp)

    from app.researcher import bp as researcher_bp
    app.register_blueprint(researcher_bp)

    from app.control import bp as control_bp
    app.register_blueprint(control_bp)

    # Initialise the database client:
    app.d = DatabaseClient()
    # File where the videos are stored:
    app.vid_file = 'app/user/video_conf.txt'
    # File where the user instructions are stored:
    app.user_instructions_file = 'app/user/user_instructions.txt'
    # File where the input fields are stored:
    app.input_fields = 'app/user/input_conf.txt'
    # All the databases that are available:
    app.dbs = {'prod': 'Production', 'dev': 'Development', 'local': 'Local'}
    # The default page for the researcher:
    app.researcher_default = 'researcher.clusters'
    # The default page for the user:
    app.user_default = 'user.userinstructions'

    return app
