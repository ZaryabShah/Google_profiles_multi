import os
import subprocess
import time
from pathlib import Path
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
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
        
        # Kill processes on debugging ports
        for port in [9222, 9223, 9224, 9225]:
            try:
                result = subprocess.run(f'netstat -aon | findstr :{port}', shell=True, capture_output=True, text=True)
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            subprocess.run(f"taskkill /f /pid {pid}", shell=True, capture_output=True)
            except:
                pass
        
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

def launch_chrome_with_seleniumwire():
    """Launch Chrome using Selenium Wire with real profile."""
    
    # Verify profile exists
    if not verify_profile_directory():
        print("❌ Profile verification failed. Please check your profile settings.")
        return None
    
    # Kill existing Chrome processes
    kill_chrome_processes()
    
    # Configure Selenium Wire proxy options
    seleniumwire_options = {}
    
    if USE_PROXY and PROXY_HOST and PROXY_PORT:
        seleniumwire_options = {
            'proxy': {
                'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
                'https': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
                'no_proxy': 'localhost,127.0.0.1'  # bypass proxy for local addresses
            }
        }
        print(f"🔐 Proxy configured: {PROXY_HOST}:{PROXY_PORT}")
    
    # Configure Chrome options
    chrome_options = Options()
    
    # Use real Chrome profile
    chrome_options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    chrome_options.add_argument(f"--profile-directory={PROFILE_DIR}")
    
    # Essential Chrome arguments
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--remote-debugging-port=9224")
    
    # Remove automation indicators
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Keep Chrome open after script ends
    chrome_options.add_experimental_option("detach", True)
    
    # Add user agent to make it look more natural
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    print(f"🚀 Launching Chrome with Selenium Wire...")
    print(f"📁 Profile: {PROFILE_DIR}")
    print(f"🌐 Target URL: {START_URL}")
    
    try:
        # Create the webdriver with Selenium Wire
        driver = webdriver.Chrome(
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )
        
        # Wait for Chrome to initialize
        print("⏳ Waiting for Chrome to initialize...")
        time.sleep(5)
        
        # Test connection
        try:
            current_url = driver.current_url
            print(f"✅ Chrome connected successfully!")
            print(f"📍 Current URL: {current_url}")
        except Exception as conn_error:
            print(f"⚠️  Connection test warning: {conn_error}")
        
        # Navigate to target URL
        print(f"🌐 Navigating to: {START_URL}")
        driver.get(START_URL)
        
        # Wait for page to load
        print("⏳ Waiting for page to load...")
        time.sleep(8)
        
        try:
            # Wait for page to be ready
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            final_url = driver.current_url
            page_title = driver.title
            
            print(f"🎉 SUCCESS!")
            print(f"📍 Final URL: {final_url}")
            print(f"📄 Page Title: {page_title}")
            
            # Check if we're on the right page
            if "unitsstorage" in final_url.lower():
                print("✅ Successfully navigated to Units Storage!")
            else:
                print(f"⚠️  URL doesn't match expected site. Check if proxy is working correctly.")
            
            return driver
            
        except Exception as page_error:
            print(f"⚠️  Page loading issue: {page_error}")
            print("🌐 Chrome is still running, you can navigate manually.")
            return driver
        
    except Exception as e:
        print(f"❌ Failed to launch Chrome with Selenium Wire: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Install selenium-wire: pip install selenium-wire")
        print("   2. Make sure Chrome is closed completely")
        print("   3. Try a different profile (Profile 1, Profile 2)")
        print("   4. Check if proxy credentials are correct")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CHROME LAUNCHER WITH SELENIUM WIRE")
    print("=" * 60)
    print(f"Target URL: {START_URL}")
    print(f"Profile: {PROFILE_DIR}")
    print(f"Proxy: {PROXY_HOST}:{PROXY_PORT} (enabled: {USE_PROXY})")
    print("=" * 60)
    
    try:
        driver = launch_chrome_with_seleniumwire()
        
        if driver:
            print("\n" + "=" * 60)
            print("✅ CHROME LAUNCHED SUCCESSFULLY!")
            print("=" * 60)
            
            try:
                final_url = driver.current_url
                print(f"📍 Current URL: {final_url}")
                print(f"📁 Profile Used: {PROFILE_DIR}")
                print(f"🔐 Proxy Status: {'Enabled' if USE_PROXY else 'Disabled'}")
                
                # Keep script running briefly to ensure stability
                print(f"\n⏳ Ensuring Chrome stability...")
                time.sleep(5)
                
                print(f"\n🎉 ALL DONE! Chrome is ready to use.")
                print(f"💡 The browser will stay open after this script ends.")
                
            except Exception as status_error:
                print(f"⚠️  Status check failed: {status_error}")
                print(f"🌐 Chrome should still be running and usable.")
        else:
            print("\n❌ FAILED TO LAUNCH CHROME")
            print("🔧 Please check the troubleshooting tips above.")
            
    except Exception as main_error:
        print(f"\n💥 CRITICAL ERROR: {main_error}")
    
    print(f"\n🏁 Script completed.")
