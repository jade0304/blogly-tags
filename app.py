import re
from flask import Flask, request, render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Post, Tag, PostTag

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///blogly'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "abc123"
# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app)
db.create_all()



@app.route('/')
def root():
    """Show recent list of posts, most-recent first."""

    posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template("posts/homepage_post.html", posts=posts)


@app.errorhandler(404)
def page_not_found(e):
    """Show 404 NOT FOUND page."""

    return render_template('404.html'), 404


@app.route('/users')
def user_listing():
    users = User.query.order_by(User.last_name, User.first_name).all()
    return render_template('listing.html', users=users)

@app.route('/users/new', methods=["GET"])
def users_new_form():
    """Show a form to create a new user"""

    return render_template('create_user.html')

@app.route('/users/new', methods=['POST'])
def create_new_user():
    """submit the form for creating a new user"""
    fname = request.form['first_name']
    lname = request.form['last_name']
    img = request.form['img_url'] or None
    
    new_user = User(first_name=fname, last_name=lname, image_url=img)
    db.session.add(new_user)
    db.session.commit()
    return redirect('/users')

@app.route('/users/<int:user_id>')
def user_detail(user_id):
    """show detail about a specific user"""
    user = User.query.get_or_404(user_id)
    return render_template('user_detail.html', user=user)


@app.route('/users/<int:user_id>/edit')
def edit_user(user_id):
    """Show form to edit existing user"""
    user = User.query.get_or_404(user_id)

    return render_template('edit_user.html', user=user)

@app.route('/users/<int:user_id>/edit', methods=['POST'])
def update_user(user_id):
    """submit the form for updating user info"""
    user = User.query.get_or_404(user_id)

    fname = request.form['first_name']
    lname = request.form['last_name']
    img = request.form['img_url']
    
    user.first_name = fname
    user.last_name = lname
    user.image_url = img

    db.session.add(user)
    db.session.commit()
    return redirect('/users')

@app.route('/users/<user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete an existing user."""
    user = User.query.get_or_404(user_id)
    
    db.session.delete(user)
    db.session.commit()
    return redirect('/users')

# ****************************************************************
# POSTS

@app.route('/users/<int:user_id>/posts/new')
def show_post_form(user_id):
    """Show post for that user."""
    user = User.query.get_or_404(user_id)
    tags = Tag.query.all()
    return render_template('posts/add_post.html', user=user, tags=tags)


@app.route('/users/<int:user_id>/posts/new', methods=["POST"])
def handle_add_form(user_id):
    """handle form submission"""
    
    user = User.query.get_or_404(user_id)
    tag_ids = [int(num) for num in request.form.getlist("tags")]
    tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

    new_post = Post(title=request.form['title'],
                    content=request.form['content'],
                    user=user,
                    tags=tags)
    
    db.session.add(new_post)
    db.session.commit()

    flash(f"Post '{new_post.title}' added.")
    return redirect(f'/users/{user_id}')
    
    
@app.route('/posts/<int:post_id>')
def show_post(post_id):
    """show post with edit and delete button"""
    
    post = Post.query.get_or_404(post_id)
    return render_template('posts/show_post.html', post=post)
        
    
@app.route('/posts/<int:post_id>/edit')
def edit_post(post_id):
    """show form to edit a post, and to cancle"""
    
    post = Post.query.get_or_404(post_id)
    tags = Tag.query.all()

    return render_template('edit_post.html', post=post, tags=tags)

      
@app.route('/posts/<int:post_id>/edit', methods=["POST"])
def handle_edit_post(post_id):
    """handle editing of a post. Redirect back to post view"""
    
    post = Post.query.get_or_404(post_id)
    post.title = request.form['title']
    post.content = request.form['content']
    
    tag_ids = [int(num) for num in request.form.getlist("tags")]
    post.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
    
    db.session.add(post)
    db.session.commit()
    flash(f"Post '{post.title}' edited.")
    
    return redirect(f'/users/{post.user_id}')


@app.route('/posts/<int:post_id>/delete', methods=["POST"])
def delete_post(post_id):
    """Handle form submission for deleting existing post"""
    
    post = Post.query.get_or_404(post_id)
    
    db.session.delete(post)
    db.session.commit()
    
    flash(f"Post '{post.title} deleted'")
    return redirect(f'/users/{post.user_id}')

# ****************************************************************
# Tags


@app.route('/tags')
def tags_list():
    """List all tags, with links to the tag detail page."""
    tags = Tag.query.all()
    return render_template('tags/all_tags.html', tags=tags)


@app.route('/tags/new')
def new_tag_form():
    """Show form to add a new tag"""

    posts = Post.query.all()
    return render_template('tags/new_tag.html', posts=posts)


@app.route('/tags/new', methods=["POST"])
def new_tag():
    """Process add form, adds tag, and redirect to tag list"""

    post_ids = [int(num) for num in request.form.getlist("posts")]
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    new_tag = Tag(name=request.form['name'], posts=posts)

    db.session.add(new_tag)
    db.session.commit()
    flash(f"Tag '{new_tag.name}' added.")

    return redirect("/tags")

@app.route('/tags/<int:tag_id>')
def show_detail(tag_id):
    """Show detail about a tag"""
    
    tags = Tag.query.get_or_404(tag_id)
    return render_template('tags/detail_tag.html', tag=tags)


@app.route('/tags/<int:tag_id>/edit')
def edit_form(tag_id):
    """Show edit form for tag"""
    
    posts = Post.query.all()
    tag = Tag.query.get_or_404(tag_id)
    return render_template('tags/edit_tag.html', tag=tag, posts=posts)


@app.route('/tags/<int:tag_id>/edit', methods=["POST"])
def edit_tags(tag_id):
    """Process edit form, edit tag, and redirects to the tags list"""
    
    tag = Tag.query.get_or_404(tag_id)
    tag.name = request.form['name']
    post_ids = [int(num) for num in request.form.getlist("posts")]
    tag.posts = Post.query.filter(Post.id.in_(post_ids)).all()
    
    db.session.add(tag)
    db.session.commit()
    flash(f"Tag '{tag.name}' edited.")

    return redirect("/tags")


@app.route('/tags/<int:tag_id>/delete', methods=["POST"])
def delete_tags(tag_id):
    """Delete existing tag"""
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash(f"Tag '{tag.name}' deleted.")

    
    return redirect('/tags')