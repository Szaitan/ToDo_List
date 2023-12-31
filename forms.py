from flask_wtf import FlaskForm
from wtforms import SubmitField, EmailField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, NumberRange


class CreateRegisterForm(FlaskForm):
    login = StringField(name="Login:", validators=[DataRequired()])
    e_mail = EmailField(name="E-mail:", validators=[DataRequired(), Email()])
    password = StringField(name="Password:", validators=[DataRequired()])
    submit = SubmitField(name="Register", render_kw={'class': 'submit-custom'})


class CreateLoginForm(FlaskForm):
    e_mail = EmailField(name="E-mail:", validators=[DataRequired(), Email()])
    password = StringField(name="Password:", validators=[DataRequired()])
    submit = SubmitField(name="Login", render_kw={'class': 'submit-custom'})


class CreateAddListForm(FlaskForm):
    name = StringField(name="Create new list:", validators=[DataRequired()])
    submit = SubmitField(name="Add", render_kw={'class': 'add-list-custom'})


class CreateContentListForm(FlaskForm):
    content = StringField(name="Add task to your list:", validators=[DataRequired()])
    submit = SubmitField(name="Add", render_kw={'class': 'add-task-custom'})

