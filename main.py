from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from forms import CreateRegisterForm, CreateLoginForm, CreateAddListForm, CreateContentListForm
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import email_validator
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from typing import List
import os
from functools import wraps


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('flask_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todolist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)

login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)

    user_lists: Mapped[List['ToDoList']] = relationship(back_populates='lists_user')
    user_list_content: Mapped[List['ListContent']] = relationship(back_populates='list_content_user')


class ToDoList(db.Model):
    __tablename__ = 'to_do_lists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    lists_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    lists_user: Mapped['User'] = relationship(back_populates='user_lists')

    to_do_list_content: Mapped[List['ListContent']] = relationship(back_populates='content_to_do_list')


class ListContent(db.Model):
    __tablename__ = 'list_contents'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String)

    content_to_do_list_id: Mapped[int] = mapped_column(ForeignKey('to_do_lists.id'))
    content_to_do_list: Mapped['ToDoList'] = relationship(back_populates='to_do_list_content')

    list_content_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    list_content_user: Mapped['User'] = relationship(back_populates='user_list_content')


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


@app.route('/')
def cover_page():
    db.create_all()
    return render_template('cover.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = CreateLoginForm()
    if form.validate_on_submit():
        user_to_check = db.session.query(User).filter_by(email=form.e_mail.data).first()
        if user_to_check is not None:
            if check_password_hash(user_to_check.password, form.password.data):
                login_user(user_to_check)
                return redirect(url_for('todo_page'))
            else:
                flash("Wrong Password. Try Again.")
                return redirect(url_for('login_page'))
        else:
            flash("This user does not exists in database. Try again or contact administrator.")
            return redirect(url_for('login_page'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    return redirect(url_for('cover_page'))


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = CreateRegisterForm()
    if form.validate_on_submit():
        if db.session.query(User).filter_by(email=form.e_mail.data).first() is None:
            # noinspection PyArgumentList
            user_to_add = User(login=form.login.data, email=form.e_mail.data,
                               password=generate_password_hash(form.password.data, salt_length=8))
            db.session.add(user_to_add)
            db.session.commit()
            login_user(user_to_add)
            return redirect(url_for('cover_page'))
        else:
            flash("This e-mail already exists in database. Please chose another one.")
            return redirect(url_for('register_page'))
    return render_template('register.html', form=form)


@app.route('/todo-list', methods=['GET', 'POST'])
def todo_page():
    list_with_lists = db.session.query(ToDoList).filter_by(lists_user_id=current_user.id).all()

    add_list_form = CreateAddListForm()
    content_of_list_form = CreateContentListForm()

    if add_list_form.validate_on_submit():
        new_list_to_add = ToDoList(name=add_list_form.name.data, lists_user_id=current_user.id)
        db.session.add(new_list_to_add)
        db.session.commit()
        return redirect(url_for('todo_page'))
    return render_template('todo.html', lists_data=list_with_lists, form=add_list_form,
                           content_form=content_of_list_form)


@app.route('/todo-list-display/<int:list_id>', methods=['GET', 'POST'])
def todo_page_display(list_id):
    try:
        list_to_check = db.session.query(ToDoList).filter_by(id=list_id).first()
        list_id_to_check = list_to_check.lists_user_id
    except AttributeError:
        return abort(403)
    except TypeError:
        return abort(403)
    else:
        if current_user.id == list_id_to_check:
            list_with_lists = db.session.query(ToDoList).filter_by(lists_user_id=current_user.id).all()
            content_of_list = db.session.query(ListContent).filter_by(content_to_do_list_id=list_id).all()

            add_list_form = CreateAddListForm()
            content_of_list_form = CreateContentListForm()

            if content_of_list_form.validate_on_submit():
                new_content_of_list = ListContent(content=content_of_list_form.content.data, content_to_do_list_id=list_id,
                                                  list_content_user_id=current_user.id)
                db.session.add(new_content_of_list)
                db.session.commit()
                return redirect(url_for('todo_page_display', list_id=list_id))

            if add_list_form.validate_on_submit():
                new_list_to_add = ToDoList(name=add_list_form.name.data, lists_user_id=current_user.id)
                db.session.add(new_list_to_add)
                db.session.commit()
                return redirect(url_for('todo_page_display', list_id=list_id))

            return render_template('tododisplay.html', lists_data=list_with_lists, content_of_list=content_of_list,
                                   form=add_list_form, list_id=list_id,
                                   content_form=content_of_list_form)
        else:
            return abort(403)


def user_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        content_id = request.args.get('content_id')
        list_id = request.args.get('list_id')
        # print(request.args.get('content_id'))
        print(request.args.get('list_id'))

        content_to_delete = db.session.query(ListContent).filter_by(id=content_id).first()
        list_to_delete = db.session.query(ToDoList).filter_by(id=list_id).first()
        # print(content_to_delete.list_content_user_id)
        print(list_to_delete.lists_user_id)
        if list_to_delete.lists_user_id == current_user.id:
            return f(*args, **kwargs)
        elif content_to_delete.list_content_user_id == current_user.id:
            return f(*args, **kwargs)
        else:
            return abort(403)

    return decorated_function


@app.route('/delete', methods=["GET", "POST"])
@user_only
def delete_list_content():
    content_to_delete = db.session.query(ListContent).filter_by(id=request.args.get('content_id')).first()
    db.session.delete(content_to_delete)
    db.session.commit()
    return redirect(url_for('todo_page_display', list_id=request.args.get('list_id')))


@app.route('/delete_list', methods=['GET', 'POST'])
@user_only
def delete_list():
    list_id = request.args.get('list_id')
    list_to_delete = db.session.query(ToDoList).filter_by(id=list_id).first()
    contents_to_delete = db.session.query(ListContent).filter_by(content_to_do_list_id=list_id).all()
    for content in contents_to_delete:
        db.session.delete(content)
        db.session.commit()
    db.session.delete(list_to_delete)
    db.session.commit()

    return redirect(url_for('todo_page'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
