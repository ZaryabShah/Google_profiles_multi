import os
import zipfile
import tempfile
import subprocess
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ---------------------------
# CONFIG — EDIT THESE VALUES
# ---------------------------

USER_DATA_DIR = r"C:\Users\Zaryab Jibu\AppData\Local\Google\Chrome\User Data"
PROFILE_DIR   = "Default"

# Proxy settings
USE_PROXY = True
PROXY_HOST = "pg.proxi.es"
PROXY_PORT = 20000
PROXY_USER = "XluiTMlGLoq9guFN-s-cf2xwVX8LA"
PROXY_PASS = "a3Dj3ecQ9Ta84Zk7"

START_URL = "https://unitsstorage.com/"

def build_proxy_auth_extension(host, port, username, password):
    """Creates a temporary Chrome extension for proxy authentication."""
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
    manifest_path.write_text(__import__("json").dumps(manifest), encoding="utf-8")
    background_path.write_text(background_js, encoding="utf-8")

    zip_path = Path(temp_dir, "proxy_auth_extension.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_path, "manifest.json")
        zf.write(background_path, "background.js")
    return str(zip_path)

def kill_chrome():
    """Kill all Chrome processes."""
    try:
        subprocess.run("taskkill /f /im chrome.exe", shell=True, capture_output=True)
        subprocess.run("taskkill /f /im chromedriver.exe", shell=True, capture_output=True)
        time.sleep(3)
        print("Killed Chrome processes")
    except Exception as e:
        print(f"Error killing Chrome: {e}")

def launch_chrome_real_profile():
    """Launch Chrome with the real user profile."""
    
    # First, kill any existing Chrome processes
    kill_chrome()
    
    options = Options()
    
    # Use your real Chrome profile
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument(f"--profile-directory={PROFILE_DIR}")
    
    # Essential arguments for Selenium compatibility
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    
    # Optional proxy extension
    if USE_PROXY and PROXY_HOST and PROXY_PORT:
        proxy_ext_zip = build_proxy_auth_extension(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        options.add_extension(proxy_ext_zip)
    
    # Keep Chrome open after script ends
    options.add_experimental_option("detach", True)
    
    try:
        print(f"Launching Chrome with real profile: {PROFILE_DIR}")
        driver = webdriver.Chrome(options=options)
        
        print("Chrome launched! Waiting for initialization...")
        time.sleep(3)
        
        print(f"Navigating to: {START_URL}")
        driver.get(START_URL)
        
        time.sleep(3)
        print(f"Success! Current URL: {driver.current_url}")
        
        return driver
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    driver = launch_chrome_real_profile()
    if driver:
        print("Chrome is running with your real profile!")
        print("You can now interact with the browser manually.")
    else:
        print("Failed to launch Chrome with real profile.")
