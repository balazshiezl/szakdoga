from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_user, logout_user
from models.user_model import create_user, get_user_by_email, email_exists
from utils.hashing import hash_password, check_password
from models.user_model import User
from models.db import get_connection


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm = request.form.get('confirmPassword')

    if not all([name, email, password]):
        flash("Minden mező kitöltése kötelező", 'error')
        return redirect(url_for('auth.register'))

    if password != confirm:
        flash("A jelszavak nem egyeznek", 'error')
        return redirect(url_for('auth.register'))

    if email_exists(email):
        flash("Ez az email cím már regisztrálva van", 'error')
        return redirect(url_for('auth.register'))

    create_user(name, email, hash_password(password))
    flash("Sikeres regisztráció!", 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email')
    password = request.form.get('password')

    user_data = get_user_by_email(email)
    if user_data and check_password(user_data.password, password):
        login_user(user_data)
        return redirect(url_for('user.dashboard'))

    flash("Hibás email vagy jelszó", 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
