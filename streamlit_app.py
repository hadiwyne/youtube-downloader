import streamlit as st
import os
from youtube_dl_wrapper import download_youtube_video
import threading
import time
import glob

# Shared state for progress
progress_state = {
    'percent': 0.0,
    'status': 'idle',
    'message': ''
}

def threaded_download(url, quality, output_dir):
    progress_state['status'] = 'starting'
    try:
        # download_youtube_video does not support progress_callback, so we just call it
        download_youtube_video(url, quality=quality, output_path=output_dir)
        progress_state['status'] = 'Finished'
        progress_state['message'] = 'Download complete.'
        progress_state['percent'] = 1.0
    except Exception as e:
        progress_state['status'] = 'error'
        progress_state['message'] = str(e)
        progress_state['percent'] = 0.0

def get_latest_file(folder):
    files = glob.glob(os.path.join(folder, "*"))
    if not files:
        return None
    return max(files, key=os.path.getctime)

st.title('YouTube HD Video Downloader')

url = st.text_input('YouTube URL')
quality = st.selectbox('Select Quality/Format', ['Best (highest quality)', '1080p', '720p', '480p', 'audio'])

if 'download_thread' not in st.session_state:
    st.session_state.download_thread = None

progress_bar = st.progress(0.0)
status_text = st.empty()

if st.button('Download'):
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
        st.warning('Please enter a valid YouTube URL.')

# Poll progress
if st.session_state.get('download_thread') is not None:
    while st.session_state.download_thread and st.session_state.download_thread.is_alive() or progress_state['status'] in ['downloading', 'starting']:
        progress_bar.progress(progress_state['percent'])
        status_text.text(f"Status: {progress_state['status']} | {progress_state['message']}")
        time.sleep(0.5)
    progress_bar.progress(progress_state['percent'])
    status_text.text(f"Status: {progress_state['status']} | {progress_state['message']}")
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
                mime="video/mp4"  # or adjust based on file type
            )