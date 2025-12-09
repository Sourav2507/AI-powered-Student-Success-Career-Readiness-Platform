from flask import Flask,redirect,render_template
from routes.auth import auth
from routes.user import user
from routes.admin import admin
from routes.ppt_gen import ppt_bp

app = Flask(__name__,
            template_folder='../../frontend/html',
            static_folder='../../frontend')

app.secret_key = "mentora_ai_secret_key"  

app.register_blueprint(auth)
app.register_blueprint(user)
app.register_blueprint(admin)
app.register_blueprint(ppt_bp)

@app.route("/")
def home():
    return redirect("/home")

@app.route("/home",methods=['GET'])
def homepage():
    return render_template("landing.html")


if __name__ == "__main__":
    app.run(debug=True,port=5555)
