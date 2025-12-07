from flask import Flask,redirect
from routes.auth import auth
from routes.user import user
from routes.admin import admin

app = Flask(__name__,
            template_folder='../../frontend/html',
            static_folder='../../frontend')

app.register_blueprint(auth)
app.register_blueprint(user)
app.register_blueprint(admin)

@app.route("/")
def home():
    return redirect("/home")

@app.route("/home",methods=['GET'])
def homepage():
    return "Welcome to homepage !!"


if __name__ == "__main__":
    app.run(debug=True,port=5555)
