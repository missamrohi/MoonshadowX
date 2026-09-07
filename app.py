import streamlit as st
import json
import re
import time
import urllib.parse
import google.generativeai as genai
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(page_title="Moonshadow X Auto-Generator & Twister", page_icon="🌙", layout="centered")

st.title("🌙 Moonshadow X Auto-Generator")
st.write("Generate 10 original trending posts inspired by current X.com conversations using your campaign keywords and hashtag.")

# 1. SECURITY: Load API key silently from Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.error("⚠️ System Configuration Error: Missing API Key in Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key.strip())

# 2. RATE LIMITING: Track user actions in session state
if "last_generation_time" not in st.session_state:
    st.session_state.last_generation_time = 0

# --- USER INPUTS ---
col1, col2 = st.columns(2)

with col1:
    keywords = st.text_input(
        "Trending Keywords (Line 2)", 
        value="CHAN BETWEEN KEY AND JAY",
        help="Campaign keywords to search and include."
    )

with col2:
    hashtags = st.text_input(
        "Episode Hashtag (Line 3)", 
        value="#MoonshadowSeriesEP5",
        help="Campaign hashtag to search and include."
    )

twist_angle = st.selectbox("Tone / Focus Angle", [
    "Puns & Funny Spins",
    "Pure Stan Hype & Screaming",
    "Sarcastic / Unhinged Reactions",
    "Theory, Angst & Plot Suspense",
    "Emotional & Character Dynamic Analysis"
])

# --- HELPER: COPY TO CLIPBOARD BUTTON COMPONENT ---
def render_action_buttons(full_text, button_idx):
    encoded_tweet = urllib.parse.quote(full_text)
    tweet_url = f"https://x.com/intent/tweet?text={encoded_tweet}"
    
    # Escape quotes and newlines for JavaScript
    js_safe_text = json.dumps(full_text)
    
    html_code = f"""
    <div style="display: flex; gap: 10px; align-items: center; margin-top: 8px;">
        <a href="{tweet_url}" target="_blank" style="
            background-color: #1d9bf0; 
            color: white; 
            padding: 8px 16px; 
            text-decoration: none; 
            border-radius: 20px; 
            font-size: 14px; 
            font-weight: bold;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            display: inline-block;">
            🚀 Tweet Option #{button_idx}
        </a>
        <button id="copy-btn-{button_idx}" onclick='copyToClipboard({js_safe_text}, "copy-btn-{button_idx}")' style="
            background-color: #2f3336; 
            color: white; 
            padding: 8px 16px; 
            border: 1px solid #53575b; 
            border-radius: 20px; 
            font-size: 14px; 
            font-weight: bold;
            cursor: pointer;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            📋 Copy
        </button>
    </div>

    <script>
    function copyToClipboard(text, btnId) {{
        navigator.clipboard.writeText(text).then(function() {{
            var btn = document.getElementById(btnId);
            var originalText = btn.innerHTML;
            btn.innerHTML = "✅ Copied!";
            btn.style.backgroundColor = "#00ba7c";
            setTimeout(function() {{
                btn.innerHTML = originalText;
                btn.style.backgroundColor = "#2f3336";
            }}, 2000);
        }}).catch(function(err) {{
            console.error('Could not copy text: ', err);
        }});
    }}
    </script>
    """
    components.html(html_code, height=50)

# --- DYNAMIC CHARACTER LIMIT CALCULATION ---
keywords_clean = keywords.strip()
hashtags_clean = hashtags.strip()

lines_overhead = 3 if (keywords_clean and hashtags_clean) else 2
suffix_length = len(keywords_clean) + len(hashtags_clean) + lines_overhead
max_post_length = max(50, 280 - suffix_length)

st.caption(f"📏 Max text length per post: **{max_post_length} characters** (leaving room for keywords and hashtags within X's 280 limit).")

# Direct link to view real-time live posts on X for inspiration
if keywords_clean or hashtags_clean:
    search_query = f"{keywords_clean} {hashtags_clean}".strip()
    x_search_url = f"https://x.com/search?q={urllib.parse.quote(search_query)}&f=live"
    st.markdown(f"🔍 [Click here to view live posts on X.com for `{search_query}`]({x_search_url})")

st.markdown("---")

# --- GENERATION LOGIC ---
if st.button("🔥 Generate 10 Unique Posts (5 EN + 5 HK CAN)", type="primary"):
    current_time = time.time()
    cooldown_seconds = 10
    
    if current_time - st.session_state.last_generation_time < cooldown_seconds:
        wait_time = int(cooldown_seconds - (current_time - st.session_state.last_generation_time))
        st.warning(f"⏳ Please wait {wait_time} seconds before generating again.")
    elif not keywords_clean and not hashtags_clean:
        st.warning("Please enter at least keywords or a hashtag.")
    else:
        st.session_state.last_generation_time = current_time
        
        with st.spinner("Fast-generating 10 distinct posts using Gemini 3.6 Flash..."):
            try:
                # USING GEMINI-3.6-FLASH
                model = genai.GenerativeModel("gemini-3.6-flash")

                prompt = f"""
                You are a top social media trend strategist and superfan for the TV series 'Moonshadow'.
                Your task is to generate 10 FRESH, DISTINCT, high-engagement posts for X (Twitter) centered around the trending campaign:
                - Keywords: "{keywords_clean}"
                - Hashtag: "{hashtags_clean}"

                OUTPUT REQUIREMENT:
                Generate EXACTLY 10 unique posts split into two completely independent sets:

                1. POSTS 1-5 (Native English Fandom Style):
                   - Written in authentic Stan Twitter / X style (casual, lowercase emphasis, natural reactions, zero AI clichés).
                   - Focus on unique jokes, theories, or reactions popular in international fandoms.

                2. POSTS 6-10 (Hong Kong Cantonese Fandom Style):
                   - CRITICAL: DO NOT TRANSLATE or rephrase Posts 1-5! These MUST be completely original Cantonese posts written from scratch with totally different angles, jokes, or theories.
                   - Written in natural, colloquial Hong Kong Cantonese (spoken HK Chinese / 廣東話) as used by local HK fans on Threads/X (e.g., 睇到喊、癲咗、黐線、張力拉滿、CP感、鎖死、呢幕真係、好正).
                   - Reflect how Hong Kong fans uniquely express hype and emotional reactions.

                GENERAL RULES:
                - Focus Angle: {twist_angle}.
                - Maximum text length for EACH post body: MUST NOT exceed {max_post_length} characters.
                - DO NOT include the campaign keywords or hashtags inside the post body (they will be appended automatically).

                CRITICAL DIRECTIVE:
                Output MUST be strictly a valid JSON array of EXACTLY 10 strings. Do not include markdown code blocks or extra text.
                """

                response = model.generate_content(prompt)
                raw_content = response.text.strip()

                # Clean JSON string
                clean_json = re.sub(r'^```json\s*|\s*```$', '', raw_content, flags=re.MULTILINE)
                captions = json.loads(clean_json)

                st.subheader("🎉 Ready-to-Post Captions")

                # Organize into Tab Views
                tab_en, tab_hk = st.tabs(["🇬🇧 Native English (5 Unique)", "🇭🇰 HK Cantonese (5 Unique)"])

                # Render English Posts inside Tab 1 (Indices 0..4)
                with tab_en:
                    for idx in range(5):
                        if idx < len(captions):
                            caption_text = captions[idx]
                            suffix_parts = [p for p in [keywords_clean, hashtags_clean] if p]
                            suffix = "\n".join(suffix_parts)
                            full_tweet = f"{caption_text.strip()}\n\n{suffix}" if suffix else caption_text.strip()

                            st.markdown(f"**English Option #{idx+1}** ({len(full_tweet)} / 280 chars)")
                            with st.container(border=True):
                                st.text(full_tweet)
                            
                            # Interactive Tweet + Copy buttons
                            render_action_buttons(full_tweet, idx + 1)
                            st.write("")

                # Render Cantonese Posts inside Tab 2 (Indices 5..9)
                with tab_hk:
                    for idx in range(5, 10):
                        if idx < len(captions):
                            caption_text = captions[idx]
                            suffix_parts = [p for p in [keywords_clean, hashtags_clean] if p]
                            suffix = "\n".join(suffix_parts)
                            full_tweet = f"{caption_text.strip()}\n\n{suffix}" if suffix else caption_text.strip()

                            st.markdown(f"**HK Cantonese Option #{idx+1}** ({len(full_tweet)} / 280 chars)")
                            with st.container(border=True):
                                st.text(full_tweet)
                            
                            # Interactive Tweet + Copy buttons
                            render_action_buttons(full_tweet, idx + 1)
                            st.write("")

            except Exception as e:
                st.error(f"Error generating posts: {str(e)}")
