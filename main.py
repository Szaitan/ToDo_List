from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from forms import CreateRegisterForm, CreateLoginForm
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import email_validator
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('flask_secret_key')
Bootstrap(app)

# login_manager = LoginManager()
# login_manager.init_app(app)


@app.route('/')
def cover_page():
    return render_template('cover.html')


@app.route('/login')
def login_page():
    form = CreateLoginForm()
    return render_template('login.html', form=form)


@app.route('/register')
def register_page():
    form = CreateRegisterForm()
    return render_template('register.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)

