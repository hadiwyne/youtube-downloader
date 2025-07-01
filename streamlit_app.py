import streamlit as st
import os
from youtube_dl_wrapper import download_youtube_video
import threading
import time
import glob
import youtube_dl

st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%);
        }
        .stButton>button {
            background-color: #ff4b4b;
            color: white !important;
            border-radius: 8px;
            font-size: 18px;
            padding: 0.5em 2em;
            margin-top: 1em;
            transition: box-shadow 0.2s, transform 0.2s, background 0.2s, color 0.2s;
            box-shadow: 0 2px 8px rgba(255,75,75,0.08);
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #ff4b4b 60%, #ff8888 100%);
            box-shadow: 0 8px 24px rgba(255,75,75,0.18);
            transform: translateY(-4px) scale(1.04);
            filter: brightness(1.08);
            color: white !important;
        }
        .stTextInput>div>div>input {
            border-radius: 8px;
        }
        .stSelectbox>div>div>div {
            border-radius: 8px;
        }
        .status-success {
            color: #27ae60;
            font-weight: bold;
        }
        .status-error {
            color: #e74c3c;
            font-weight: bold;
        }
        .status-idle, .status-starting {
            color: #2980b9;
            font-weight: bold;
        }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 16px rgba(0,0,0,0.07);
            padding: 2em 2em 1em 2em;
            margin-bottom: 2em;
        }
        /* Remove extra Streamlit block container padding */
        section.main > div { padding-top: 0rem; }
    </style>
""", unsafe_allow_html=True)

# Shared state for progress
progress_state = {
    'percent': 0.0,
    'status': 'idle',
    'message': ''
}

def threaded_download(url, quality, output_dir):
    progress_state['status'] = 'starting'
    try:
        download_youtube_video(url, quality=quality, output_path=output_dir)
        progress_state['status'] = 'Finished'
        progress_state['message'] = '✅ Download complete.'
        progress_state['percent'] = 1.0
    except Exception as e:
        progress_state['status'] = 'error'
        progress_state['message'] = f"❌ {str(e)}"
        progress_state['percent'] = 0.0

def get_latest_file(folder):
    files = glob.glob(os.path.join(folder, "*"))
    if not files:
        return None
    return max(files, key=os.path.getctime)

def get_video_metadata(url):
    ydl_opts = {'quiet': True, 'skip_download': True}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "duration": info.get("duration"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "upload_date": info.get("upload_date"),
                "description": info.get("description"),
                "thumbnail": info.get("thumbnail"),
            }
        except Exception as e:
            return {"error": str(e)}

st.markdown("<h1 style='text-align:center; color:#ff4b4b;'>🎬 YouTube HD Video Downloader</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555;'>Download your favorite YouTube videos in high quality!</p>", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input('🔗 Paste YouTube URL here', key="url_input")
    with col2:
        quality = st.selectbox('Quality', ['Best (highest quality)', '1080p', '720p', '480p', 'audio'])
    st.markdown('</div>', unsafe_allow_html=True)

if 'download_thread' not in st.session_state:
    st.session_state.download_thread = None

progress_bar = st.progress(0.0)
status_text = st.empty()

# Show metadata and start download on button click
if st.button('Download'):
    if url:
        # Show metadata
        with st.spinner("Fetching video metadata..."):
            meta = get_video_metadata(url)
        if meta.get("error"):
            st.error(f"Could not fetch metadata: {meta['error']}")
        else:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                cols = st.columns([1, 3])
                with cols[0]:
                    if meta.get("thumbnail"):
                        st.image(meta["thumbnail"], width=120)
                with cols[1]:
                    st.markdown(f"**Title:** {meta.get('title', 'N/A')}")
                    st.markdown(f"**Uploader:** {meta.get('uploader', 'N/A')}")
                    st.markdown(f"**Duration:** {meta.get('duration', 'N/A')} seconds")
                    st.markdown(f"**Views:** {meta.get('view_count', 'N/A')}")
                    st.markdown(f"**Likes:** {meta.get('like_count', 'N/A')}")
                    st.markdown(f"**Upload Date:** {meta.get('upload_date', 'N/A')}")
                st.markdown('</div>', unsafe_allow_html=True)
        # Start download
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        os.makedirs(output_dir, exist_ok=True)
        progress_state['percent'] = 0.0
        progress_state['status'] = 'starting'
        progress_state['message'] = ''
        thread = threading.Thread(target=threaded_download, args=(url, quality, output_dir))
        thread.start()
        st.session_state.download_thread = thread
    else:
        st.warning('⚠️ Please enter a valid YouTube URL.')

# Poll progress
if st.session_state.get('download_thread') is not None:
    while st.session_state.download_thread and st.session_state.download_thread.is_alive() or progress_state['status'] in ['downloading', 'starting']:
        progress_bar.progress(progress_state['percent'])
        status = progress_state['status']
        if status == 'Finished':
            status_html = f"<span class='status-success'>{progress_state['message']}</span>"
        elif status == 'error':
            status_html = f"<span class='status-error'>{progress_state['message']}</span>"
        else:
            status_html = f"<span class='status-idle'>{progress_state['status'].capitalize()}...</span>"
        status_text.markdown(status_html, unsafe_allow_html=True)
        time.sleep(0.5)
    progress_bar.progress(progress_state['percent'])
    status = progress_state['status']
    if status == 'Finished':
        status_html = f"<span class='status-success'>{progress_state['message']}</span>"
    elif status == 'error':
        status_html = f"<span class='status-error'>{progress_state['message']}</span>"
    else:
        status_html = f"<span class='status-idle'>{progress_state['status'].capitalize()}...</span>"
    status_text.markdown(status_html, unsafe_allow_html=True)
    st.session_state.download_thread = None

    # If download finished, offer download button
    if progress_state['status'] == 'Finished':
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        latest_file = get_latest_file(output_dir)
        if latest_file:
            with open(latest_file, "rb") as f:
                file_bytes = f.read()
            st.download_button(
                label="Click here to download your video",
                data=file_bytes,
                file_name=os.path.basename(latest_file),
                mime="video/mp4" 
            )