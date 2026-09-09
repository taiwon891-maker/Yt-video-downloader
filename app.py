import os
from datetime import timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)

# ১. ফিক্সড সিক্রেট কি (যাতে সার্ভার রিস্টার্ট হলেও সেশন না ভাঙে)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my-permanent-fixed-secret-key-998877')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ২. লগইন সেশনের মেয়াদ ৩০ দিন পর্যন্ত বাড়ানো হলো
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

YOUTUBE_API_KEY = "AIzaSyAj_ZB8TOSQViO5MYQAfYEnf-T9LlcuFks"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- Auth Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('এই ইউজারনেমটি ইতোমধ্যে ব্যবহৃত হয়েছে।', 'danger')
            return redirect(url_for('register'))
            
        # Standard pbkdf2:sha256 হ্যাশিং
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        flash('রেজিস্ট্রেশন সফল হয়েছে! লগইন করুন।', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # ৩. remember=True দিলে ব্রাউজার সেশন সেভ থাকবে (বারবার লগইন লাগবে না)
            login_user(user, remember=True)
            return redirect(url_for('index'))
        else:
            flash('ভুল ইউজারনেম বা পাসওয়ার্ড!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Main App Routes ---

@app.route('/')
@login_required
def index():
    return render_template('index.html', username=current_user.username)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', 'Bangla hit songs')
    page_token = request.args.get('pageToken', '')
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=12&q={query}&type=video&pageToken={page_token}&key={YOUTUBE_API_KEY}"
    try:
        r = requests.get(url).json()
        videos = []
        for item in r.get('items', []):
            videos.append({
                "title": item['snippet']['title'],
                "thumbnail": item['snippet']['thumbnails']['high']['url'],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "videoId": item['id']['videoId']
            })
        return jsonify({"videos": videos, "nextPageToken": r.get('nextPageToken', '')})
    except Exception:
        return jsonify({"videos": [], "nextPageToken": ""})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    
