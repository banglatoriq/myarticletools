import streamlit as st
from serpapi import GoogleSearch
import re
import json
import os
import pandas as pd

# --- পেজের কনফিগারেশন ---
st.set_page_config(page_title="SEO & Amazon Tool", page_icon="🛠️", layout="wide")
st.title("🛠️ All-in-One Content & Affiliate Tool")

# --- সাইডবার সেটিংস ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # --- API Key Management (Save Option Added) ---
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

# --- ASIN বের করার ফাংশন ---
def extract_asin(url):
    regex_list = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
        r"dp/([A-Z0-9]{10})"
    ]
    for regex in regex_list:
        match = re.search(regex, url)
        if match:
            return match.group(1)
    return None

# --- Local Storage Functions for Content Planner ---
PLANNER_FILE = 'content_planner.json'

def load_planner_data():
    if os.path.exists(PLANNER_FILE):
        try:
            with open(PLANNER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_planner_data(data):
    with open(PLANNER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- মেইন অ্যাপ এরিয়া (Tabs) ---
# নতুন ট্যাব যোগ করা হয়েছে: "🗂️ Content Planner"
tab_seo, tab_amazon, tab_affiliate, tab_planner = st.tabs(["🔎 SEO Research", "🛒 Amazon Product Info", "🎨 Affiliate Code Gen", "🗂️ Content Planner"])

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
# TAB 2: AMAZON PRODUCT INFO
# ==========================
with tab_amazon:
    st.subheader("Amazon Product Details Fetcher")
    st.info("💡 অ্যামাজন লিংক দিন, আমরা টাইটেল, ইমেজ এবং রেটিং নিয়ে আসব।")
    
    product_url = st.text_input("Paste Amazon Product Link:", placeholder="https://www.amazon.com/dp/B08...")
    amazon_submit = st.button("📦 Get Product Info")

    # --- Helper Function for HD Images ---
    def get_high_res_image(img_url):
        if not img_url or img_url == "N/A":
            return "N/A"
        clean_url = re.sub(r'\._[A-Z]{2}.+?\.', '.', img_url)
        return clean_url

    if amazon_submit:
        if not api_key:
            st.error("⚠️ SerpApi Key প্রয়োজন।")
        elif not product_url:
            st.warning("⚠️ লিংক দিন।")
        else:
            asin = extract_asin(product_url)
            if not asin:
                st.error("❌ লিংকটি সঠিক নয় বা ASIN পাওয়া যায়নি।")
            else:
                try:
                    with st.spinner(f'Fetching details for ASIN: {asin}...'):
                        found_data = False
                        error_log = ""

                        # Step 1: Amazon Product API
                        try:
                            params = {
                                "engine": "amazon_product",
                                "product_id": asin,
                                "domain": "www.amazon.com",
                                "api_key": api_key
                            }
                            search = GoogleSearch(params)
                            results = search.get_dict()

                            if "error" in results:
                                raise Exception(results["error"])

                            if "product_result" in results:
                                product = results["product_result"]
                                title = product.get("title", "N/A")
                                raw_image = "N/A"
                                if "images" in product and len(product["images"]) > 0:
                                    first_img = product["images"][0]
                                    raw_image = first_img.get("link") if isinstance(first_img, dict) else first_img
                                else:
                                    raw_image = product.get("main_image", "N/A")
                                image = get_high_res_image(raw_image)
                                rating = product.get("rating", "N/A")
                                reviews = product.get("reviews", "N/A")
                                price = "Check on Amazon"
                                if "price" in product:
                                    price = product["price"]
                                elif "prices" in results and len(results["prices"]) > 0:
                                    price = results["prices"][0].get("price", "Check on Amazon")
                                found_data = True
                        except Exception as e:
                            error_log = f"Amazon Product API: {str(e)}"

                        # Step 2: Amazon Search API Fallback
                        if not found_data:
                            try:
                                params_fallback = {
                                    "engine": "amazon",
                                    "q": asin,
                                    "domain": "www.amazon.com",
                                    "api_key": api_key
                                }
                                search_fallback = GoogleSearch(params_fallback)
                                results = search_fallback.get_dict()
                                
                                if "organic_results" in results and len(results["organic_results"]) > 0:
                                    item = results["organic_results"][0]
                                    title = item.get("title", "N/A")
                                    raw_image = item.get("thumbnail", "N/A")
                                    image = get_high_res_image(raw_image)
                                    rating = item.get("rating", "N/A")
                                    reviews = item.get("reviews", "N/A")
                                    price = item.get("price", "Check on Amazon")
                                    found_data = True
                            except Exception as e:
                                error_log += f" | Amazon Search API: {str(e)}"

                        # Step 3: Google Search Fallback
                        if not found_data:
                            try:
                                params_google = {
                                    "engine": "google",
                                    "q": f"site:amazon.com {asin}",
                                    "location": "United States",
                                    "google_domain": "google.com",
                                    "gl": "us",
                                    "hl": "en",
                                    "api_key": api_key
                                }
                                search_google = GoogleSearch(params_google)
                                results = search_google.get_dict()
                                
                                if "organic_results" in results and len(results["organic_results"]) > 0:
                                    item = results["organic_results"][0]
                                    raw_title = item.get("title", "N/A")
                                    title = raw_title.replace("Amazon.com: ", "").replace("Amazon.com : ", "")
                                    raw_image = item.get("thumbnail", "N/A")
                                    image = get_high_res_image(raw_image)
                                    rating = "N/A"
                                    reviews = "N/A"
                                    price = "Check on Amazon"
                                    if "rich_snippet" in item and "top" in item["rich_snippet"]:
                                        extensions = item["rich_snippet"]["top"].get("detected_extensions", {})
                                        rating = extensions.get("rating", "N/A")
                                        reviews = extensions.get("reviews", "N/A")
                                        price = extensions.get("price", "Check on Amazon")
                                    found_data = True
                            except Exception as e:
                                error_log += f" | Google Fallback: {str(e)}"

                        if found_data:
                            st.success("✅ প্রোডাক্ট পাওয়া গেছে!")
                            col_img, col_data = st.columns([1, 2])
                            with col_img:
                                st.image(image, caption="Product Image")
                            with col_data:
                                st.markdown(f"### {title}")
                                st.markdown(f"**Rating:** ⭐ {rating} ({reviews} reviews)")
                                st.markdown(f"**Price:** {price}")
                                st.markdown(f"**ASIN:** `{asin}`")
                            st.divider()
                            st.subheader("📋 Copy this Table for Blog")
                            table_md = f"""
| Feature | Details |
| :--- | :--- |
| **Product Name** | {title} |
| **Image URL** | [View Image]({image}) |
| **Rating** | {rating}/5 |
| **Price** | {price} |
"""
                            st.code(table_md, language="markdown")
                        else:
                            st.error(f"দুঃখিত, প্রোডাক্টটি খুঁজে পাওয়া যায়নি। (ASIN: {asin})")
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
        st.components.v1.html(full_html_output, height=600, scrolling=True)

# ==========================
# TAB 4: CONTENT PLANNER (Updated with Grid Card View)
# ==========================
with tab_planner:
    st.header("🗂️ Keyword Cluster & Content Planner")
    st.info("আপনার কিওয়ার্ড ক্লাস্টারগুলো এখানে সেভ রাখুন এবং কাজের অগ্রগতি ট্র্যাক করুন। ডাটা অটোমেটিক সেভ থাকবে।")

    # Load Data
    if 'planner_data' not in st.session_state:
        st.session_state.planner_data = load_planner_data()

    # --- Dashboard Metrics ---
    # Metric Logic Updated: Count keywords (articles) instead of clusters
    total_keywords_count = 0
    completed_keywords_count = 0

    for item in st.session_state.planner_data:
        # Get list of all keywords in this cluster
        kws = [k.strip() for k in item.get('keywords', '').split(';') if k.strip()]
        total_keywords_count += len(kws)
        
        # Get count of checked keywords
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
        st.write("") # Spacer to align
        st.write("") # Spacer to align
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
                # Regex to parse the specific format provided by user
                # Matches: Cluster Label : [Match Group 1] Keywords: [Match Group 2]
                matches = re.findall(r"Cluster Label\s*[:\|]\s*(.*?)\s*Keywords\s*[:\|]\s*(.*)", raw_text, re.IGNORECASE | re.MULTILINE)
                
                if matches:
                    count = 0
                    for match in matches:
                        label = match[0].strip()
                        keywords = match[1].strip()
                        # Add to session state if not exists (simple duplicate check by label)
                        if not any(d['label'] == label for d in st.session_state.planner_data):
                            st.session_state.planner_data.append({
                                'label': label,
                                'keywords': keywords,
                                'done': False,
                                'checked_keywords': [] # List to track completed sub-keywords
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
                    
                    # Try to find relevant columns - SMART SELECTION
                    label_cols = [c for c in df.columns if 'label' in c.lower() or 'cluster' in c.lower()]
                    kw_cols = [c for c in df.columns if 'keyword' in c.lower()]
                    
                    # Default selection
                    label_col = label_cols[0] if label_cols else None
                    kw_col = None

                    # Smart selection for keyword column (avoid counts like '25')
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
    
    # Filtering
    filter_status = st.radio("Filter:", ["All", "Pending", "Completed"], horizontal=True)
    
    display_data = []
    for i, item in enumerate(st.session_state.planner_data):
        item['original_index'] = i # Keep track of index for updating
        if filter_status == "All":
            display_data.append(item)
        elif filter_status == "Pending" and not item['done']:
            display_data.append(item)
        elif filter_status == "Completed" and item['done']:
            display_data.append(item)

    if not display_data:
        st.info("No clusters found matching your filter.")
    else:
        # Create a grid with 3 columns
        cols = st.columns(3)
        
        for i, item in enumerate(display_data):
            idx = item['original_index']
            col = cols[i % 3] # Distribute items across 3 columns
            
            with col:
                # CARD CONTAINER
                with st.container(border=True):
                    # --- Header Section ---
                    h_col1, h_col2 = st.columns([0.8, 0.2])
                    
                    with h_col1:
                        # Cluster Title with Strikethrough if done
                        title_style = "text-decoration: line-through; color: gray;" if item['done'] else "font-weight: bold; color: #1f77b4; font-size: 16px;"
                        st.markdown(f"<div style='{title_style}'>{item['label']}</div>", unsafe_allow_html=True)
                        
                        # Cluster Done Checkbox
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
                    # Using container with fixed height for scroll
                    with st.container(height=250, border=False):
                        keywords_list = [k.strip() for k in item['keywords'].split(';') if k.strip()]
                        
                        if not keywords_list:
                            st.caption("No keywords.")
                        else:
                            # Sub-task Checkboxes
                            checked_kws = set(item.get('checked_keywords', []))
                            
                            for kw in keywords_list:
                                # Unique key for each checkbox: cluster_index + keyword
                                kw_key = f"chk_{idx}_{hash(kw)}"
                                is_checked = kw in checked_kws
                                
                                new_checked = st.checkbox(kw, value=is_checked, key=kw_key)
                                
                                if new_checked != is_checked:
                                    if new_checked:
                                        item.setdefault('checked_keywords', []).append(kw)
                                    else:
                                        item.setdefault('checked_keywords', []).remove(kw)
                                    save_planner_data(st.session_state.planner_data)
                                    # We don't rerun here to allow quick multiple ticks without reload lag
                    
                    # --- Edit Keywords Expander (Bottom of Card) ---
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