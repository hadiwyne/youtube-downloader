import streamlit as st
import os
from youtube_dl_wrapper import download_youtube_video
import threading
import time
import glob

# --- Custom CSS for a modern look ---
st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%);
        }
        .stButton>button {
            background-color: #ff4b4b;
            color: white;
            border-radius: 8px;
            font-size: 18px;
            padding: 0.5em 2em;
            margin-top: 1em;
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

st.markdown("<h1 style='text-align:center; color:#ff4b4b;'>🎬 YouTube HD Video Downloader</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555;'>Download your favorite YouTube videos in high quality!</p>", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input('🔗 Paste YouTube URL here')
    with col2:
        quality = st.selectbox('Quality', ['Best (highest quality)', '1080p', '720p', '480p', 'audio'])
    st.markdown('</div>', unsafe_allow_html=True)

if 'download_thread' not in st.session_state:
    st.session_state.download_thread = None

progress_bar = st.progress(0.0)
status_text = st.empty()

if st.button('⬇️ Download'):
    if url:
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
                label="🎉 Click here to download your video",
                data=file_bytes,
                file_name=os.path.basename(latest_file),
                mime="video/mp4"  # or adjust based on file type
            )