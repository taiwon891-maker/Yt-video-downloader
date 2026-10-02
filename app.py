import os
import json
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_admin_key_123'

YOUTUBE_API_KEY = "AIzaSyAj_ZB8TOSQViO5MYQAfYEnf-T9LlcuFks"
SETTINGS_FILE = "settings.json"

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        default_settings = {
            "adsterra_head_script": "<!-- Adsterra Head Script -->",
            "adsterra_banner_script": "<!-- Adsterra Banner Script -->",
            "custom_header_title": "YouTube Player & Downloader"
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_settings, f, ensure_ascii=False, indent=4)
        return default_settings
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "adsterra_head_script": "",
            "adsterra_banner_script": "",
            "custom_header_title": "YouTube Player & Downloader"
        }

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    settings = load_settings()
    return render_template('index.html', settings=settings)

@app.route('/search')
def search():
    query = request.args.get('q', 'Bangla hit songs')
    page_token = request.args.get('pageToken', '')
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=12&q={query}&type=video&pageToken={page_token}&key={YOUTUBE_API_KEY}"
    
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        videos = []
        for item in data.get('items', []):
            if 'snippet' in item and 'videoId' in item.get('id', {}):
                videos.append({
                    "title": item['snippet']['title'],
                    "thumbnail": item['snippet']['thumbnails']['high']['url'],
                    "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "videoId": item['id']['videoId'],
                    "channel": item['snippet']['channelTitle']
                })
        return jsonify({"videos": videos, "nextPageToken": data.get('nextPageToken', '')})
    except Exception as e:
        return jsonify({"videos": [], "nextPageToken": "", "error": str(e)})

@app.route('/get_proxy_stream')
def get_proxy_stream():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"status": "error"}), 400

    invidious_instances = [
        f"https://yewtu.be/api/v1/videos/{video_id}",
        f"https://invidious.nerdvpn.de/api/v1/videos/{video_id}"
    ]

    for instance_url in invidious_instances:
        try:
            r = requests.get(instance_url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                format_streams = data.get('formatStreams', [])
                if format_streams:
                    selected_stream = format_streams[-1].get('url')
                    return jsonify({"status": "success", "stream_url": selected_stream})
        except Exception:
            continue

    return jsonify({"status": "error", "message": "Stream extraction failed"})

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    
    if session.get('logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin'))
    settings = load_settings()
    return render_template('admin_dashboard.html', settings=settings)

@app.route('/admin/update_settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    head_script = request.form.get('adsterra_head_script', '')
    banner_script = request.form.get('adsterra_banner_script', '')
    title = request.form.get('custom_header_title', '')

    new_settings = {
        "adsterra_head_script": head_script,
        "adsterra_banner_script": banner_script,
        "custom_header_title": title
    }
    save_settings(new_settings)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
        
