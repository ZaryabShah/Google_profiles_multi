import os
import subprocess
import time
import tempfile
import zipfile
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Configuration
USER_DATA_DIR = r"C:\Users\Zaryab Jibu\AppData\Local\Google\Chrome\User Data"
PROFILE_DIR = "Profile 1"  # Using Profile 1 since Default might have issues
START_URL = "https://unitsstorage.com/"

# Proxy settings
USE_PROXY = True
PROXY_HOST = "pg.proxi.es"
PROXY_PORT = 20000
PROXY_USER = "XluiTMlGLoq9guFN-s-cf2xwVX8LA"
PROXY_PASS = "a3Dj3ecQ9Ta84Zk7"

def build_proxy_extension():
    """Build proxy extension."""
    if not USE_PROXY:
        return None
        
    manifest = {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth",
        "permissions": ["proxy", "tabs", "storage", "<all_urls>", "webRequest", "webRequestBlocking"],
        "background": {"scripts": ["background.js"]}
    }

    background_js = f"""
chrome.proxy.settings.set({{
    value: {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{PROXY_HOST}",
                port: {PROXY_PORT}
            }}
        }}
    }},
    scope: "regular"
}});

chrome.webRequest.onAuthRequired.addListener(
    function(details) {{
        return {{
            authCredentials: {{
                username: "{PROXY_USER}",
                password: "{PROXY_PASS}"
            }}
        }};
    }},
    {{urls: ["<all_urls>"]}},
    ["blocking"]
);
"""

    temp_dir = tempfile.mkdtemp()
    with open(Path(temp_dir) / "manifest.json", "w") as f:
        json.dump(manifest, f)
    with open(Path(temp_dir) / "background.js", "w") as f:
        f.write(background_js)
    
    return temp_dir

def main():
    print("Starting Chrome with real profile...")
    
    # Kill existing Chrome processes
    try:
        subprocess.run("taskkill /f /im chrome.exe", shell=True, capture_output=True, text=True)
        subprocess.run("taskkill /f /im chromedriver.exe", shell=True, capture_output=True, text=True)
        print("Killed existing Chrome processes")
        time.sleep(2)
    except:
        pass
    
    # Setup Chrome options
    options = Options()
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument(f"--profile-directory={PROFILE_DIR}")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--start-maximized")
    
    # Add proxy extension
    proxy_dir = build_proxy_extension()
    if proxy_dir:
        options.add_argument(f"--load-extension={proxy_dir}")
        print("Added proxy extension")
    
    # Advanced options to avoid conflicts
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("detach", True)
    
    try:
        print(f"Launching Chrome with profile: {PROFILE_DIR}")
        driver = webdriver.Chrome(options=options)
        print("Chrome launched successfully!")
        
        # Small delay to let Chrome settle
        time.sleep(3)
        
        # Navigate to URL
        print(f"Navigating to: {START_URL}")
        driver.get(START_URL)
        
        # Wait for page load
        time.sleep(5)
        
        print(f"✅ SUCCESS!")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Test if proxy is working by checking IP
        try:
            driver.get("https://httpbin.org/ip")
            time.sleep(3)
            page_source = driver.page_source
            if "pg.proxi.es" in page_source or PROXY_HOST in page_source:
                print("✅ Proxy is working!")
            else:
                print("ℹ️  Proxy status unclear")
        except:
            print("Could not test proxy")
        
        # Go back to target URL
        driver.get(START_URL)
        time.sleep(2)
        
        print("\n🎉 Chrome is now running with your real profile and proxy!")
        print("You can interact with it normally. The browser will stay open.")
        
        return driver
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTrying alternative approach...")
        
        # Alternative: try without some problematic options
        options = Options()
        options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        options.add_argument(f"--profile-directory={PROFILE_DIR}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_experimental_option("detach", True)
        
        if proxy_dir:
            options.add_argument(f"--load-extension={proxy_dir}")
        
        try:
            print("Trying simplified approach...")
            driver = webdriver.Chrome(options=options)
            time.sleep(3)
            driver.get(START_URL)
            time.sleep(3)
            print(f"✅ SUCCESS with alternative approach!")
            print(f"Current URL: {driver.current_url}")
            return driver
        except Exception as e2:
            print(f"❌ Alternative approach also failed: {e2}")
            return None

if __name__ == "__main__":
    driver = main()
    if driver:
        print("\nScript completed. Chrome should be running with your profile.")
    else:
        print("\nScript failed. Please check the error messages above.")
