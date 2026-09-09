import os
from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import requests

app = Flask(__name__)

YOUTUBE_API_KEY = "AIzaSyAj_ZB8TOSQViO5MYQAfYEnf-T9LlcuFks"

@app.route('/')
def index():
    return render_template('index.html')

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
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "videoId": item['id']['videoId']
            })
        return jsonify({"videos": videos, "nextPageToken": r.get('nextPageToken', '')})
    except Exception as e:
        return jsonify({"videos": [], "nextPageToken": ""})

# yt-dlp Options সহ লিঙ্ক পাওয়ার রুট
@app.route('/get_info', methods=['POST'])
def get_info():
    video_url = request.form.get('url')
    
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'format': 'best',
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify({
                "title": info.get('title', 'Video'),
                "download_url": info.get('url'),
                "id": info.get('id')
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ডাউনলোড অপশন: সরাসরি মেমোরি থেকে রেসপন্স পাঠানো
@app.route('/download')
def download():
    video_url = request.args.get('url')
    quality = request.args.get('quality', '720p')

    ydl_opts = {
        'quiet': True,
        'format': 'best' if quality == 'mp3' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_url = info.get('url')
            title = info.get('title', 'download').replace(' ', '_')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            }
            req = requests.get(direct_url, headers=headers, stream=True)
            
            return Response(
                req.iter_content(chunk_size=1024*1024),
                content_type=req.headers.get('content-type', 'application/octet-stream'),
                headers={"Content-Disposition": f"attachment; filename={title}.mp4"}
            )
    except Exception as e:
        return f"Download Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    
