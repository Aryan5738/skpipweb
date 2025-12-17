import os
import time
import threading
import datetime
from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

app = Flask(__name__)

# --- GLOBAL LOGS (Memory Optimized) ---
logs = []

def add_log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    logs.append(f"[{timestamp}] {msg}")
    # Memory leak bachane ke liye sirf last 50 logs rakhenge
    if len(logs) > 50:
        logs.pop(0)

# --- DRIVER SETUP (Render Crash Proof 🛡️) ---
def get_driver():
    chrome_options = Options()
    
    # 1. Anti-Detection User Agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    # 2. Critical Memory Saving Flags (Crash Rokne ke liye)
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage") # Sabse zaroori flag Render ke liye
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions") # Extension memory khate hain
    chrome_options.add_argument("--disable-notifications") # Notifications block
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disk-cache-size=1") # Disk cache off
    chrome_options.add_argument("--disable-application-cache")
    
    # 3. Screen Size (Thoda chota rakha hai taaki RAM kam use ho)
    chrome_options.add_argument("--window-size=1280,720")
    
    # 4. Anti-Bot Detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 5. Paths (From Dockerfile)
    chromium_path = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    service = Service(chromedriver_path)
    try:
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        add_log(f"Driver Init Error: {str(e)}")
        return None

# --- COOKIE PARSER ---
def parse_cookies(cookie_string):
    cookies = []
    try:
        lines = cookie_string.split('\n')
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 7:
                cookies.append({'name': parts[5], 'value': parts[6].strip(), 'domain': parts[0]})
        
        if not cookies:
            items = cookie_string.split(';')
            for item in items:
                if '=' in item:
                    name, value = item.strip().split('=', 1)
                    cookies.append({'name': name, 'value': value, 'domain': '.facebook.com'})
        return cookies
    except:
        return []

# --- POPUP & PIN BYPASS LOGIC (Updated) ---
def bypass_popups(driver):
    add_log("Scanning for PIN/Popups...")
    
    try:
        # 1. ESC Key (Universal Closer)
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        
        # 2. XPaths for all types of Popups/PINs
        xpaths = [
            "//div[@role='button']//span[contains(text(), 'Continue')]",
            "//*[contains(text(), 'restore messages')]",
            "//div[@aria-label='Continue']",
            "//div[@aria-label='Close']",
            "//div[@aria-label='close']",
            "//*[text()='Not Now']",
            "//*[text()='Close']",
            "//div[contains(@class, 'x1b0d499')]" # Close icon class
        ]
        
        for xpath in xpaths:
            try:
                btns = driver.find_elements(By.XPATH, xpath)
                for btn in btns:
                    if btn.is_displayed():
                        driver.execute_script("arguments[0].click();", btn)
                        add_log(f"Popup Closed: {xpath}")
                        time.sleep(1)
            except: pass
            
    except Exception:
        pass

# --- MESSAGE SENDER ---
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
            time.sleep(0.5)
            actions.send_keys(Keys.RETURN)
            actions.perform()
            return True
        except: return False
    return False

# --- MAIN BOT LOOP ---
def run_bot(cookie_str, url, msg, delay):
    add_log("Bot Starting...")
    driver = get_driver()
    if not driver: 
        add_log("Failed to start Driver (Memory Issue?)")
        return

    try:
        driver.get("https://www.facebook.com/")
        cookies = parse_cookies(cookie_str)
        for c in cookies:
            try: driver.add_cookie(c)
            except: pass
        
        add_log("Cookies set. Loading Chat...")
        driver.get(url)
        time.sleep(10) # Wait for load

        # Initial Bypass
        bypass_popups(driver)
        time.sleep(2)

        add_log("Starting Message Loop...")
        while True:
            # 1. Check for popups before sending
            bypass_popups(driver)
            
            # 2. Try to send
            success = send_message_safely(driver, msg)
            
            if success:
                add_log(f"Sent: {msg}")
                time.sleep(int(delay))
            else:
                add_log("Send Failed. Retrying (Maybe PIN blocked?)...")
                bypass_popups(driver) # Aggressive popup check
                time.sleep(5)
            
    except Exception as e:
        add_log(f"Error: {str(e)}")
    finally:
        if driver:
            driver.quit()
        add_log("Bot Stopped.")

# --- FLASK ROUTES ---
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
        <head>
            <title>FB Bot (Render Optimized)</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: sans-serif; padding: 20px; background: #f0f2f5; }
                form { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
                input, textarea { width: 100%; padding: 10px; margin: 5px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
                button { background-color: #1877f2; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%; font-size: 16px; }
                button:hover { background-color: #166fe5; }
                h2 { text-align: center; color: #1877f2; }
            </style>
        </head>
        <body>
            <h2>🚀 FB Sender (Anti-Crash Mode)</h2>
            <form method="POST">
                <label><b>Cookie:</b></label>
                <textarea name="cookie" rows="5" required placeholder="Paste cookies here..."></textarea>
                
                <label><b>Chat URL:</b></label>
                <input type="text" name="url" required placeholder="https://www.facebook.com/messages/t/..." />
                
                <label><b>Message:</b></label>
                <input type="text" name="msg" required placeholder="Hello!" />
                
                <label><b>Delay (Seconds):</b></label>
                <input type="number" name="delay" value="10" required />
                
                <button type="submit">Start Bot</button>
            </form>
            <br>
            <div style="text-align: center;">
                <a href="/logs"><button style="background: #42b72a; width: 200px;">View Logs</button></a>
            </div>
        </body>
    </html>
    '''

@app.route('/logs')
def show_logs():
    return f'''
    <html>
        <head>
            <meta http-equiv="refresh" content="3">
            <title>Live Logs</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: monospace; padding: 20px; background: #222; color: #0f0; }
                .log-box { background: #000; padding: 15px; border: 1px solid #444; border-radius: 5px; height: 80vh; overflow-y: scroll; }
                a { color: white; text-decoration: none; border: 1px solid white; padding: 5px 10px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h2>📜 Live Server Logs</h2>
            <a href="/">Back to Home</a>
            <br><br>
            <div class="log-box">
                {"<br>".join(logs)}
            </div>
        </body>
    </html>
    '''

if __name__ == '__main__':
    # Render PORT variable use karega
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
