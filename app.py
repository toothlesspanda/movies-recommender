from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from db import init_app
from routes.movies import bp as movies_bp

app = Flask(__name__)
app.config["DATABASE"] = "movies.db"
init_app(app)

limiter = Limiter(get_remote_address, app=app, default_limits=["60 per minute"])

app.register_blueprint(movies_bp)


@app.route("/")
def index():
    return render_template("index.html")
