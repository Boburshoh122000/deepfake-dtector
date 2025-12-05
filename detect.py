from realitydefender import RealityDefender
import os

import argparse
import sys
import tempfile
import urllib.request
from urllib.parse import urlparse

# You can also set this via environment variable: export REALITY_DEFENDER_API_KEY="your_key"
api_key = os.getenv("REALITY_DEFENDER_API_KEY", "rd_695514645a00b6d0_5db2bc1347c11b81fb4b21006ee0574e")

def is_url(path):
    return path.startswith('http://') or path.startswith('https://')

def download_file(url):
    try:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or 'downloaded_file'
        suffix = os.path.splitext(filename)[1]
        
        # Create a temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(temp_fd)
        
        print(f"Downloading {url}...")
        req = urllib.request.Request(
            url, 
            data=None, 
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'}
        )
        with urllib.request.urlopen(req) as response, open(temp_path, 'wb') as out_file:
            out_file.write(response.read())
        return temp_path
    except Exception as e:
        print(f"Failed to download URL: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Detect deepfakes in images and videos (local files or URLs).")
    parser.add_argument("path", nargs="?", help="Path to local file or URL to media.")
    args = parser.parse_args()

    # Default to sample image if no argument provided
    path = args.path or "/Users/bobur/.gemini/antigravity/brain/c3bdb620-6400-4cd3-b3f0-897834fef1b0/sample_face_1764936452944.png"
    
    temp_file = None
    file_to_scan = path

    try:
        if is_url(path):
            temp_file = download_file(path)
            if not temp_file:
                sys.exit(1)
            file_to_scan = temp_file
        
        client = RealityDefender(api_key=api_key)
        
        if os.path.exists(file_to_scan):
            print(f"Scanning file: {file_to_scan}...")
            result = client.detect_file(file_to_scan)
            print(result)
        else:
            print(f"Error: File not found: {file_to_scan}")
            sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        # Cleanup temp file if it was downloaded
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
            print("Cleaned up temporary file.")

if __name__ == "__main__":
    main()
