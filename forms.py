from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField,TextAreaField
from wtforms.validators import DataRequired, URL,ValidationError,EqualTo
from flask_ckeditor import CKEditorField
from models import User


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


#Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired()])
    name = StringField("Name",validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message="Passwords must match!")
    ])
    submit = SubmitField("Register")

    def validate_name(self,field):
        existing_user = User.query.filter_by(username=field.data).first()
        if existing_user:
            raise ValidationError("Username already exists. Please choose a different username.")

# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")  

# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment = TextAreaField("Leave a comment...")
    submit = SubmitField("Submit")
