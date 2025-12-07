from flask import Blueprint, request, jsonify, render_template, redirect, url_for,Response

auth = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON provided"}), 400

        username = data.get('username')
        password = data.get('password')

        # Example authentication logic
        if username == 'admin' and password == 'password':
            return jsonify({"message": "Login successful",
                            'username': username,
                            'role': 'admin ',
                            'password':password}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401