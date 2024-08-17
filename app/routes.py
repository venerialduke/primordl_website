from openai import OpenAI
import os
from flask import render_template, flash, redirect, url_for, request
from app import app, db, login
from app.models import User, Character
#from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required, LoginManager

# Set your OpenAI API key
client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],  # this is also the default, it can be omitted
)

print(f"API Key: {os.environ['OPENAI_API_KEY']}")

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    characters = Character.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', characters=characters)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create_character', methods=['GET', 'POST'])
@login_required
def create_character():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        character = Character(name=name, description=description, user_id=current_user.id)
        db.session.add(character)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('create_character.html')




@app.route('/generate_story')
@login_required
def generate_story():
    # Gather all characters for the current user
    characters = Character.query.filter_by(user_id=current_user.id).all()

    # Create a context string with all character names and descriptions
    context = "The following characters are involved in this story:\n"
    for character in characters:
        context += f"Name: {character.name}, Description: {character.description}\n"

    # Generate the story using the correct OpenAI method
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use "gpt-4" if you're using GPT-4
        messages=[
            {"role": "system", "content": "You are a creative story writer."},
            {"role": "user", "content": f"{context} Write a short story involving these characters."}
        ]
    )

    #story = response['choices'][0]['message']['content'].strip()
    story = response.choices[0].message.content

    return render_template('story.html', story=story)