import streamlit as st
from openai import OpenAI
import wikipedia
from gtts import gTTS
from io import BytesIO
import re
import os

# Secure API key from Streamlit secrets or env
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Wikipedia language setup
wikipedia.set_lang("en")

def get_wikivoyage_summary(destination):
    try:
        return wikipedia.summary(destination + " (Wikivoyage)", sentences=10)
    except Exception as e:
        return f"Error fetching summary: {e}"

def get_wikivoyage_url(destination):
    return f"https://en.wikivoyage.org/wiki/{destination.replace(' ', '_')}"

def generate_conversation(content, personas):
    persona_intro = ", ".join(personas)
    messages = [
        {"role": "system", "content": f"You are a travel radio station with hosts {persona_intro}. Speak naturally. Do not use asterisks or em dashes."},
        {"role": "user", "content": f"Have a lively 3-minute radio-style conversation about this Wikivoyage article:\n\n{content}"}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.8
    )
    raw_text = response.choices[0].message.content
    clean_text = re.sub(r"[*—–]+", "", raw_text)
    return clean_text

def synthesize_gtts_audio(full_text):
    tts = gTTS(text=full_text, lang='en')
    buf = BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Destination Radio", layout="centered")

st.markdown(
    """
    <style>
    .radio-box {
        background-color: #1c1c1c;
        color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.6);
        text-align: center;
    }
    .now-playing {
        font-size: 20px;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True
)

st.title("Destination Radio")
st.caption("AI-powered travel podcast using Wikivoyage articles")

st.markdown("<div class='radio-box'>", unsafe_allow_html=True)

destination = st.text_input("Enter a destination", placeholder="e.g., Tokyo, Lisbon")

personas = st.multiselect(
    "Choose your radio hosts",
    ["Local Historian", "Luxury Travel Blogger", "Backpacker", "Food Critic", "Cultural Anthropologist"],
    default=["Local Historian", "Luxury Travel Blogger"]
)

if st.button("Generate Podcast"):
    if not destination:
        st.warning("Please enter a destination.")
    else:
        with st.spinner("Generating your podcast..."):
            article = get_wikivoyage_summary(destination)
            if "Error" in article:
                st.error(article)
            else:
                conversation = generate_conversation(article, personas)
                audio_fp = synthesize_gtts_audio(conversation)
                st.markdown(f"<div class='now-playing'>Now Playing: {destination}</div>", unsafe_allow_html=True)
                st.audio(audio_fp, format="audio/mp3")

                with st.expander("Show transcript"):
                    st.markdown(conversation)

                st.markdown(f"[View original Wikivoyage article]({get_wikivoyage_url(destination)})")

st.markdown("</div>", unsafe_allow_html=True)
