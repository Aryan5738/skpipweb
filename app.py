import os
import time
import threading
import datetime
from flask import Flask, request, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

app = Flask(__name__)

# --- GLOBAL LOGS (The Brain) ---
logs = []

def add_log(msg):
    # Ye function global manager ki tarah kaam karega
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    logs.append(f"[{timestamp}] {msg}")
    # Memory bachane ke liye sirf last 50 logs rakhenge
    if len(logs) > 50:
        logs.pop(0)

# --- DRIVER SETUP ---
def get_driver():
    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    chromium_path = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    service = Service(chromedriver_path)
    try:
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        add_log(f"Driver Error: {str(e)}")
        return None

def parse_cookies(cookie_string):
    cookies = []
    try:
        # Netscape format support
        lines = cookie_string.split('\n')
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 7:
                cookies.append({'name': parts[5], 'value': parts[6].strip(), 'domain': parts[0]})
        
        # Key=Value format support
        if not cookies:
            items = cookie_string.split(';')
            for item in items:
                if '=' in item:
                    name, value = item.strip().split('=', 1)
                    cookies.append({'name': name, 'value': value, 'domain': '.facebook.com'})
        return cookies
    except:
        return []

# --- UPDATED POPUP BYPASS LOGIC ---
def bypass_popups(driver):
    # Yahan humne st.write hata kar add_log laga diya hai
    add_log("Scanning for popups/PIN...") 
    
    try:
        # 1. Sabse pehle ESC button dabayein (Universal close)
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        
        # 2. Aapke diye gaye XPaths + Extra Safety
        xpaths = [
            "//div[@role='button']//span[contains(text(), 'Continue')]",
            "//*[contains(text(), 'restore messages')]",
            "//div[@aria-label='Continue']",
            "//div[@aria-label='Close']",
            "//div[@aria-label='close']", # Lowercase variant
            "//*[text()='Not Now']",
            "//i[contains(@class, 'x1b0d499')]" # 'X' icon ka class
        ]
        
        for xpath in xpaths:
            try:
                btns = driver.find_elements(By.XPATH, xpath)
                for btn in btns:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        add_log(f"Popup Closed: {xpath}")
                        time.sleep(1)
            except:
                pass
    except Exception as e:
        # add_log(f"Popup check error: {e}") 
        pass

def send_message_safely(driver, text):
    selectors = [
        'div[aria-label="Message"]', 
        'div[role="textbox"]', 
        'div[contenteditable="true"]', 
        'p[class*="xdj266r"]'
    ]
    msg_box = None
    for selector in selectors:
        try:
            msg_box = driver.find_element(By.CSS_SELECTOR, selector)
            if msg_box: break
        except: continue
            
    if msg_box:
        try:
            driver.execute_script("arguments[0].focus();", msg_box)
            actions = ActionChains(driver)
            actions.send_keys(text)
            time.sleep(1)
            actions.send_keys(Keys.RETURN)
            actions.perform()
            return True
        except: return False
    return False

def run_bot(cookie_str, url, msg, delay):
    add_log("Bot Starting...")
    driver = get_driver()
    if not driver: return

    try:
        driver.get("https://www.facebook.com/")
        cookies = parse_cookies(cookie_str)
        for c in cookies:
            try: driver.add_cookie(c)
            except: pass
        
        add_log("Loading Chat URL...")
        driver.get(url)
        time.sleep(8)

        # Pehli baar popup check
        bypass_popups(driver) 
        time.sleep(2)

        add_log("Starting Loop...")
        while True:
            # Har message se pehle popup/PIN check karega
            bypass_popups(driver)
            
            success = send_message_safely(driver, msg)
            if success:
                add_log(f"Message Sent: {msg}")
                time.sleep(int(delay))
            else:
                add_log("Retrying (PIN check)...")
                bypass_popups(driver)
                time.sleep(5)
            
    except Exception as e:
        add_log(f"Critical Error: {e}")
    finally:
        driver.quit()
        add_log("Bot Stopped.")

# --- FLASK UI ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cookie = request.form.get('cookie')
        url = request.form.get('url')
        msg = request.form.get('msg')
        delay = request.form.get('delay')
        
        t = threading.Thread(target=run_bot, args=(cookie, url, msg, delay))
        t.start()
        
        return "<h1>Bot Started! <a href='/logs'>Check Logs</a></h1>"

    return '''
    <html>
        <head><title>FB Bot (Flask)</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h2>🚀 FB Sender (Flask + Global Logs)</h2>
            <form method="POST">
                <p><b>Cookie:</b><br><textarea name="cookie" rows="5" cols="50" required></textarea></p>
                <p><b>Chat URL:</b><br><input type="text" name="url" size="50" required></p>
                <p><b>Message:</b><br><input type="text" name="msg" required></p>
                <p><b>Delay (sec):</b><br><input type="number" name="delay" value="10" required></p>
                <button type="submit" style="background: green; color: white; padding: 10px;">Start Bot</button>
            </form>
            <br><a href="/logs"><button>View Logs</button></a>
        </body>
    </html>
    '''

@app.route('/logs')
def show_logs():
    return f'''
    <html>
        <head><meta http-equiv="refresh" content="2"></head>
        <body style="font-family: monospace; padding: 20px; background: #f4f4f4;">
            <h2>📜 Live Global Logs</h2>
            <div style="background: white; padding: 15px; border: 1px solid #ccc;">
                {"<br>".join(logs)}
            </div>
            <br><a href="/">Back</a>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    
