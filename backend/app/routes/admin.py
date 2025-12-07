from flask import Blueprint, request, jsonify, render_template, redirect, url_for

admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')