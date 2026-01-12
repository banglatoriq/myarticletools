import streamlit as st
from serpapi import GoogleSearch
import re
import json
import os
import pandas as pd
from PIL import Image
import pytesseract
import streamlit.components.v1 as components

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

    api_key_input = st.text_input("Enter SerpApi Key:", value=st.session_state.api_key, type="password")

    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.rerun()

    api_key = st.session_state.api_key

    save_url = st.checkbox("Save Key to URL (Bookmarking)", value=(st.query_params.get("api_key") == api_key) if api_key else False)
    
    if save_url and api_key:
        st.query_params["api_key"] = api_key
    elif not save_url and "api_key" in st.query_params:
        del st.query_params["api_key"]

    st.info("আপনার SerpApi ড্যাশবোর্ড থেকে Key টি এখানে দিন। 'Save Key to URL' চেক করলে পরবর্তীতে অটোমেটিক লোড হবে।")
    
    st.divider()

    country = st.selectbox("Select Target Country:", ["United States", "United Kingdom", "Bangladesh", "India"])
    location_map = {
        "United States": {"gl": "us", "loc": "United States", "domain": "google.com"},
        "United Kingdom": {"gl": "uk", "loc": "United Kingdom", "domain": "google.co.uk"},
        "Bangladesh": {"gl": "bd", "loc": "Bangladesh", "domain": "google.com.bd"},
        "India": {"gl": "in", "loc": "India", "domain": "google.co.in"}
    }

# --- Helper Functions ---

# --- Updated Helper Functions ---

def get_domain_from_url(url):
    """URL থেকে Amazon Domain বের করে (যেমন: amazon.in, amazon.co.uk)"""
    try:
        if "amazon.co.uk" in url: return "www.amazon.co.uk"
        if "amazon.in" in url: return "www.amazon.in"
        if "amazon.ca" in url: return "www.amazon.ca"
        if "amazon.de" in url: return "www.amazon.de"
        # ডিফল্ট হিসেবে .com
        return "www.amazon.com"
    except:
        return "www.amazon.com"

def extract_asin(url):
    # ক্লিন করার জন্য স্পেস রিমুভ করা
    url = url.strip()
    
    # সাধারণ প্যাটার্নগুলো চেক করা
    regex_list = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
        r"dp/([A-Z0-9]{10})",
        r"aadp/([A-Z0-9]{10})", # মোবাইল লিংক
        r"/[A-Z0-9]{10}"       # শর্ট লিংক প্যাটার্ন
    ]
    
    for regex in regex_list:
        match = re.search(regex, url)
        if match:
            # ১০ ক্যারেক্টারের সঠিক ASIN কিনা ডাবল চেক
            asin = match.group(1)
            if len(asin) == 10 and asin.isalnum():
                return asin
    return None

def get_high_res_image(img_url):
    """Amazon এর থাম্বনেইল ইমেজকে হাই-রেজোলিউশনে কনভার্ট করে"""
    if not img_url or img_url == "N/A":
        return "https://via.placeholder.com/150"
    # _AC_... অংশটি সরিয়ে দিলে অরিজিনাল সাইজ পাওয়া যায়
    return re.sub(r'\._AC_.*?\.', '.', img_url)

# --- Local Storage Functions for Content Planner ---
PLANNER_FILE = 'content_planner.json'

def load_planner_data():
    if os.path.exists(PLANNER_FILE):
        try:
            with open(PLANNER_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    if 'checked_keywords' not in item:
                        item['checked_keywords'] = []
                return data
        except:
            return []
    return []

def save_planner_data(data):
    with open(PLANNER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- Text Formatting Function (Inline CSS Version) ---
def format_text_to_html(text, style_name):
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

# --- মেইন অ্যাপ এরিয়া (Tabs) ---
tab_seo, tab_amazon, tab_affiliate, tab_planner, tab_formatter, tab_ocr = st.tabs([
    "🔎 SEO Research", 
    "🛒 Amazon Product Info", 
    "🎨 Affiliate Code Gen", 
    "🗂️ Content Planner", 
    "📝 Blog Formatter",
    "📷 Image to Text"
])

# ==========================
# TAB 1: SEO RESEARCH
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
            st.error("⚠️ দয়া করে সাইডবারে SerpApi Key টি দিন।")
        elif not keyword:
            st.warning("⚠️ দয়া করে একটি Keyword লিখুন।")
        else:
            try:
                with st.spinner('গুগল থেকে ডাটা কালেক্ট করা হচ্ছে...'):
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
# TAB 2: AMAZON PRODUCT INFO (SMART DOMAIN FIX)
# ==========================
with tab_amazon:
    st.subheader("Amazon Product Gallery & Details")
    st.info("💡 অ্যামাজন লিংক দিন। আমরা সব ইমেজ গ্যালারি আকারে দেখাব এবং টাইটেল কপি করার ব্যবস্থা করে দেব।")
    
    product_url = st.text_input("Paste Amazon Product Link:", placeholder="https://www.amazon.com/dp/B08...")
    amazon_submit = st.button("📦 Get Product Images & Info")

    if amazon_submit:
        if not api_key:
            st.error("⚠️ SerpApi Key প্রয়োজন। Settings এ গিয়ে Key দিন।")
        elif not product_url:
            st.warning("⚠️ লিংক দিন।")
        else:
            asin = extract_asin(product_url)
            domain = get_domain_from_url(product_url)
            
            if not asin:
                st.error("❌ লিংকটি সঠিক নয় বা ASIN পাওয়া যায়নি। দয়া করে 'amazon.com/dp/...' ফরম্যাটের লিংক দিন।")
            else:
                try:
                    with st.spinner(f'Fetching details for ASIN: {asin} from {domain}...'):
                        found_data = False
                        error_log = ""
                        
                        # Data placeholders
                        product_title = "N/A"
                        product_price = "Check on Amazon"
                        product_rating = "N/A"
                        image_list = [] 

                        # Step 1: Amazon Product API
                        try:
                            params = {
                                "engine": "amazon_product",
                                "product_id": asin,
                                "domain": domain, # ডাইনামিক ডোমেইন ব্যবহার করা হচ্ছে
                                "api_key": api_key
                            }
                            search = GoogleSearch(params)
                            results = search.get_dict()

                            if "product_result" in results:
                                product = results["product_result"]
                                product_title = product.get("title", "N/A")
                                product_rating = product.get("rating", "N/A")
                                if "price" in product:
                                    product_price = product["price"]
                                
                                # Fetch ALL Images
                                if "images" in product and len(product["images"]) > 0:
                                    for img in product["images"]:
                                        raw_link = img.get("link") if isinstance(img, dict) else img
                                        hd_link = get_high_res_image(raw_link)
                                        if hd_link not in image_list:
                                            image_list.append(hd_link)
                                else:
                                    main_img = product.get("main_image", "N/A")
                                    image_list.append(get_high_res_image(main_img))
                                
                                found_data = True
                            elif "error" in results:
                                error_log = results["error"]
                                
                        except Exception as e:
                            error_log = f"Amazon Product API: {str(e)}"

                        # Step 2: Fallback to Search API (If Product page fails)
                        if not found_data:
                            try:
                                params_fallback = {
                                    "engine": "amazon",
                                    "q": asin,
                                    "domain": domain,
                                    "api_key": api_key
                                }
                                search_fallback = GoogleSearch(params_fallback)
                                results = search_fallback.get_dict()
                                
                                if "organic_results" in results and len(results["organic_results"]) > 0:
                                    item = results["organic_results"][0]
                                    product_title = item.get("title", "N/A")
                                    raw_image = item.get("thumbnail", "N/A")
                                    image_list.append(get_high_res_image(raw_image))
                                    found_data = True
                            except Exception as e:
                                error_log += f" | Fallback: {str(e)}"

                        if found_data:
                            st.success("✅ ডাটা লোড হয়েছে!")
                            
                            st.markdown("### 🏷️ Product Title")
                            st.code(product_title, language=None)
                            
                            c1, c2 = st.columns(2)
                            c1.metric("Price", product_price)
                            c2.metric("Rating", f"⭐ {product_rating}")
                            
                            st.divider()
                            st.markdown(f"### 🖼️ Image Gallery ({len(image_list)} images found)")
                            st.info("লিংক কপি করতে নিচের বক্সে ক্লিক করুন।")

                            cols = st.columns(3)
                            for i, img_link in enumerate(image_list):
                                with cols[i % 3]:
                                    with st.container(border=True):
                                        st.image(img_link, use_container_width=True)
                                        st.caption(f"Image Link #{i+1}")
                                        st.code(img_link, language=None)
                                        
                        else:
                            st.error(f"দুঃখিত, কোনো তথ্য পাওয়া যায়নি।")
                            st.markdown(f"**কারণ হতে পারে:**\n1. ASIN `{asin}` এই ডোমেইনে নেই।\n2. SerpApi লিমিট শেষ।")
                            if error_log:
                                st.caption(f"Debug Log: {error_log}")
                                
                except Exception as e:
                    st.error(f"System Error: {e}")

# ==========================
# TAB 3: AFFILIATE CODE GENERATOR
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
# TAB 4: CONTENT PLANNER (Updated with Grid Card View)
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
# TAB 5: BLOG FORMATTER (New Feature)
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
# TAB 6: IMAGE TO TEXT (OCR)
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


