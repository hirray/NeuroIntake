"""
Downloads Noto Sans, Noto Sans Devanagari, and Noto Sans Gujarati fonts
for accurate ReportLab PDF rendering with multilingual text (English, Hindi, Gujarati).
"""
import os
import urllib.request

FONTS_DIR = os.path.dirname(os.path.abspath(__file__))

FONTS = {
    "NotoSans-Regular.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf",
    "NotoSans-Bold.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSans/NotoSans-Bold.ttf",
    "NotoSansDevanagari-Regular.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf",
    "NotoSansDevanagari-Bold.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf",
    "NotoSansGujarati-Regular.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Regular.ttf",
    "NotoSansGujarati-Bold.ttf": "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansGujarati/NotoSansGujarati-Bold.ttf",
}

def ensure_fonts():
    for filename, url in FONTS.items():
        target_path = os.path.join(FONTS_DIR, filename)
        if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
            print(f"Downloading {filename}...")
            try:
                urllib.request.urlretrieve(url, target_path)
                print(f"Downloaded {filename}: {os.path.getsize(target_path)} bytes")
            except Exception as e:
                print(f"Warning: Failed downloading {filename} from {url}: {e}")

if __name__ == "__main__":
    ensure_fonts()
