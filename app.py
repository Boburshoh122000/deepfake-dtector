import streamlit as st
import os
import tempfile
import urllib.request
from urllib.parse import urlparse
from realitydefender import RealityDefender
import nest_asyncio

# Fix: Allow nested event loops for Streamlit + RealityDefender
nest_asyncio.apply()

# Retrieve API Key from environment or hardcoded (for demo purposes)
# Ideally, users should input this in the UI or set it securely.
DEFAULT_API_KEY = os.getenv("REALITY_DEFENDER_API_KEY", "rd_695514645a00b6d0_5db2bc1347c11b81fb4b21006ee0574e")

# UI Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🛡️ Deepfake Detector")
    st.caption("Powered by Reality Defender")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Settings")
    api_key_input = st.text_input("API Key", value=DEFAULT_API_KEY, type="password")
    
    st.divider()
    st.info("""
    **How it works:**
    1. Upload a file or paste a URL.
    2. AI scans for manipulation traces.
    3. View the authenticity score.
    """)

# Caching the client initialization to improve performance
@st.cache_resource
def get_client(api_key):
    return RealityDefender(api_key=api_key)

def is_url(path):
    return path.startswith('http://') or path.startswith('https://')

def download_file(url):
    try:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or 'downloaded_file'
        suffix = os.path.splitext(filename)[1]
        if not suffix:
            suffix = ".jpg" # Default fallback
            
        # Create a temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(temp_fd)
        
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'}
        )
        with urllib.request.urlopen(req) as response, open(temp_path, 'wb') as out_file:
            # Chunked writing for memory efficiency
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                out_file.write(chunk)
        return temp_path
    except Exception as e:
        st.error(f"Failed to download URL: {e}")
        return None

def scan_file(file_path, key):
    try:
        client = get_client(key)
        # st.status will handle the spinner now
        result = client.detect_file(file_path)
        return result
    except Exception as e:
        st.error(f"Error during scan: {e}")
        return None

# Initialize session state for results if not present
if 'scan_result' not in st.session_state:
    st.session_state.scan_result = None
if 'scanned_file_name' not in st.session_state:
    st.session_state.scanned_file_name = None

# Main Content
st.markdown("### 1. Choose Input Source")
tab1, tab2 = st.tabs(["📂 **File Upload**", "🔗 **URL Input**"])

file_to_scan = None
temp_file_path = None # Track local temp files for immediate logic

with tab1:
    uploaded_file = st.file_uploader("Drop an image or video here", type=['png', 'jpg', 'jpeg', 'mp4', 'mov', 'avi'])
    if uploaded_file is not None:
        # Save uploaded file to a temp location with chunked writing
        if 'uploaded_temp_path' not in st.session_state or st.session_state.get('last_uploaded_name') != uploaded_file.name:
             with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
                chunk_size = 4096
                while True:
                    chunk = uploaded_file.read(chunk_size)
                    if not chunk:
                        break
                    tmp.write(chunk)
                st.session_state.uploaded_temp_path = tmp.name
                st.session_state.last_uploaded_name = uploaded_file.name
        
        file_to_scan = st.session_state.uploaded_temp_path
        st.success(f"Loaded: `{uploaded_file.name}`")
        with st.expander("Preview"):
            st.image(uploaded_file, use_column_width=True) if uploaded_file.type.startswith('image') else st.video(uploaded_file)

with tab2:
    url_input = st.text_input("Paste Image or Video URL")
    if url_input:
        if st.button("Fetch URL", type="secondary"):
            with st.status("Downloading media...", expanded=True) as status:
                downloaded = download_file(url_input)
                if downloaded:
                    st.session_state.url_temp_path = downloaded
                    st.session_state.last_url = url_input
                    status.update(label="Download complete!", state="complete", expanded=False)
                else:
                    status.update(label="Download failed", state="error")
        
        if st.session_state.get('last_url') == url_input and 'url_temp_path' in st.session_state:
             file_to_scan = st.session_state.url_temp_path
             st.success("Ready to scan URL media")

st.markdown("---")

# Action Section
if file_to_scan:
    st.markdown("### 2. Analyze")
    if st.button("🚀 Start Detection", type="primary", use_container_width=True):
        if not api_key_input:
            st.error("⚠️ Please enter an API Key in the sidebar.")
        else:
            with st.status("Analyzing media...", expanded=True) as status:
                st.write("Initializing AI client...")
                client = get_client(api_key_input) # fast due to cache
                st.write("Uploading and scanning...")
                result = scan_file(file_to_scan, api_key_input)
                
                if result:
                    st.session_state.scan_result = result
                    st.session_state.scanned_file_name = os.path.basename(file_to_scan)
                    status.update(label="Analysis complete!", state="complete", expanded=False)
                else:
                    status.update(label="Analysis failed", state="error")

# Results Display
if st.session_state.scan_result:
    result = st.session_state.scan_result
    status_text = result.get('status', 'UNKNOWN')
    score = result.get('score', 0.0)
    
    st.markdown("### 3. Results")
    
    # Hero Result Card
    result_container = st.container()
    
    if status_text == "AUTHENTIC":
        result_container.success(f"## ✅ {status_text}")
        color = "green"
    elif status_text == "FAKE":
        result_container.error(f"## 🚨 {status_text}")
        color = "red"
    else:
        result_container.warning(f"## ⚠️ {status_text}")
        color = "orange"

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(label="Manipulation Score", value=f"{score:.2%}", delta=None)
        st.caption("0% = Real, 100% = Fake")
    with col_b:
        st.progress(score)
    
    with st.expander("🔍 View Detailed Analysis"):
        st.json(result)
    
    if st.button("Start Over", type="secondary"):
        st.session_state.scan_result = None
        st.session_state.scanned_file_name = None
        st.rerun()
