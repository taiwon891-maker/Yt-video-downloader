import os
from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests

app = Flask(__name__)

# ইউটিউব API Key (আপনার আসল API Key ব্যবহার করুন)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "AIzaSyAj_ZB8TOSQViO5MYQAfYEnf-T9LlcuFks")

@app.route('/')
def index():
    return render_template('index.html')

# ইউটিউব ভিডিও সার্চ
@app.route('/search')
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
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        return jsonify({"videos": videos, "nextPageToken": r.get('nextPageToken', '')})
    except Exception as e:
        return jsonify({"videos": [], "nextPageToken": ""})

# ভিডিও ইনফো ও প্লে ব্যাক লিঙ্ক
@app.route('/get_info', methods=['POST'])
def get_info():
    video_url = request.form.get('url')
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get('formats', [])
            play_url = next((f['url'] for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4'), info.get('url'))
            return jsonify({"title": info['title'], "video_url": play_url, "url": video_url})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# সার্ভারে সেভ না করে সরাসরি ব্রাউজারে ডাইরেক্ট স্ট্রিম ডাউনলোড
@app.route('/download')
def download():
    video_url = request.args.get('url')
    quality = request.args.get('quality', '720p')

    ydl_opts = {
        'quiet': True,
        'format': 'best' if quality == 'mp3' else f'best[height<={quality.replace("p","")}][ext=mp4]/best'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            media_url = info.get('url')
            title = info.get('title', 'video').replace(' ', '_')
            ext = 'mp3' if quality == 'mp3' else 'mp4'

            # সরাসরি ফাইল টি স্ট্রিম করে ইউজারকে পাঠানো
            req = requests.get(media_url, stream=True)
            return Response(
                req.iter_content(chunk_size=1024*1024),
                content_type=req.headers.get('content-type'),
                headers={"Content-Disposition": f"attachment; filename={title}.{ext}"}
            )
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
