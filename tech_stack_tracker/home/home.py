from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__)


# Home page route
@home_bp.route("/")
def home():
    """
    Serves the home page.
    """
    return render_template("index.html")
