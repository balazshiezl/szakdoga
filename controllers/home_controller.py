from flask import Blueprint, render_template
from models.db import get_connection


home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    return render_template('index.html')
