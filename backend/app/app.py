from flask import Flask,redirect,render_template
from backend.app.config.config import LocalDevelopmentConfig
from backend.app.config.create_initial_data import setup_initial_data
from backend.app.config.extensions import db,cache,mail
from backend.app.async_celery.celery_setup import celery_init_app
from backend.app.routes.auth import auth
from backend.app.routes.user import user
from backend.app.routes.admin import admin
from backend.app.routes.ppt_gen import ppt_bp
from backend.app.routes.ml import ml
from flask_migrate import Migrate


def create_app():
    app = Flask(__name__,
                template_folder='../../frontend/html',
                static_folder='../../frontend')
    
    app.config.from_object(LocalDevelopmentConfig)
    from backend.app.async_celery.celery_scheduler import CELERY_BEAT_SCHEDULE
    app.config["CELERY"]["beat_schedule"] = CELERY_BEAT_SCHEDULE

    db.init_app(app)
    migrate = Migrate(app, db)

    cache.init_app(app)
    mail.init_app(app)

    with app.app_context():
        import backend.app.model
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
