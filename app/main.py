from dotenv import load_dotenv
load_dotenv()

import logging
import streamlit as st
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from utils.sqlite_script import copy_captcha_table, get_next_uncorrected, update_corrected_text, get_history
from utils.utils import decode_image
from utils.gdrive import upload_to_gdrive

# --- UI Starts Here ---
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    copy_captcha_table()
st.set_page_config(page_title="Captcha Correction", layout="wide")

st.title("🧠 CAPTCHA Correction Tool")

# --- Backup Button ---
if st.sidebar.button("💾 Backup Database"):
    try:
        upload_to_gdrive()
        st.sidebar.success(f"Backup created!")
    except Exception as e:
        st.sidebar.error(f"❌ Backup failed: {e}")

# Sidebar history
st.sidebar.header("📝 Correction History")

limit = 10
page = st.sidebar.number_input("Page", min_value=1, step=1)
offset = (page - 1) * limit

history_df = get_history(offset, limit)

for _, row in history_df.iterrows():
    with st.sidebar.expander(f"Captcha ID: {row['id']}", expanded=True):
        try:
            img_bytes = decode_image(row['img'])
            st.image(img_bytes, width=150)
        except Exception as e:
            st.error(f"⚠️ Failed to decode image: {e}")

        st.write(f"Corrected Text: `{row['corrected_text']}`")
        

# Main section
# Only fetch a new record if not already loaded or after submission
if "current_record" not in st.session_state or st.session_state.get("clear_input", False):
    record = get_next_uncorrected()
    if record:
        st.session_state.current_record = {
            "captcha_id": record[0],
            "image_data": record[1]
        }
    else:
        st.session_state.current_record = None

record = st.session_state.current_record

# Initialize session state vars
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "clear_input" not in st.session_state:
    st.session_state.clear_input = False
if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = True
if "username_error" not in st.session_state:
    st.session_state.username_error = False
if "username_submitted" not in st.session_state:
    st.session_state.username_submitted = False
if "username_validated" not in st.session_state:
    st.session_state.username_validated = False

# Clear input *before* widget is instantiated
if st.session_state.clear_input:
    st.session_state.user_input = ""
    st.session_state.clear_input = False

def handle_submit():
    username = st.session_state.get("username_input", "").strip()
    if username == "":
        st.session_state.username_error = True
    else:
        st.session_state.username_error = False
        st.session_state.username_validated = True  # Just flag it
        # Do NOT call st.rerun() here

# Dialog
@st.dialog("Username")
def enter_username():
    with st.form("dialog_form"):
        st.text_input("Enter your username:", key="username_input")

        if st.form_submit_button("Submit"):
            username = st.session_state.get("username_input", "").strip()
            if username == "":
                st.session_state.username_error = True
            else:
                st.session_state.username_error = False
                st.session_state.username_validated = True  # Just flag it
        
        # Handle auto-close logic (run outside the callback)
        if st.session_state.username_validated:
            st.session_state.username_validated = False  # reset for next time
            st.toast("Closing dialog in 2 seconds...", icon="⏳")
            time.sleep(2)
            st.session_state.show_dialog = False
            st.rerun()

        if st.session_state.username_error:
            st.error("Please input your username to proceed.")

# Trigger dialog
if st.session_state.show_dialog:
    enter_username()

if record:
    captcha_id = record["captcha_id"]
    image = decode_image(record["image_data"])

    with st.form("captcha_form"):
        if image:
            st.image(image, caption=f"Captcha ID: {captcha_id}", use_container_width=True)
        else:
            st.error("⚠️ Failed to load image.")

        st.text_input("Enter the correct captcha text:", key="user_input")

        if st.form_submit_button("Submit"):
            user_input = st.session_state.user_input.strip()
            if user_input:
                info = {
                    "captcha_id": captcha_id,
                    "corrected_text": user_input,
                    "status": 2,
                    "updated_by": st.session_state.get("username_input", "unknown_user")
                }
                update_corrected_text(info)
                st.session_state.clear_input = True
                st.session_state.current_record = None
                st.rerun()
            else:
                st.warning("Please enter a value before submitting.")
else:
    st.info("🎉 No more uncorrected CAPTCHAs.")
