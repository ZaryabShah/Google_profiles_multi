import os
import subprocess
import time
import tempfile
import zipfile
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------------------
# CONFIG — EDIT THESE VALUES
# ---------------------------

# 1) Point to your real Chrome user data directory and profile name
USER_DATA_DIR = r"C:\Users\Zaryab Jibu\AppData\Local\Google\Chrome\User Data"
PROFILE_DIR   = "Default"  # Try "Profile 1" or "Profile 2" if Default doesn't work

# 2) Proxy settings
USE_PROXY = True
PROXY_HOST = "pg.proxi.es"
PROXY_PORT = 20000
PROXY_USER = "XluiTMlGLoq9guFN-s-cf2xwVX8LA"
PROXY_PASS = "a3Dj3ecQ9Ta84Zk7"

# 3) Target page
START_URL = "https://unitsstorage.com/"

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------

def kill_chrome_processes():
    """Kill all Chrome processes to ensure clean start."""
    try:
        print("🔄 Killing existing Chrome processes...")
        
        # Force kill all Chrome processes
        subprocess.run("taskkill /f /im chrome.exe", shell=True, capture_output=True)
        subprocess.run("taskkill /f /im chromedriver.exe", shell=True, capture_output=True)
        
        print("✅ Chrome processes killed")
        time.sleep(3)  # Wait for processes to terminate
        
    except Exception as e:
        print(f"⚠️  Could not kill all Chrome processes: {e}")

def verify_profile_directory():
    """Verify that the profile directory exists."""
    user_data_path = Path(USER_DATA_DIR)
    profile_path = user_data_path / PROFILE_DIR
    
    if not user_data_path.exists():
        print(f"❌ User data directory does not exist: {USER_DATA_DIR}")
        return False
    
    if not profile_path.exists():
        print(f"❌ Profile directory does not exist: {profile_path}")
        print("📋 Available profiles:")
        try:
            for item in user_data_path.iterdir():
                if item.is_dir() and (item.name.startswith("Profile") or item.name == "Default"):
                    print(f"   - {item.name}")
        except Exception as e:
            print(f"Could not list profiles: {e}")
        return False
    
    print(f"✅ Profile directory verified: {profile_path}")
    return True

def build_proxy_auth_extension(host, port, username, password):
    """Create a Chrome extension for proxy authentication."""
    manifest = {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth",
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

def launch_chrome_with_undetected():
    """Launch Chrome using undetected-chromedriver with real profile."""
    
    # Verify profile exists
    if not verify_profile_directory():
        print("❌ Profile verification failed. Please check your profile settings.")
        return None
    
    # Kill existing Chrome processes
    kill_chrome_processes()
    
    print(f"🚀 Launching Chrome with undetected-chromedriver...")
    print(f"📁 Profile: {PROFILE_DIR}")
    print(f"🌐 Target URL: {START_URL}")
    
    try:
        # Configure Chrome options
        options = uc.ChromeOptions()
        
        # Use real Chrome profile
        options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        options.add_argument(f"--profile-directory={PROFILE_DIR}")
        
        # Essential arguments
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-popup-blocking")
        
        # Add proxy extension if needed
        if USE_PROXY and PROXY_HOST and PROXY_PORT:
            proxy_ext_zip = build_proxy_auth_extension(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
            options.add_extension(proxy_ext_zip)
            print(f"🔐 Proxy extension added: {PROXY_HOST}:{PROXY_PORT}")
        
        # Create the webdriver
        driver = uc.Chrome(
            options=options,
            user_data_dir=USER_DATA_DIR,  # This helps with profile handling
            version_main=None,  # Auto-detect Chrome version
        )
        
        # Wait for Chrome to initialize
        print("⏳ Waiting for Chrome to initialize...")
        time.sleep(8)  # Longer wait for real profiles
        
        # Test connection
        try:
            current_url = driver.current_url
            print(f"✅ Chrome connected successfully!")
            print(f"📍 Initial URL: {current_url}")
        except Exception as conn_error:
            print(f"⚠️  Connection test warning: {conn_error}")
        
        # Navigate to target URL with retries
        print(f"🌐 Navigating to: {START_URL}")
        
        navigation_success = False
        for attempt in range(3):
            try:
                driver.get(START_URL)
                
                # Wait for page to load
                print(f"⏳ Waiting for page to load (attempt {attempt + 1})...")
                time.sleep(10)
                
                # Check if navigation was successful
                final_url = driver.current_url
                page_title = driver.title
                
                print(f"📍 Current URL: {final_url}")
                print(f"📄 Page Title: {page_title}")
                
                # Verify we're on the right page
                if "unitsstorage" in final_url.lower() or "unitsstorage" in page_title.lower():
                    print("🎉 SUCCESS! Successfully navigated to Units Storage!")
                    navigation_success = True
                    break
                elif final_url != "data:," and "about:blank" not in final_url:
                    print(f"⚠️  Navigation successful but unexpected page. URL: {final_url}")
                    navigation_success = True
                    break
                else:
                    print(f"❌ Navigation attempt {attempt + 1} failed. Retrying...")
                    if attempt < 2:
                        time.sleep(5)
                
            except Exception as nav_error:
                print(f"❌ Navigation attempt {attempt + 1} error: {nav_error}")
                if attempt < 2:
                    time.sleep(5)
        
        if not navigation_success:
            print("⚠️  Navigation not fully successful, but Chrome is running.")
            print("💡 You can manually navigate to the desired URL.")
        
        return driver
        
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure Chrome is completely closed")
        print("   2. Try using a different profile (Profile 1, Profile 2)")
        print("   3. Check if the user data directory path is correct")
        print("   4. Run as administrator if needed")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CHROME LAUNCHER WITH UNDETECTED-CHROMEDRIVER")
    print("=" * 60)
    print(f"Target URL: {START_URL}")
    print(f"Profile: {PROFILE_DIR}")
    print(f"Proxy: {PROXY_HOST}:{PROXY_PORT} (enabled: {USE_PROXY})")
    print("=" * 60)
    
    try:
        driver = launch_chrome_with_undetected()
        
        if driver:
            print("\n" + "=" * 60)
            print("✅ CHROME LAUNCHED SUCCESSFULLY!")
            print("=" * 60)
            
            try:
                final_url = driver.current_url
                page_title = driver.title
                
                print(f"📍 Final URL: {final_url}")
                print(f"📄 Page Title: {page_title}")
                print(f"📁 Profile Used: {PROFILE_DIR}")
                print(f"🔐 Proxy Status: {'Enabled' if USE_PROXY else 'Disabled'}")
                
                # Keep the browser session alive
                print(f"\n⏳ Keeping Chrome stable...")
                time.sleep(10)
                
                print(f"\n🎉 ALL DONE! Chrome is ready to use.")
                print(f"💡 Chrome will stay open. You can now use it normally.")
                print(f"🔒 Your profile data and cookies are preserved.")
                
                # Keep the script running briefly to ensure the browser stays open
                print(f"\n⏳ Script will end in 15 seconds, Chrome will remain open...")
                time.sleep(15)
                
            except Exception as status_error:
                print(f"⚠️  Status check failed: {status_error}")
                print(f"🌐 Chrome should still be running and usable.")
        else:
            print("\n❌ FAILED TO LAUNCH CHROME")
            print("🔧 Please check the troubleshooting tips above.")
            
    except Exception as main_error:
        print(f"\n💥 CRITICAL ERROR: {main_error}")
    
    print(f"\n🏁 Script completed. Chrome should be running!")
