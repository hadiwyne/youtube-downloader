import subprocess
import os
import argparse
from yt_dlp import YoutubeDL

def get_format_code(quality):
    if quality == "1080p":
        return "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    elif quality == "720p":
        return "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif quality == "480p":
        return "bestvideo[height<=480]+bestaudio/best[height<=480]"
    elif quality == "audio":
        return "bestaudio"
    else:
        return "bv*+ba/b"

def download_youtube_video(url, quality="best", output_path="downloads", progress_state=None):
    os.makedirs(output_path, exist_ok=True)
    format_code = get_format_code(quality)

    def progress_hook(d):
        if progress_state is not None:
            if d['status'] == 'downloading':
                try:
                    percent = float(d.get('_percent_str', '0').strip('%'))
                except Exception:
                    percent = 0.0
                progress_state['percent'] = percent / 100.0
                progress_state['status'] = 'downloading'
                progress_state['message'] = f"Speed: {d.get('_speed_str', 'N/A')} | ETA: {d.get('_eta_str', 'N/A')}"
            elif d['status'] == 'finished':
                progress_state['percent'] = 1.0
                progress_state['status'] = 'finishing'
                progress_state['message'] = 'Merging and finalizing...'

    ydl_opts = {
        'format': format_code,
        'merge_output_format': 'mp4',
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
    }
    try:
        if progress_state is not None:
            progress_state.update({
                'percent': 0.0,
                'status': 'starting',
                'message': 'Initializing download...'
            })
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if progress_state is not None:
            progress_state.update({
                'status': 'finished',
                'message': 'Download completed successfully!'
            })
    except Exception as e:
        if progress_state is not None:
            progress_state.update({
                'status': 'error',
                'message': f'Error: {str(e)}'
            })
        raise

def main():
    parser = argparse.ArgumentParser(description="YouTube HD Video Downloader with yt-dlp and FFmpeg")
    parser.add_argument('url', nargs='?', help='YouTube video URL')
    parser.add_argument('-o', '--output', default='downloads', help='Output directory')
    parser.add_argument('-q', '--quality', default='best', help='Video quality')
    args = parser.parse_args()

    if not args.url:
        args.url = input("Enter YouTube URL: ")
    download_youtube_video(args.url, args.quality, args.output)

if __name__ == "__main__":
    main() 