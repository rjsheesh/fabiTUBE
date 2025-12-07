import os
import uuid
import time
import threading
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

# ডাউনলোড ফোল্ডার
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ফাইল ডিলিট করার ফাংশন (৩ মিনিট পর ডিলিট হবে)
def delete_file_delay(path, delay=180):
    time.sleep(delay)
    try:
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted temp file: {path}")
    except Exception as e:
        print(f"Error deleting file: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/yt-download', methods=['POST'])
def download_video():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({'success': False, 'message': 'দয়া করে ইউটিউব লিংক দিন!'})

    try:
        # ইউনিক নাম জেনারেট করা
        video_id = str(uuid.uuid4())
        output_filename = f"{DOWNLOAD_FOLDER}/{video_id}.%(ext)s"

        # yt-dlp অপশন (সবচেয়ে ভালো কোয়ালিটি যা অডিও সহ আছে)
        ydl_opts = {
            'outtmpl': output_filename,
            'format': 'best', # 1080p নামাতে গেলে ffmpeg লাগবে, তাই 'best' (720p) সেফ
            'noplaylist': True,
            'cookiefile': 'cookies.txt',  # <--- এই নতুন লাইনটা যোগ কর
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            final_filename = os.path.basename(filename)

            return jsonify({
                'success': True,
                'title': info.get('title', 'YouTube Video'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string'),
                'download_url': f"/download/{final_filename}"
            })

    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'message': 'ভিডিও নামানো যাচ্ছে না। লিংক বা সার্ভার সমস্যা।'})

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    try:
        # ফাইল পাঠানোর পর ব্যাকগ্রাউন্ডে ডিলিট শিডিউল করা হলো
        threading.Thread(target=delete_file_delay, args=(file_path,)).start()
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"File not found or expired."

if __name__ == '__main__':

    app.run(debug=True, port=5000)
