from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SubmitField, FileField,  TextAreaField, SelectField, MultipleFileField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from flask_wtf.file import FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    identifier = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SightingForm(FlaskForm):
    species = StringField('Species', validators=[DataRequired(), Length(max=100)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    date = DateField('Date', validators=[DataRequired()])
    observation_notes = TextAreaField('Observation Notes')
    image = FileField('Upload Images')
    videos = FileField('Upload Videos')
    submit = SubmitField('Submit')


class UserProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_image = FileField('Profile Image')
    submit = SubmitField('Update Profile')
