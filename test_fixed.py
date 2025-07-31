import os
import zipfile
import tempfile
import subprocess
import time
import json
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------------------
# CONFIG — EDIT THESE VALUES
# ---------------------------

# 1) Point to your real Chrome user data directory and profile name
USER_DATA_DIR = r"C:\Users\Zaryab Jibu\AppData\Local\Google\Chrome\User Data"
PROFILE_DIR   = "Profile 1"  # Try "Profile 1" or "Profile 2" if Default doesn't work

# 2) Optional: add extensions at launch (unpacked folders or .crx files)
EXTRA_EXTENSIONS = []

# 3) Optional proxy with auth (builds a tiny extension at runtime)
USE_PROXY = True
PROXY_HOST = "pg.proxi.es"
PROXY_PORT = 20000
PROXY_USER = "XluiTMlGLoq9guFN-s-cf2xwVX8LA"
PROXY_PASS = "a3Dj3ecQ9Ta84Zk7"

# 4) Target page (you can change later)
START_URL = "https://unitsstorage.com/"

def build_proxy_auth_extension(host, port, username, password):
    """Creates a Chrome extension for proxy authentication."""
    manifest = {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Selenium Proxy Auth",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "22.0.0"
    }

    background_js = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{host}",
            port: {port}
        }},
        bypassList: ["localhost"]
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{username}",
            password: "{password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ["blocking"]
);
"""

    temp_dir = tempfile.mkdtemp()
    manifest_path = Path(temp_dir, "manifest.json")
    background_path = Path(temp_dir, "background.js")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    background_path.write_text(background_js, encoding="utf-8")

    zip_path = Path(temp_dir, "proxy_auth_extension.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_path, "manifest.json")
        zf.write(background_path, "background.js")
    return str(zip_path)

def kill_chrome_processes():
    """Kill all Chrome processes."""
    try:
        print("Killing existing Chrome processes...")
        subprocess.run("taskkill /f /im chrome.exe", shell=True, capture_output=True)
        subprocess.run("taskkill /f /im chromedriver.exe", shell=True, capture_output=True)
        time.sleep(3)
        print("Chrome processes killed")
    except Exception as e:
        print(f"Could not kill Chrome processes: {e}")

def launch_chrome_manually():
    """Launch Chrome manually with the real profile and return the debugging port."""
    kill_chrome_processes()
    
    # Build the Chrome command
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not Path(chrome_exe).exists():
        chrome_exe = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    
    if not Path(chrome_exe).exists():
        raise Exception("Chrome executable not found")
    
    debugging_port = 9225
    
    # Build Chrome command with all necessary arguments
    chrome_args = [
        chrome_exe,
        f"--user-data-dir={USER_DATA_DIR}",
        f"--profile-directory={PROFILE_DIR}",
        f"--remote-debugging-port={debugging_port}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",
        "--start-maximized",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--disable-extensions-file-access-check",
        "--disable-extensions-http-throttling"
    ]
    
    # Add proxy extension if needed
    if USE_PROXY and PROXY_HOST and PROXY_PORT:
        proxy_ext_zip = build_proxy_auth_extension(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        chrome_args.append(f"--load-extension={Path(proxy_ext_zip).parent}")
    
    print(f"Launching Chrome manually with profile: {PROFILE_DIR}")
    print("Chrome command:", ' '.join(chrome_args))
    
    # Start Chrome process
    process = subprocess.Popen(chrome_args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    
    # Wait for Chrome to start and remote debugging to be available
    print("Waiting for Chrome to initialize...")
    time.sleep(8)
    
    # Check if remote debugging is available
    for i in range(10):
        try:
            response = requests.get(f"http://localhost:{debugging_port}/json/version", timeout=2)
            if response.status_code == 200:
                print("Chrome remote debugging is ready!")
                return debugging_port, process
        except:
            pass
        time.sleep(1)
    
    raise Exception("Chrome remote debugging not available")

def connect_to_chrome(debugging_port):
    """Connect Selenium to the already running Chrome instance."""
    options = Options()
    options.add_experimental_option("debuggerAddress", f"localhost:{debugging_port}")
    
    # Don't add user-data-dir or profile-directory when connecting to existing instance
    # These should only be used when launching Chrome
    
    try:
        print("Connecting Selenium to existing Chrome instance...")
        driver = webdriver.Chrome(options=options)
        print("Successfully connected to Chrome!")
        return driver
    except Exception as e:
        print(f"Failed to connect to Chrome: {e}")
        raise

def navigate_to_url(driver, url):
    """Navigate to the target URL."""
    try:
        print(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(3)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        current_url = driver.current_url
        print(f"Successfully navigated! Current URL: {current_url}")
        return True
    except Exception as e:
        print(f"Navigation failed: {e}")
        return False

def main():
    try:
        # Step 1: Launch Chrome manually with real profile
        debugging_port, chrome_process = launch_chrome_manually()
        
        # Step 2: Connect Selenium to the existing Chrome instance
        driver = connect_to_chrome(debugging_port)
        
        # Step 3: Navigate to target URL
        if navigate_to_url(driver, START_URL):
            print("\n✅ SUCCESS! Chrome is running with your real profile and navigated to the target URL.")
            print(f"Profile: {PROFILE_DIR}")
            print(f"URL: {driver.current_url}")
            print(f"Title: {driver.title}")
        else:
            print("❌ Navigation failed")
        
        # Keep the browser open
        print("\nChrome will remain open for manual use.")
        print("The script has completed successfully!")
        
        return driver
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    driver = main()
