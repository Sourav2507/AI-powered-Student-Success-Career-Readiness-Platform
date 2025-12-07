from flask import Blueprint, request, jsonify, render_template, redirect, url_for

user = Blueprint('user', __name__, template_folder='templates', url_prefix='/user')

@user.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')