from flask import Blueprint, jsonify, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, EmailCaptchaModel
from database import db, mail
from flask_login import login_user, login_required, logout_user, current_user
import logging
import random
import string
from flask_mail import Message

auth = Blueprint('auth', __name__)
logger = logging.getLogger("fileLogger")


@auth.route('/')
def login():
    # Render login page
    return render_template('login.html')

@auth.route('/captcha/email', methods=['GET', 'POST'])
def get_email_captcha():
    # Endpoint to generate and send email verification code
    email = request.args.get("email")
    source = string.digits * 4
    captcha = random.sample(source, 4)
    captcha = "".join(captcha)
    user = User.query.filter_by(email=email).first()

    # Send email with verification code
    message = Message(subject="JobHunt---Verification Code", recipients=[email],
                      body=f"Verification Code:{captcha}")
    mail.send(message)

    # Store verification code in the database
    email_captcha = EmailCaptchaModel(email=email, captcha=captcha)
    db.session.add(email_captcha)
    db.session.commit()
    return jsonify({"code": 200, "message": "success", "data": None})





@auth.route('/login', methods=['POST'])
def login_post():
    # Process login form data
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth.login'))
    logger.info(f"{email} login success ! ")
    login_user(user, remember=remember)
    return redirect(url_for('main.index'))


@auth.route('/register')
def register():
    # Render registration page
    return render_template('register.html')


@auth.route('/register', methods=['POST'])
def register_post():
    # Process registration form data
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    user = User.query.filter_by(email=email).first()
    print()
    if user:
        # If a user with the same email already exists, redirect to the registration page
        flash('Email address already exists')
        return redirect(url_for('auth.register'))
    # Create a new user and add to the database
    new_user = User(email=email, name=name, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    # Logout the user and redirect to the index page
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/forgot-password')
def forgot_password():
    # Render forgot password page
    return render_template('forgot-password.html')


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_post():
    # Process forgot password form data
    email = request.form.get("email")
    password = request.form.get("password")
    code = request.form.get("code")

    # Check if the entered verification code matches the stored one
    captcha_model = EmailCaptchaModel.query.filter_by(email=email, captcha=code).first()
    user = User.query.filter_by(email=email).first()
    if not captcha_model:
        flash('Wrong Verification Code!', "forgot")
        return redirect(url_for('auth.forgot_password'))
    if not user:
        flash('No User Found for This Email!', "forgot")
        return redirect(url_for('auth.forgot_password'))
    else:
        # Reset the user's password
        user.password = generate_password_hash(password)
        db.session.commit()
        logger.info(f"{email} reset password success !")
        return redirect('/login')


@auth.route('/change-password')
def change_password():
    # Render change password page
    return render_template('change-password.html')


@auth.route('/change-password', methods=['POST'])
def change_password_post():
    # Process change password form data
    password = request.form.get('password')
    newPassword = request.form.get('newPassword')
    confirmPassword = request.form.get('confirmPassword')
    logger.info(f"{current_user.id} try to update password")

    if confirmPassword != newPassword:
        flash("confirm password not match new password!")
        return redirect(url_for('auth.change_password'))
    if not check_password_hash(current_user.password, password):
        flash('Please check your password and try again.')
        return redirect(url_for('auth.change_password'))

    # Update the user's password
    userId = current_user.id
    user = User.query.filter_by(id=userId).first()
    user.password = generate_password_hash(newPassword)
    db.session.commit()

    # Logout the user after changing the password
    logout_user()
    return redirect('/login')
