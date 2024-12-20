from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import login_user, LoginManager, current_user, logout_user,login_required
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from models import db,User,BlogPost,Comments
from forms import CreatePostForm,RegisterForm,LoginForm,CommentForm
import hashlib



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

#Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app) 
login_manager.login_view = 'login'

# CREATE DATABASE
# class Base(DeclarativeBase):
#     pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///post2.db'
db.init_app(app)



# function to generate gravatar images
@app.context_processor
def utility_functions(): 
    def gravatar_url(email, size=100):
        """
        Generate a Gravatar URL for the given email.
        """
        email = email.strip().lower()
        hash_email = hashlib.md5(email.encode('utf-8')).hexdigest()
        # print(f"Email: {email}, Hash: {hash_email}")
        return f"https://www.gravatar.com/avatar/{hash_email}?s={size}&d=identicon"
    return dict(gravatar_url=gravatar_url)

# with app.app_context():
#     db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User,int(user_id))

# admin only decorator
def admin_only(func):
    @wraps(func)
    @login_required
    def wrapper(*args,**kwargs):
        if current_user.id != 1:
            return abort(403)
        return func(*args,**kwargs)
    return wrapper



#Use Werkzeug to hash the user's password when creating a new user.
# register route
@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data,salt_length=8)
        email = form.email.data
        username = form.name.data
        email_exist = db.session.execute(db.select(User).where(User.email == email)).scalars().first()
        if email_exist:
            flash('Email already is registered Log in instead','error')
            return redirect(url_for('login'))

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        print("success")
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))

    return render_template("register.html",form=form)

#login route
#Retrieve a user from the database based on their email. 
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db.session.execute(db.select(User).where(User.email == email)).scalars().first()
        if user:
            if check_password_hash(user.password,password):
                login_user(user)
                flash("Logged in successfully",'success')
                return redirect(url_for('get_all_posts'))
            else:
                flash('Invalid password','error')
                return redirect(url_for('login'))
        else:
            flash('Email not found,Register first','error')
            return redirect(url_for('register'))
    return render_template("login.html",form=form)

# logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

# homepage route
@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)

# blog post route
#Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>",methods=['GET','POST'])
def show_post(post_id):
    form = CommentForm()
    requested_post = db.get_or_404(BlogPost, post_id)
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to login to comment','error')
            return redirect(url_for('login'))
        comment = form.comment.data
        if comment:
            new_comment = Comments(
                text=comment,
                author_id=current_user.id,
                blog_post_id=post_id

            )
            db.session.add(new_comment)
            db.session.commit()
            print("comment added")
            return redirect(url_for("show_post",post_id=new_comment.blog_post_id))
    return render_template("post.html", post=requested_post,form=form)



# Adding a new post ,only admin can add a new post
@app.route("/new-post", methods=["GET", "POST"])

@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,current_user=current_user)


#Edit a post route,only admin can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])

@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True,current_user=current_user)


# Delete a post route,only admin can delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5002)
