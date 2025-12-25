from flask import Flask,redirect,render_template
from config.config import LocalDevelopmentConfig
from config.create_initial_data import setup_initial_data
from config.extensions import db,cache,mail
from async_celery.celery_setup import celery_init_app
from routes.auth import auth
from routes.user import user
from routes.admin import admin
from routes.ppt_gen import ppt_bp
from routes.ml import ml

def create_app():
    app = Flask(__name__,
                template_folder='../../frontend/html',
                static_folder='../../frontend')
    
    app.config.from_object(LocalDevelopmentConfig)
    from async_celery.celery_scheduler import CELERY_BEAT_SCHEDULE
    app.config["CELERY"]["beat_schedule"] = CELERY_BEAT_SCHEDULE

    db.init_app(app)
    cache.init_app(app)
    mail.init_app(app)

    with app.app_context():
        setup_initial_data(app)

    app.register_blueprint(auth)
    app.register_blueprint(user)
    app.register_blueprint(admin)
    app.register_blueprint(ppt_bp)
    app.register_blueprint(ml)

    return app

app = create_app()

celery_app = celery_init_app(app)
app.celery = celery_app

@app.route("/")
def home():
    return redirect("/home")

@app.route("/home",methods=['GET'])
def homepage():
    return render_template("landing.html")


if __name__ == "__main__":
    app.run(debug=True,port=5555)
