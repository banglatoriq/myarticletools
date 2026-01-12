import streamlit as st
from serpapi import GoogleSearch 
import re
import json
import os
import pandas as pd
from PIL import Image
import pytesseract
import streamlit.components.v1 as components
import requests
from bs4 import BeautifulSoup
import io  # ইমেজ অপটিমাইজারের জন্য নতুন যুক্ত করা হয়েছে

# --- পেজের কনফিগারেশন ---
st.set_page_config(page_title="SEO & Amazon Tool", page_icon="🛠️", layout="wide")
st.title("🛠️ All-in-One Content & Affiliate Tool")

# --- সাইডবার সেটিংস ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # --- API Key Management ---
    if 'api_key' not in st.session_state:
        query_params = st.query_params
        st.session_state.api_key = query_params.get("api_key", "")

    api_key_input = st.text_input("Enter SerpApi Key (For SEO Only):", value=st.session_state.api_key, type="password")

    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.rerun()

    api_key = st.session_state.api_key
    
    save_url = st.checkbox("Save Key to URL", value=(st.query_params.get("api_key") == api_key) if api_key else False)
    if save_url and api_key:
        st.query_params["api_key"] = api_key
    elif not save_url and "api_key" in st.query_params:
        del st.query_params["api_key"]
    
    st.divider()
    country = st.selectbox("Select Target Country (SEO):", ["United States", "United Kingdom", "Bangladesh", "India"])
    location_map = {
        "United States": {"gl": "us", "loc": "United States", "domain": "google.com"},
        "United Kingdom": {"gl": "uk", "loc": "United Kingdom", "domain": "google.co.uk"},
        "Bangladesh": {"gl": "bd", "loc": "Bangladesh", "domain": "google.com.bd"},
        "India": {"gl": "in", "loc": "India", "domain": "google.co.in"}
    }

# --- Helper Functions ---

# [NEW] Image Optimizer Function
def convert_image_to_webp(image_file):
    """ইমেজকে WebP ফরম্যাটে অপটিমাইজ করে কনভার্ট করে"""
    try:
        image = Image.open(image_file)
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", optimize=True, quality=80)
        buffer.seek(0)
        return buffer
    except Exception as e:
        return None

# [UPDATED] Amazon Scraper Function (Price/Rating removed, Desc added)
def get_amazon_product_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Page could not be loaded. Amazon might be blocking requests."}
            
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Product Title
        title_tag = soup.find(id="productTitle")
        product_title = title_tag.get_text(strip=True) if title_tag else "Title Not Found"

        # 2. Main Gallery Images
        gallery_images = []
        img_container = soup.find("img", {"id": "landingImage"})
        if img_container and img_container.get("data-a-dynamic-image"):
            json_data = img_container.get("data-a-dynamic-image")
            gallery_images = list(json.loads(json_data).keys())
        
        # Fallback for gallery
        if not gallery_images:
            match = re.search(r'"hiRes":"(.*?)"', response.text)
            if match: gallery_images.append(match.group(1))

        # 3. Description Text (Summary)
        description_text = ""
        desc_div = soup.find("div", {"id": "productDescription"})
        if desc_div:
            description_text = desc_div.get_text(separator="\n", strip=True)
        else:
            aplus_div = soup.find("div", {"id": "aplus"})
            if aplus_div:
                paragraphs = aplus_div.find_all("p")
                description_text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

        # 4. Description Images
        description_images = []
        target_divs = [soup.find("div", {"id": "productDescription"}), soup.find("div", {"id": "aplus"})]
        
        for container in target_divs:
            if container:
                imgs = container.find_all("img")
                for img in imgs:
                    src = img.get("data-src") or img.get("src")
                    if src and "http" in src:
                        if "sprite" not in src and "pixel" not in src and ".gif" not in src:
                            if src not in description_images and src not in gallery_images:
                                description_images.append(src)

        return {
            "title": product_title,
            "gallery_images": gallery_images,
            "description_text": description_text[:3000] + "..." if len(description_text) > 3000 else description_text,
            "description_images": description_images
        }
    
    except Exception as e:
        return {"error": str(e)}

def extract_asin(url):
    match = re.search(r"/([A-Z0-9]{10})(?:[/?]|$)", url)
    return match.group(1) if match else "Unknown"

# --- Content Planner Storage ---
PLANNER_FILE = 'content_planner.json'
def load_planner_data():
    if os.path.exists(PLANNER_FILE):
        try:
            with open(PLANNER_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    if 'checked_keywords' not in item: item['checked_keywords'] = []
                return data
        except: return []
    return []

def save_planner_data(data):
    with open(PLANNER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- Text Formatter ---
def format_text_to_html(text, style_name):
    # আপনার অরিজিনাল স্টাইল কোড এখানে অক্ষত রাখা হয়েছে
    styles = {
        "Modern Clean": {
            "div": "font-family: 'Inter', 'Segoe UI', sans-serif; line-height: 1.7; color: #333; max-width: 100%;",
            "h1": "color: #111; font-weight: 800; margin-top: 0.5em; margin-bottom: 0.5em; font-size: 2.2em;",
            "h2": "color: #111; font-weight: 700; margin-top: 1.5em; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; font-size: 1.8em;",
            "h3": "color: #444; font-weight: 600; margin-top: 1.2em; font-size: 1.4em;",
            "p": "margin-bottom: 1.2em; font-size: 17px; color: #333;",
            "ul": "margin-bottom: 1.2em; padding-left: 20px;",
            "li": "margin-bottom: 8px;",
            "img": "max-width: 100%; height: auto; border-radius: 8px; margin: 20px 0; display: block;",
            "strong": "color: #000; font-weight: 700;"
        },
        "Classic Serif": {
            "div": "font-family: 'Georgia', 'Cambria', serif; line-height: 1.8; color: #2a2a2a; font-size: 18px; max-width: 100%;",
            "h1": "font-family: 'Georgia', serif; color: #000; margin-top: 40px; font-size: 32px; font-weight: normal;",
            "h2": "font-family: 'Georgia', serif; color: #000; margin-top: 40px; font-size: 28px; font-weight: normal; border-bottom: 1px solid #ccc; padding-bottom: 5px;",
            "h3": "font-family: 'Georgia', serif; color: #333; margin-top: 30px; font-style: italic; font-size: 24px;",
            "p": "margin-bottom: 24px;",
            "ul": "margin-bottom: 24px; padding-left: 25px;",
            "li": "margin-bottom: 10px;",
            "img": "max-width: 100%; height: auto; border: 1px solid #ddd; padding: 5px; margin: 20px auto; display: block;",
            "strong": "font-weight: bold; color: #000;"
        },
        "Magazine Focus": {
            "div": "font-family: 'Merriweather', serif; line-height: 1.9; color: #222; max-width: 100%; background: #fff; padding: 20px; box-sizing: border-box;",
            "h1": "font-family: 'Montserrat', sans-serif; text-transform: uppercase; letter-spacing: 1px; color: #2c3e50; margin-top: 20px; font-size: 36px;",
            "h2": "font-family: 'Montserrat', sans-serif; text-transform: uppercase; letter-spacing: 1px; color: #d35400; border-left: 5px solid #d35400; padding-left: 15px; margin-top: 40px; font-size: 26px;",
            "h3": "font-family: 'Montserrat', sans-serif; color: #2c3e50; margin-top: 30px; font-size: 22px;",
            "p": "margin-bottom: 20px; font-size: 18px;",
            "ul": "list-style-type: square; color: #d35400; margin-bottom: 20px; padding-left: 20px;",
            "li": "margin-bottom: 10px; color: #222;",
            "img": "width: 100%; height: auto; margin: 30px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);",
            "strong": "font-weight: bold; color: #222;"
        }
    }
    
    current_style = styles.get(style_name, styles["Modern Clean"])
    
    html_content = f'<div style="{current_style["div"]}">\n'
    
    lines = text.split('\n')
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_content += "</ul>\n"
                in_list = False
            continue
            
        if line.startswith('### '):
            html_content += f'<h3 style="{current_style["h3"]}">{line[4:]}</h3>\n'
        elif line.startswith('## '):
            html_content += f'<h2 style="{current_style["h2"]}">{line[3:]}</h2>\n'
        elif line.startswith('# '):
            html_content += f'<h1 style="{current_style["h1"]}">{line[2:]}</h1>\n'
        elif line.startswith('- ') or line.startswith('* '):
            if not in_list:
                html_content += f'<ul style="{current_style["ul"]}">\n'
                in_list = True
            html_content += f'<li style="{current_style["li"]}">{line[2:]}</li>\n'
        elif line.startswith('![') and '](' in line:
            try:
                alt = line.split('![')[1].split('](')[0]
                src = line.split('](')[1].split(')')[0]
                html_content += f'<img src="{src}" alt="{alt}" style="{current_style["img"]}">\n'
            except:
                html_content += f'<p style="{current_style["p"]}">{line}</p>\n'
        else:
            if in_list:
                html_content += "</ul>\n"
                in_list = False
            line = re.sub(r'\*\*(.*?)\*\*', f'<strong style="{current_style["strong"]}">\\1</strong>', line)
            html_content += f'<p style="{current_style["p"]}">{line}</p>\n'
            
    if in_list:
        html_content += "</ul>\n"

    html_content += "</div>"
    return html_content

# --- TABS (Updated with Optimizer) ---
tab_seo, tab_amazon, tab_affiliate, tab_optimizer, tab_planner, tab_formatter, tab_ocr = st.tabs([
    "🔎 SEO Research", 
    "🛒 Amazon Scraper", 
    "🎨 Affiliate Code",
    "🚀 Image Optimizer", 
    "🗂️ Content Planner", 
    "📝 Blog Formatter",
    "📷 Image to Text"
])

# ==========================
# TAB 1: SEO RESEARCH (Keep Original)
# ==========================
with tab_seo:
    st.subheader("Google Search Analysis")
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("Enter Main Keyword:", placeholder="Example: Best Walking Cane")
    with col2:
        st.write("") 
        st.write("") 
        seo_submit = st.button("🚀 Start SEO Research", use_container_width=True)

    if seo_submit:
        if not api_key:
            st.error("⚠️ দয়া করে সাইডবারে SerpApi Key টি দিন (SEO ডাটার জন্য)।")
        elif not keyword:
            st.warning("⚠️ দয়া করে একটি Keyword লিখুন।")
        else:
            try:
                with st.spinner('Fetching SEO Data...'):
                    selected_loc = location_map[country]
                    params = {
                        "engine": "google",
                        "q": keyword,
                        "location": selected_loc["loc"],
                        "google_domain": selected_loc["domain"],
                        "gl": selected_loc["gl"],
                        "hl": "en",
                        "api_key": api_key
                    }
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    
                    snippet_content = "No direct snippet found."
                    if "answer_box" in results:
                        box = results["answer_box"]
                        if "snippet" in box: snippet_content = box["snippet"]
                        elif "answer" in box: snippet_content = box["answer"]
                        elif "list" in box: snippet_content = "\n".join(box["list"])

                    lsi = [i['query'] for i in results.get("related_searches", [])]
                    faqs = [q['question'] for q in results.get("related_questions", [])]
                    comps = []
                    for res in results.get("organic_results", [])[:10]:
                        comps.append(f"- [{res.get('title')}]({res.get('link')})")

                    st.success("✅ SEO Data Found!")
                    
                    prompt_text = f"""
Main Keyword: "{keyword}"
Snippet Context: "{snippet_content}"
LSI Keywords: {', '.join(lsi)}
FAQs: {chr(10).join(['- ' + q for q in faqs])}
Competitors: {chr(10).join([c.replace('- ', '').split('](')[1][:-1] for c in comps])}
"""
                    st.text_area("Copy for AI Writer:", value=prompt_text, height=200)
                    
            except Exception as e:
                st.error(f"Error: {e}")

# ==========================
# TAB 2: AMAZON PRODUCT INFO (UPDATED: Title, Gallery, Desc, No Price)
# ==========================
with tab_amazon:
    st.subheader("🛒 Amazon Name, Description & Images")
    st.info("লিংক দিন। আমরা টাইটেল, গ্যালারি ইমেজ, ডিসক্রিপশন টেক্সট এবং ডিসক্রিপশনের ভেতরের ছবিগুলো বের করে দেব।")
    
    amazon_url = st.text_input("Enter Amazon Product URL:", placeholder="https://www.amazon.com/dp/...")
    
    if st.button("Get Content"):
        if amazon_url:
            with st.spinner("Scraping Content from Amazon..."):
                data = get_amazon_product_data(amazon_url)
                
                if "error" in data:
                    st.error(f"Failed: {data['error']}")
                else:
                    st.success("✅ Content Extracted!")
                    
                    # 1. Title
                    st.markdown("### 🏷️ Product Title")
                    st.code(data['title'], language=None)
                    
                    st.divider()
                    
                    # 2. Main Gallery Images
                    st.markdown(f"### 🖼️ Main Gallery Images ({len(data['gallery_images'])})")
                    if data['gallery_images']:
                        cols = st.columns(3)
                        for i, img_link in enumerate(data['gallery_images']):
                            with cols[i % 3]:
                                st.image(img_link, use_container_width=True)
                                st.code(img_link, language=None)
                    else:
                        st.warning("No gallery images found.")

                    st.divider()

                    # 3. Description Text
                    st.markdown("### 📝 Description Summary")
                    if data['description_text']:
                        st.text_area("Product Description Content:", value=data['description_text'], height=250)
                    else:
                        st.info("No text description found.")

                    st.divider()

                    # 4. Description Images (Lifestyle/Features)
                    st.markdown(f"### 📸 Images from Description ({len(data['description_images'])})")
                    st.caption("এই ছবিগুলো প্রোডাক্ট ডিসক্রিপশন বা A+ Content এর ভেতর থেকে নেওয়া।")
                    
                    if data['description_images']:
                        d_cols = st.columns(3)
                        for i, d_img in enumerate(data['description_images']):
                            with d_cols[i % 3]:
                                st.image(d_img, use_container_width=True)
                                st.code(d_img, language=None)
                    else:
                        st.info("ডিসক্রিপশনের ভেতরে কোনো অতিরিক্ত ছবি পাওয়া যায়নি।")

        else:
            st.warning("Please enter a URL.")

# ==========================
# TAB 3: AFFILIATE CODE GENERATOR (Keep Original)
# ==========================
with tab_affiliate:
    st.header("🎨 HTML Affiliate Code Generator")
    st.write("এখানে প্রোডাক্টের তথ্য দিন, আমরা আপনার ব্লগের জন্য সুন্দর HTML কোড তৈরি করে দেব।")

    if 'aff_products' not in st.session_state:
        st.session_state.aff_products = [{'id': 0}]

    def get_star_html(rating):
        full_star = '&#9733;'
        empty_star = '&#9734;'
        stars = ''
        try:
            rating_val = float(rating)
        except:
            rating_val = 0.0
        full_stars_count = round(rating_val)
        for i in range(5):
            stars += full_star if i < full_stars_count else empty_star
        return f'<div style="color: #ffa41c; font-size: 14px; margin: 3px 0 5px 0;">{stars} <span style="color: #666; font-size: 12px;">({rating_val})</span></div>'

    def generate_detailed_review(data):
        star_html = get_star_html(data['rating'])
        pros_list = "".join([f"<li>&#10003; {p.strip()}</li>" for p in data['pros'].split('\n') if p.strip()]) or '<li>&#10003; No pros listed.</li>'
        cons_list = "".join([f"<li>&#10007; {c.strip()}</li>" for c in data['cons'].split('\n') if c.strip()]) or '<li>&#10007; No cons listed.</li>'
        return f"""<div style="margin-bottom: 25px;">    <a href="{data['link']}" target="_blank" rel="nofollow sponsored"         style="text-decoration: none; color: inherit; display: block; border: 1px solid #ddd; border-radius: 10px; padding: 20px; background: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">                <div style="display: flex; align-items: center; gap: 20px; border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 15px;">            <img src="{data['image']}" style="width: 80px; height: 80px; object-fit: contain; flex-shrink: 0;" alt="{data['title']}">            <div style="flex: 1;">                <h4 style="margin: 0; color: #2c3e50; font-size: 18px;">{data['title']}</h4>                {star_html}                <p style="margin: 5px 0 0 0; font-size: 13px; color: #555;">{data['description']}</p>            </div>            <div style="min-width: 140px; text-align: right;">                <span style="background: #e67e22; color: white; padding: 10px 20px; border-radius: 5px; font-size: 14px; font-weight: bold; display: inline-block;">Check Price &rarr;</span>            </div>        </div>                <div style="display: flex; flex-wrap: wrap; gap: 20px;">            <div style="flex: 1; min-width: 45%; padding: 10px; border-left: 3px solid #2ecc71; background: #f7fff7;">                <h5 style="margin: 0 0 5px 0; color: #27ae60; font-size: 15px;">PROS:</h5>                <ul style="list-style: none; padding: 0; margin: 0; font-size: 13px; color: #333;">{pros_list}</ul>            </div>            <div style="flex: 1; min-width: 45%; padding: 10px; border-left: 3px solid #e74c3c; background: #fff7f7;">                <h5 style="margin: 0 0 5px 0; color: #c0392b; font-size: 15px;">CONS:</h5>                <ul style="list-style: none; padding: 0; margin: 0; font-size: 13px; color: #333;">{cons_list}</ul>            </div>        </div>    </a></div>"""

    def generate_benefit_badge(data):
        star_html = get_star_html(data['rating'])
        return f"""<div style="margin-bottom: 25px;">    <a href="{data['link']}" target="_blank" rel="nofollow sponsored"         style="text-decoration: none; color: inherit; display: block; position: relative; border: 2px solid {data['badge_color']}; border-radius: 8px; padding: 20px; background: #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">        <div style="position: absolute; top: -12px; left: 20px; background: {data['badge_color']}; color: white; padding: 2px 12px; font-size: 12px; font-weight: bold; border-radius: 4px; text-transform: uppercase;">            {data['badge_text']}        </div>        <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">            <img src="{data['image']}" style="width: 80px; height: 80px; object-fit: contain; flex-shrink: 0;" alt="{data['title']}">            <div style="flex: 1;">                <h4 style="margin: 0; color: #333;">{data['title']}</h4>                {star_html}                <p style="margin: 5px 0 0 0; font-size: 13px; color: #666;">{data['description']}</p>            </div>            <div style="text-align: right; min-width: 120px;">                <span style="background: {data['badge_color']}; color: white; padding: 10px 15px; border-radius: 4px; font-size: 13px; font-weight: bold; display: inline-block;">Check Price &rarr;</span>            </div>        </div>    </a></div>"""

    def generate_featured_deal(data):
        star_html = get_star_html(data['rating'])
        deal_color = data['badge_color'] if data['badge_color'] else '#ff9900'
        return f"""<div style="margin-bottom: 30px;">    <a href="{data['link']}" target="_blank" rel="nofollow sponsored"         style="text-decoration: none; color: inherit; display: block; position: relative; border-radius: 12px; padding: 20px; background: linear-gradient(145deg, #f0f0f0, #ffffff); box-shadow: 0 8px 20px rgba(0,0,0,0.15);">        <div style="position: absolute; top: 0; right: 0; background: {deal_color}; color: white; padding: 6px 15px; font-size: 14px; font-weight: bold; border-bottom-left-radius: 10px;">            {data['badge_text']}        </div>        <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap; padding-top: 15px;">            <img src="{data['image']}" style="width: 100px; height: 100px; object-fit: contain; flex-shrink: 0;" alt="{data['title']}">            <div style="flex: 1;">                <h4 style="margin: 0; color: #333; font-size: 18px;">{data['title']}</h4>                {star_html}                <p style="margin: 5px 0 15px 0; font-size: 14px; color: #555; border-bottom: 1px dashed #ddd; padding-bottom: 10px;">{data['description']}</p>                <div style="text-align: left;">                    <span style="background: #c0392b; color: white; padding: 12px 25px; border-radius: 8px; font-size: 15px; font-weight: bold; display: inline-block;">See Deal on Amazon &rarr;</span>                </div>            </div>        </div>    </a></div>"""

    def generate_feature_callout(data):
        features = [f.strip() for f in data['description'].split('.') if len(f.strip()) > 5][:3]
        features_html = "".join([f"<li>&#9989; {f}</li>" for f in features])
        return f"""<div style="margin-bottom: 25px;">    <a href="{data['link']}" target="_blank" rel="nofollow sponsored"         style="text-decoration: none; color: inherit; display: block; border: 1px solid #ddd; border-left: 8px solid #3498db; border-radius: 10px; padding: 20px; background: #f7f7f7; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">        <div style="display: flex; gap: 20px; flex-wrap: wrap;">            <div style="flex-shrink: 0; text-align: center;">                <img src="{data['image']}" style="width: 80px; height: 80px; object-fit: contain; margin-bottom: 5px;" alt="{data['title']}">                <div style="color: #ffa41c; font-size: 12px; font-weight: bold;">{data['rating']} Stars</div>            </div>            <div style="flex: 1; min-width: 250px;">                <h4 style="margin: 0 0 8px 0; color: #333; font-size: 18px;">{data['title']}</h4>                <ul style="list-style: none; padding: 0; margin: 0; font-size: 13px; color: #555;">                    {features_html}                </ul>            </div>            <div style="flex-shrink: 0; display: flex; align-items: center; justify-content: center;">                <span style="background: #3498db; color: white; padding: 12px 20px; border-radius: 6px; font-size: 14px; font-weight: bold; display: inline-block;">Shop Now &rarr;</span>            </div>        </div>    </a></div>"""

    def generate_vertical_card(data):
        star_html = get_star_html(data['rating'])
        return f"""<div style="margin-bottom: 25px; display: inline-block; width: 100%; max-width: 300px; vertical-align: top; margin-right: 15px;">    <a href="{data['link']}" target="_blank" rel="nofollow sponsored"         style="text-decoration: none; color: inherit; display: block; border: 1px solid #eee; border-radius: 12px; padding: 20px; background: #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.06); transition: transform 0.2s; text-align: center;">                <div style="margin-bottom: 15px; height: 180px; display: flex; align-items: center; justify-content: center;">            <img src="{data['image']}" style="max-width: 100%; max-height: 100%; object-fit: contain;" alt="{data['title']}">        </div>        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 5px;">{data['badge_text']}</div>                <h4 style="margin: 0 0 10px 0; color: #222; font-size: 16px; line-height: 1.4; height: 45px; overflow: hidden;">{data['title']}</h4>                <div style="display: flex; justify-content: center; margin-bottom: 10px;">{star_html}</div>                <p style="font-size: 13px; color: #666; margin-bottom: 15px; line-height: 1.5; height: 40px; overflow: hidden;">{data['description']}</p>        <span style="background: #111; color: white; padding: 12px 0; width: 100%; border-radius: 6px; font-size: 14px; font-weight: bold; display: block;">            Check Price        </span>    </a></div>"""

    design_option = st.selectbox("ডিজাইন স্টাইল নির্বাচন করুন:", ["Detailed Review Snippet (Pros/Cons সহ)", "Benefit Badge Style (ব্যাজ সহ)", "Featured Deal Box (অফার বক্স)", "Key Feature Callout (লিস্ট স্টাইল)", "Modern Vertical Card (লম্বা কার্ড)"])
    
    for i, prod in enumerate(st.session_state.aff_products):
        with st.expander(f"🛒 Product {i+1} Details", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.aff_products[i]['title'] = st.text_input(f"Product Title #{i+1}", key=f"title_{i}")
                st.session_state.aff_products[i]['link'] = st.text_input(f"Affiliate Link #{i+1}", key=f"link_{i}")
                st.session_state.aff_products[i]['badge_text'] = st.text_input(f"Badge Text #{i+1} (e.g. Best Overall)", key=f"badge_{i}")
            with col2:
                st.session_state.aff_products[i]['image'] = st.text_input(f"Image URL #{i+1}", key=f"img_{i}")
                st.session_state.aff_products[i]['rating'] = st.number_input(f"Rating (1-5) #{i+1}", min_value=1.0, max_value=5.0, value=4.5, step=0.1, key=f"rating_{i}")
                st.session_state.aff_products[i]['badge_color'] = st.color_picker(f"Badge Color #{i+1}", "#343a40", key=f"color_{i}")
            st.session_state.aff_products[i]['description'] = st.text_area(f"Description #{i+1}", key=f"desc_{i}", height=70)
            c1, c2 = st.columns(2)
            with c1:
                st.session_state.aff_products[i]['pros'] = st.text_area(f"Pros (Line by line) #{i+1}", key=f"pros_{i}", height=100)
            with c2:
                st.session_state.aff_products[i]['cons'] = st.text_area(f"Cons (Line by line) #{i+1}", key=f"cons_{i}", height=100)

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("➕ Add Product"):
            st.session_state.aff_products.append({'id': len(st.session_state.aff_products)})
            st.rerun()
    with col_btn2:
        if len(st.session_state.aff_products) > 1:
            if st.button("❌ Remove Last"):
                st.session_state.aff_products.pop()
                st.rerun()

    st.divider()

    if st.button("🚀 Generate Code & Preview"):
        full_html_output = ""
        for p in st.session_state.aff_products:
            data = {
                'title': p.get('title', 'Sample Product'),
                'link': p.get('link', '#'),
                'image': p.get('image', 'https://via.placeholder.com/150'),
                'rating': p.get('rating', 4.5),
                'description': p.get('description', 'Great product description here.'),
                'badge_text': p.get('badge_text', 'Best Choice'),
                'badge_color': p.get('badge_color', '#000000'),
                'pros': p.get('pros', ''),
                'cons': p.get('cons', '')
            }
            if "Detailed Review" in design_option:
                full_html_output += generate_detailed_review(data)
            elif "Benefit Badge" in design_option:
                full_html_output += generate_benefit_badge(data)
            elif "Featured Deal" in design_option:
                full_html_output += generate_featured_deal(data)
            elif "Key Feature" in design_option:
                full_html_output += generate_feature_callout(data)
            elif "Vertical Card" in design_option:
                full_html_output += generate_vertical_card(data)

        disclosure = '<div style="font-size: 11px; color: #888; margin-top: 15px; font-style: italic; text-align: right; clear: both;">As an Amazon Associate I earn from qualifying purchases.</div>'
        full_html_output += disclosure

        st.subheader("📝 Generated HTML Code")
        st.code(full_html_output, language='html')
        st.subheader("👁️ Live Preview")
        components.html(full_html_output, height=600, scrolling=True)

# ==========================
# TAB 4: IMAGE OPTIMIZER (NEW FEATURE)
# ==========================
with tab_optimizer:
    st.header("🚀 WebP Image Optimizer")
    st.info("আপনার ছবি আপলোড করুন। এটি অটোমেটিক কম্প্রেস হবে এবং WebP ফরম্যাটে কনভার্ট হয়ে যাবে। এটি ব্লগের লোডিং স্পিড বাড়াতে সাহায্য করে।")

    uploaded_files = st.file_uploader("Upload Images (JPG, PNG)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

    if uploaded_files:
        st.divider()
        st.subheader("🎉 Optimized Images")
        
        # Grid layout for results
        cols = st.columns(3)
        
        for i, uploaded_file in enumerate(uploaded_files):
            # Process each image
            optimized_buffer = convert_image_to_webp(uploaded_file)
            
            if optimized_buffer:
                # Calculate size savings (Optional visualization)
                original_size = uploaded_file.size / 1024 # KB
                optimized_size = optimized_buffer.getbuffer().nbytes / 1024 # KB
                saving = original_size - optimized_size
                saving_percent = (saving / original_size) * 100
                
                # Display in grid
                with cols[i % 3]:
                    with st.container(border=True):
                        # Show original image preview
                        st.image(uploaded_file, caption="Original Preview", use_container_width=True)
                        
                        st.markdown(f"""
                        **Stats:**
                        - Original: `{original_size:.1f} KB`
                        - Optimized: `{optimized_size:.1f} KB`
                        - Saved: **{saving_percent:.1f}%** 📉
                        """)
                        
                        # Download Button
                        file_name = os.path.splitext(uploaded_file.name)[0] + ".webp"
                        st.download_button(
                            label="⬇️ Download WebP",
                            data=optimized_buffer,
                            file_name=file_name,
                            mime="image/webp",
                            key=f"dl_{i}",
                            type="primary",
                            use_container_width=True
                        )

# ==========================
# TAB 5: CONTENT PLANNER (Keep Original)
# ==========================
with tab_planner:
    st.header("🗂️ Keyword Cluster & Content Planner")
    st.info("আপনার কিওয়ার্ড ক্লাস্টারগুলো এখানে সেভ রাখুন এবং কাজের অগ্রগতি ট্র্যাক করুন। ডাটা অটোমেটিক সেভ থাকবে।")

    # Load Data
    if 'planner_data' not in st.session_state:
        st.session_state.planner_data = load_planner_data()

    # --- Dashboard Metrics ---
    total_keywords_count = 0
    completed_keywords_count = 0

    for item in st.session_state.planner_data:
        kws = [k.strip() for k in item.get('keywords', '').split(';') if k.strip()]
        total_keywords_count += len(kws)
        checked = item.get('checked_keywords', [])
        completed_keywords_count += len(checked)

    pending_keywords_count = total_keywords_count - completed_keywords_count
    
    col_metrics, col_actions = st.columns([3, 1])

    with col_metrics:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Articles (Keywords)", total_keywords_count)
        m2.metric("✅ Completed Articles", completed_keywords_count)
        m3.metric("⏳ Pending Articles", pending_keywords_count)

    with col_actions:
        st.write("") 
        st.write("") 
        if total_keywords_count > 0:
            if st.button("🗑️ সব ডাটা মুছে ফেলুন", type="primary", use_container_width=True):
                st.session_state.planner_data = []
                save_planner_data([])
                st.rerun()

    st.divider()

    # --- Data Input Section ---
    with st.expander("➕ Add New Clusters (Upload CSV or Paste Text)", expanded=(total_keywords_count == 0)):
        tab_input_text, tab_input_csv = st.tabs(["Paste Text", "Upload CSV"])
        
        with tab_input_text:
            st.caption("Format: `Cluster Label : YOUR LABEL Keywords: key1; key2; key3`")
            raw_text = st.text_area("Paste your cluster data here:", height=150)
            if st.button("Add from Text"):
                matches = re.findall(r"Cluster Label\s*[:\|]\s*(.*?)\s*Keywords\s*[:\|]\s*(.*)", raw_text, re.IGNORECASE | re.MULTILINE)
                
                if matches:
                    count = 0
                    for match in matches:
                        label = match[0].strip()
                        keywords = match[1].strip()
                        if not any(d['label'] == label for d in st.session_state.planner_data):
                            st.session_state.planner_data.append({
                                'label': label,
                                'keywords': keywords,
                                'done': False,
                                'checked_keywords': [] 
                            })
                            count += 1
                    save_planner_data(st.session_state.planner_data)
                    st.success(f"✅ {count} new clusters added!")
                    st.rerun()
                else:
                    st.warning("No matching format found. Please check the input format.")

        with tab_input_csv:
            uploaded_file = st.file_uploader("Upload CSV/Excel file", type=['csv', 'xlsx'])
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    label_cols = [c for c in df.columns if 'label' in c.lower() or 'cluster' in c.lower()]
                    kw_cols = [c for c in df.columns if 'keyword' in c.lower()]
                    
                    label_col = label_cols[0] if label_cols else None
                    kw_col = None

                    if kw_cols:
                        for col in kw_cols:
                            sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
                            if isinstance(sample, str) and (';' in sample or len(sample) > 5):
                                kw_col = col
                                break
                        if not kw_col:
                            kw_col = kw_cols[0]
                    
                    if label_col and kw_col:
                        count = 0
                        for _, row in df.iterrows():
                            label = str(row[label_col]).strip()
                            keywords = str(row[kw_col]).strip()
                            if not any(d['label'] == label for d in st.session_state.planner_data):
                                st.session_state.planner_data.append({
                                    'label': label,
                                    'keywords': keywords,
                                    'done': False,
                                    'checked_keywords': []
                                })
                                count += 1
                        save_planner_data(st.session_state.planner_data)
                        st.success(f"✅ {count} clusters imported from file!")
                        st.rerun()
                    else:
                        st.error("Could not identify 'Cluster Label' and 'Keywords' columns. Ensure CSV headers are correct.")
                except Exception as e:
                    st.error(f"Error reading file: {e}")

    # --- Display Cards (GRID LAYOUT) ---
    st.subheader("Your Content Plan")
    
    filter_status = st.radio("Filter:", ["All", "Pending", "Completed"], horizontal=True)
    
    display_data = []
    for i, item in enumerate(st.session_state.planner_data):
        item['original_index'] = i 
        if filter_status == "All":
            display_data.append(item)
        elif filter_status == "Pending" and not item['done']:
            display_data.append(item)
        elif filter_status == "Completed" and item['done']:
            display_data.append(item)

    if not display_data:
        st.info("No clusters found matching your filter.")
    else:
        cols = st.columns(3)
        
        for i, item in enumerate(display_data):
            idx = item['original_index']
            col = cols[i % 3] 
            
            with col:
                with st.container(border=True):
                    # --- Header Section ---
                    h_col1, h_col2 = st.columns([0.8, 0.2])
                    
                    with h_col1:
                        title_style = "text-decoration: line-through; color: gray;" if item['done'] else "font-weight: bold; color: #1f77b4; font-size: 16px;"
                        st.markdown(f"<div style='{title_style}'>{item['label']}</div>", unsafe_allow_html=True)
                        
                        is_done = st.checkbox("Mark Complete", value=item['done'], key=f"status_{idx}")
                        if is_done != item['done']:
                            st.session_state.planner_data[idx]['done'] = is_done
                            save_planner_data(st.session_state.planner_data)
                            st.rerun()

                    with h_col2:
                         if st.button("🗑️", key=f"del_c_{idx}", help="Delete Cluster"):
                            st.session_state.planner_data.pop(idx)
                            save_planner_data(st.session_state.planner_data)
                            st.rerun()
                    
                    st.markdown("---")
                    
                    # --- Scrollable Keywords List ---
                    with st.container(height=250, border=False):
                        keywords_list = [k.strip() for k in item['keywords'].split(';') if k.strip()]
                        
                        if not keywords_list:
                            st.caption("No keywords.")
                        else:
                            checked_kws = set(item.get('checked_keywords', []))
                            
                            for kw in keywords_list:
                                kw_key = f"chk_{idx}_{hash(kw)}"
                                is_checked = kw in checked_kws
                                
                                k_col1, k_col2 = st.columns([0.15, 0.85])
                                
                                with k_col1:
                                    new_checked = st.checkbox("Done", value=is_checked, key=kw_key, label_visibility="collapsed")
                                
                                with k_col2:
                                    st.code(kw, language=None)
                                
                                if new_checked != is_checked:
                                    if new_checked:
                                        item.setdefault('checked_keywords', []).append(kw)
                                    else:
                                        item.setdefault('checked_keywords', []).remove(kw)
                                    save_planner_data(st.session_state.planner_data)
                                    st.rerun()
                    
                    with st.expander("⚙️ Edit"):
                        updated_keywords = st.multiselect(
                            "Remove:",
                            options=keywords_list,
                            default=keywords_list,
                            key=f"edit_{idx}",
                            label_visibility="collapsed"
                        )
                        if len(updated_keywords) != len(keywords_list) or set(updated_keywords) != set(keywords_list):
                            new_keywords_str = "; ".join(updated_keywords)
                            st.session_state.planner_data[idx]['keywords'] = new_keywords_str
                            save_planner_data(st.session_state.planner_data)
                            st.rerun()

# ==========================
# TAB 6: BLOG FORMATTER (Keep Original)
# ==========================
with tab_formatter:
    st.header("📝 Blog Post Formatter")
    st.info("আপনার আর্টিকেলটি এখানে পেস্ট করুন। আমরা এটিকে সুন্দর, রেসপন্সিভ এবং SEO-Friendly HTML এ রূপান্তর করে দেব।")

    col_input, col_settings = st.columns([3, 1])
    
    with col_settings:
        st.subheader("Design Settings")
        design_style = st.selectbox(
            "Select Design Style:", 
            ["Modern Clean", "Classic Serif", "Magazine Focus"]
        )
        st.write("---")
        if st.button("🔄 Convert to HTML", type="primary", use_container_width=True):
            st.session_state.do_convert = True
        
    with col_input:
        raw_blog_text = st.text_area(
            "Paste your full blog content here (supports Basic Markdown like # Headers, - Lists, **Bold**):", 
            height=400,
            placeholder="# My Awesome Blog Post\n\nHere is the introduction...\n\n## Key Features\n- Feature 1\n- Feature 2"
        )

    if st.session_state.get('do_convert') and raw_blog_text:
        st.divider()
        st.subheader("🎉 Your Formatted HTML")
        
        formatted_html = format_text_to_html(raw_blog_text, design_style)
        
        st.code(formatted_html, language='html')
        st.subheader("👁️ Live Preview")
        components.html(formatted_html, height=600, scrolling=True)
        st.success("HTML generated successfully! Copy the code above and paste it into your CMS (WordPress Custom HTML block, Blogger HTML view, etc.).")

# ==========================
# TAB 7: IMAGE TO TEXT (Keep Original)
# ==========================
with tab_ocr:
    st.header("📷 Image to Text (OCR)")
    st.info("যেকোনো ছবি আপলোড করুন, আমরা তার ভেতরের লেখাগুলো বের করে দেব।")

    uploaded_image = st.file_uploader("Upload an Image (JPG, PNG)", type=["jpg", "png", "jpeg"])

    if uploaded_image is not None:
        col_img_view, col_text_view = st.columns(2)
        
        with col_img_view:
            st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)
            if st.button("🔍 Extract Text", type="primary"):
                st.session_state.do_ocr = True

        with col_text_view:
            if st.session_state.get('do_ocr'):
                with st.spinner("Extracting text..."):
                    try:
                        image = Image.open(uploaded_image)
                        extracted_text = pytesseract.image_to_string(image)
                        
                        st.subheader("📝 Extracted Text:")
                        if extracted_text.strip():
                            st.text_area("Copy text below:", value=extracted_text, height=300)
                        else:
                            st.warning("No text found in the image.")
                            
                    except Exception as e:
                        st.error("Error during extraction. Please make sure Tesseract OCR is installed on the server.")
                        st.caption(f"Details: {e}")
                        st.info("Tip: If you are deploying on Streamlit Cloud, ensure `packages.txt` contains `tesseract-ocr`.")

# ==========================
# TAB 8: QUICK WRITER (SMART TEMPLATE)
# ==========================
with tab_writer:
    st.header("⚡ Smart Article Generator (Fill-in-the-Blanks)")
    st.info("এটি একটি 'Rule-Based' রাইটার। এটি আপনার দেওয়া তথ্যগুলোকে সুন্দর বাক্যে সাজিয়ে একটি এসইও ফ্রেন্ডলি ড্রাফট তৈরি করে দেবে।")

    # --- INPUT SECTION ---
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            w_product = st.text_input("Product Name:", placeholder="Ex: Hugo Adjustable Cane")
            w_keyword = st.text_input("Target Keyword:", placeholder="Ex: best walking cane for seniors")
            w_audience = st.text_input("Target Audience:", placeholder="Ex: elderly people")
        with col2:
            w_rating = st.slider("Product Rating:", 1.0, 5.0, 4.5)
            w_price_type = st.selectbox("Price Range:", ["Budget-Friendly", "Mid-Range", "Premium/Expensive"])
    
    st.write("---")
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**🔹 Key Features (প্রতি লাইনে একটি করে ফিচার লিখুন):**")
        w_features = st.text_area("Features:", height=150, placeholder="Lightweight aluminum body\nErgonomic cushion handle\nAdjustable height settings")
    with col4:
        st.markdown("**🔹 Pros & Cons (প্রতি লাইনে একটি):**")
        w_pros = st.text_area("Pros:", height=70, placeholder="Easy to carry\nVery durable")
        w_cons = st.text_area("Cons:", height=70, placeholder="Limited color options")

    # --- GENERATOR LOGIC ---
    if st.button("📝 Generate Article Draft", type="primary"):
        if w_product and w_keyword and w_features:
            
            # 1. Processing Lists
            # ফিচারগুলোকে লিস্টে ভাগ করা এবং প্যারাগ্রাফে রূপান্তর করা
            feat_list = [f.strip() for f in w_features.split('\n') if f.strip()]
            pros_list = [p.strip() for p in w_pros.split('\n') if p.strip()]
            cons_list = [c.strip() for c in w_cons.split('\n') if c.strip()]
            
            # ফিচারগুলোকে একটু বিস্তারিত বাক্যে রূপান্তর করা (Sentence Expansion)
            expanded_features = ""
            for i, feat in enumerate(feat_list):
                starters = [
                    f"First and foremost, the **{w_product}** comes with {feat}.",
                    f"Another significant aspect is the {feat}, which makes it stand out.",
                    f"Users will also appreciate the {feat}, ensuring a great experience.",
                    f"Furthermore, the inclusion of {feat} adds tremendous value."
                ]
                # ঘুরিয়ে ফিরিয়ে বাক্য ব্যবহার করা
                sentence = starters[i % len(starters)] 
                expanded_features += f"- {sentence} This is particularly useful for {w_audience} because it solves common daily struggles.\n"

            # 2. Building the Article (THE TEMPLATE)
            article_body = f"""
# {w_product} Review: The Best Choice for {w_keyword}?

## Introduction
Finding the **{w_keyword}** can be a daunting task, especially with so many options available in the market today. Whether you are looking for comfort, durability, or style, making the right choice is crucial.

Today, we are diving deep into the **{w_product}**. This product has been gaining attention among {w_audience} for its impressive build quality and features. In this review, we will analyze why this might be the perfect solution for your needs.

---

## At a Glance
* **Product Name:** {w_product}
* **Rating:** {w_rating}/5 Stars
* **Price Category:** {w_price_type}
* **Best For:** {w_audience} looking for {w_keyword}

---

## In-Depth Features Analysis
Why should you consider buying the {w_product}? Let's look at the key features that set it apart from the competition.

{expanded_features}

These features combined make the {w_product} a top contender in the {w_keyword} category.

---

## Pros and Cons
No product is perfect. Here is a transparent look at what we liked and what could be improved.

### ✅ What We Like (Pros)
{chr(10).join([f"* **{p}**: This is a major advantage for daily use." for p in pros_list])}

### ❌ What We Don't Like (Cons)
{chr(10).join([f"* {c}: While not a dealbreaker, it is something to keep in mind." for c in cons_list])}

---

## Who is this for?
If you are **{w_audience}**, then the **{w_product}** is designed specifically with you in mind. Its {w_price_type} price point makes it an attractive option without compromising on quality. 

If you prioritize {feat_list[0] if feat_list else 'quality'} and {feat_list[1] if len(feat_list)>1 else 'performance'}, this is an investment worth making.

---

## Final Verdict
To conclude, the **{w_product}** offers excellent value for money. With a rating of **{w_rating}/5**, it delivers on its promises.

For anyone searching for a reliable **{w_keyword}**, we highly recommend checking this out. It checks all the boxes for comfort, usability, and durability.

**[Check Latest Price of {w_product} on Amazon](#)**
            """
            
            # --- OUTPUT ---
            st.success("🎉 Article Draft Generated Successfully!")
            st.subheader("Preview:")
            st.markdown(article_body)
            st.divider()
            st.subheader("Copy Code:")
            st.text_area("Copy Markdown Code:", value=article_body, height=400)
            
        else:
            st.warning("⚠️ Please fill in at least the Product Name, Keyword, and Features.")
