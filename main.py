import streamlit as st
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


# ======================================================
# BROWSERLESS DRIVER (YOUR API KEY INCLUDED)
# ======================================================
def get_driver():
    API_KEY = "2TQSpVJyH2BZADb41f4d46d2fb237812fb263f112fa69ef25"

    opts = webdriver.ChromeOptions()
    opts.set_capability("browserless:token", API_KEY)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-gpu")

    driver = webdriver.Remote(
        command_executor="https://chrome.browserless.io/webdriver",
        options=opts
    )
    return driver


# ======================================================
# COOKIE LOADER
# ======================================================
def load_cookies(driver, cookies):
    driver.get("https://facebook.com")
    time.sleep(4)

    for c in cookies:
        try:
            driver.add_cookie({"name": c["name"], "value": c["value"]})
        except:
            pass

    driver.refresh()
    time.sleep(4)
    return True


# ======================================================
# MESSAGE SENDER
# ======================================================
def send_message(driver, msg_url, messages, delay, log_callback):
    try:
        log_callback("🔗 Opening Messenger chat...", "blue")
        driver.get(msg_url)
        time.sleep(5)

        input_box = driver.find_element(By.XPATH, "//div[@role='textbox']")
        log_callback("📩 Message box found!", "green")

        # Send messages line-by-line
        for msg in messages:
            log_callback(f"✏ Typing: {msg}", "white")

            for ch in msg:
                input_box.send_keys(ch)
                time.sleep(0.04)

            input_box.send_keys(Keys.ENTER)
            log_callback("✔ Message sent!", "green")
            time.sleep(delay)

        return True

    except Exception as e:
        log_callback(f"❌ ERROR: {str(e)}", "red")
        return False


# ======================================================
# STREAMLIT UI
# ======================================================
st.set_page_config(
    page_title="FB Auto Messenger",
    page_icon="💬",
    layout="wide"
)

st.markdown("""
    <h1 style='text-align:center;color:#4CAF50;'>📨 Facebook Auto Messenger Bot</h1>
    <p style='text-align:center;'>Cookies + Selenium + Browserless + HTML Logs UI</p>
    <hr>
""", unsafe_allow_html=True)


# Input fields
msg_url = st.text_input("🔗 Messenger Chat URL")
messages_text = st.text_area("💬 Messages (line-by-line)", "Hello\nHow are you?")
delay = st.number_input("⏱ Delay (seconds)", 1, 20, 3)

# PRELOADED COOKIE JSON (your cookies)
cookie_json = """
[
{"name":"datr","value":"x-4VZ4GTwgXotc2K6i8LtUGI"},
{"name":"sb","value":"x-4VZxbqkmCAawFwsNZch1cr"},
{"name":"m_pixel_ratio","value":"2"},
{"name":"ps_l","value":"1"},
{"name":"ps_n","value":"1"},
{"name":"usida","value":"eyJ2ZXIiOjEsImlkIjoiQXNwa3poZzFqMWYwbmsiLCJ0aW1lIjoxNzM2MDIyNjM2fQ=="},
{"name":"oo","value":"v1"},
{"name":"vpd","value":"v1;634x360x2"},
{"name":"x-referer","value":"..."},
{"name":"pas","value":"..."},
{"name":"c_user","value":"61580725287646"},
{"name":"xs","value":"6:lx_yX9F76iRb_Q:2:1761452052:-1:-1"},
{"name":"fr","value":"..."},
{"name":"locale","value":"en_GB"},
{"name":"fbl_st","value":"100427941;T:29386432"},
{"name":"wl_cbv","value":"v2;client_version:2971;timestamp:1763185966"}
]
"""
cookies = json.loads(cookie_json)


# ------------------------------------------------------
# HTML LOG WINDOW
# ------------------------------------------------------
log_html = """
<div style="
    background-color:#000;
    color:white;
    padding:15px;
    border-radius:10px;
    height:450px;
    overflow-y:scroll;
    font-family:monospace;
    border:2px solid #4CAF50;">
"""

log_box = st.empty()


def add_log(message, color="white"):
    global log_html
    log_html += f"<p style='color:{color};margin:2px;'>{message}</p>"
    log_box.markdown(log_html + "</div>", unsafe_allow_html=True)


# ------------------------------------------------------
# START BUTTON
# ------------------------------------------------------
if st.button("🚀 START BOT"):
    add_log("🚀 Starting Browserless driver...", "yellow")
    driver = get_driver()
    add_log("✔ Driver Ready!", "green")

    add_log("🔐 Injecting cookies...", "yellow")
    load_cookies(driver, cookies)
    add_log("✔ Cookies Loaded!", "green")

    messages = [m.strip() for m in messages_text.split("\n") if m.strip()]

    add_log("💬 Starting message sending...", "yellow")
    result = send_message(driver, msg_url, messages, delay, add_log)

    if result:
        add_log("🎉 ALL MESSAGES SENT SUCCESSFULLY!", "lightgreen")
    else:
        add_log("❌ FAILED!", "red")
