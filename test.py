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

# 1) Point to your real Chrome user data directory and profile name
#    Example Windows: r"C:\Users\me\AppData\Local\Google\Chrome\User Data"
#    Example macOS:   "/Users/me/Library/Application Support/Google/Chrome"
USER_DATA_DIR = r"C:\Users\Zaryab Jibu\AppData\Local\Google\Chrome\User Data"   # <-- Updated to correct path
PROFILE_DIR   = "Default"                                             # e.g. 'Default' or 'Profile 1'

# 2) Optional: add extensions at launch (unpacked folders or .crx files)
#    If you already have them installed in the profile, you can leave this empty.
EXTRA_EXTENSIONS = [
    # r"C:\path\to\2captcha_extension_unpacked",   # unpacked folder
    # r"C:\path\to\some_extension.crx",            # CRX file
]

# 3) Optional proxy with auth (builds a tiny extension at runtime)
USE_PROXY = True
PROXY_HOST = "pg.proxi.es"     # from your message
PROXY_PORT = 20000             # from your message
PROXY_USER = "XluiTMlGLoq9guFN-s-cf2xwVX8LA"  # from your message
PROXY_PASS = "a3Dj3ecQ9Ta84Zk7"               # from your message

# 4) Target page (you can change later)
START_URL = "https://unitsstorage.com/"

# ---------------------------
# HELPER: build proxy extension (.zip)
# ---------------------------

def build_proxy_auth_extension(host, port, username, password):
    """
    Creates a temporary Chrome extension that:
      - sets fixed proxy (http/https) to host:port
      - handles proxy authentication with provided creds
    Returns path to zip file.
    """
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

# ---------------------------
# MAIN: launch real Chrome with your profile and extensions
# ---------------------------

def kill_chrome_processes():
    """Kill all Chrome processes to ensure clean start."""
    try:
        print("Killing existing Chrome processes...")
        
        # First, try graceful shutdown
        subprocess.run('wmic process where "name=\'chrome.exe\'" delete', shell=True, capture_output=True)
        time.sleep(2)
        
        # Then force kill any remaining processes
        result1 = subprocess.run("taskkill /f /im chrome.exe", shell=True, capture_output=True)
        result2 = subprocess.run("taskkill /f /im chromedriver.exe", shell=True, capture_output=True)
        
        # Kill processes using debugging ports
        for port in [9222, 9223, 9224, 9225, 9226]:
            try:
                result = subprocess.run(f'netstat -aon | findstr :{port}', shell=True, capture_output=True, text=True)
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            subprocess.run(f"taskkill /f /pid {pid}", shell=True, capture_output=True)
            except:
                pass
        
        print("Chrome processes killed")
    except Exception as e:
        print(f"Could not kill Chrome processes: {e}")
    
    # Wait longer for processes to fully terminate
    time.sleep(5)

def verify_profile_directory():
    """Verify that the profile directory exists and is accessible."""
    user_data_path = Path(USER_DATA_DIR)
    profile_path = user_data_path / PROFILE_DIR
    
    if not user_data_path.exists():
        print(f"Warning: User data directory does not exist: {USER_DATA_DIR}")
        return False
    
    if not profile_path.exists():
        print(f"Warning: Profile directory does not exist: {profile_path}")
        print("Available profiles:")
        try:
            for item in user_data_path.iterdir():
                if item.is_dir() and (item.name.startswith("Profile") or item.name == "Default"):
                    print(f"  - {item.name}")
        except Exception as e:
            print(f"Could not list profiles: {e}")
        return False
    
    return True

def check_chrome_profile_lock():
    """Check if Chrome profile is locked by another instance."""
    lockfile_path = Path(USER_DATA_DIR) / PROFILE_DIR / "SingletonLock"
    if lockfile_path.exists():
        print(f"Warning: Profile {PROFILE_DIR} appears to be in use (lockfile exists)")
        return True
    return False

def find_free_port():
    """Find a free port for Chrome remote debugging."""
    import socket
    for port in range(9222, 9230):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return 9222  # fallback

def wait_for_debug_port(port, timeout=30):
    """Wait for Chrome remote debugging port to become available."""
    import socket
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    print(f"✅ Chrome debugging port {port} is now available")
                    return True
        except:
            pass
        time.sleep(1)
    
    print(f"❌ Chrome debugging port {port} not available after {timeout} seconds")
    return False

def launch_chrome_with_profile():
    # First, verify the profile directory exists
    if not verify_profile_directory():
        print("Profile directory verification failed. Trying with temporary profile...")
        return launch_chrome_with_temp_profile()
    
    # Kill existing Chrome processes thoroughly
    kill_chrome_processes()
    
    # Find a free debugging port
    debug_port = find_free_port()
    print(f"Using debugging port: {debug_port}")
    
    options = Options()

    # Real profile (keeps cookies, sessions, installed extensions)
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument(f"--profile-directory={PROFILE_DIR}")
    
    # Use the free debugging port
    options.add_argument(f"--remote-debugging-port={debug_port}")asd
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    # Add arguments to help with navigation
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-extensions-file-access-check")
    options.add_argument("--disable-extensions-http-throttling")
    options.add_argument("--disable-dev-shm-usage")

    # Make it feel more like a regular session
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Load extra extensions
    unpacked = [p for p in EXTRA_EXTENSIONS if Path(p).is_dir()]
    crxes    = [p for p in EXTRA_EXTENSIONS if Path(p).is_file() and p.lower().endswith(".crx")]

    if unpacked:
        options.add_argument("--load-extension=" + ",".join(unpacked))

    for crx in crxes:
        options.add_extension(crx)

    # Add proxy extension if needed
    if USE_PROXY and PROXY_HOST and PROXY_PORT:
        proxy_ext_zip = build_proxy_auth_extension(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        options.add_extension(proxy_ext_zip)

    # Keep Chrome open when script finishes
    options.add_experimental_option("detach", True)

    # Try to start Chrome with multiple attempts
    driver = None
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            print(f"Launching Chrome with profile: {PROFILE_DIR} (attempt {attempt + 1}/{max_retries})")
            driver = webdriver.Chrome(options=options)
            
            # Wait longer for Chrome to fully initialize with real profile
            print("Waiting for Chrome to fully initialize...")
            time.sleep(8)  # Increased wait time for real profiles
            
            # Test connection multiple times
            connection_attempts = 3
            current_url = None
            for conn_attempt in range(connection_attempts):
                try:
                    current_url = driver.current_url
                    print(f"✅ Driver connected successfully. Current URL: {current_url}")
                    break
                except Exception as conn_error:
                    print(f"Connection attempt {conn_attempt + 1} failed: {conn_error}")
                    if conn_attempt < connection_attempts - 1:
                        time.sleep(3)
                    else:
                        raise conn_error
            
            # Force navigation to target URL with retries
            print(f"Navigating to: {START_URL}")
            navigation_success = False
            nav_attempts = 3
            
            for nav_attempt in range(nav_attempts):
                try:
                    # Close any existing tabs except the first one
                    if len(driver.window_handles) > 1:
                        for handle in driver.window_handles[1:]:
                            driver.switch_to.window(handle)
                            driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    
                    # Navigate to the target URL
                    driver.get(START_URL)
                    time.sleep(5)  # Wait for page to load
                    
                    # Verify navigation was successful
                    final_url = driver.current_url
                    if START_URL.replace("https://", "").replace("http://", "") in final_url.replace("https://", "").replace("http://", ""):
                        print(f"🎉 SUCCESS! Chrome with real profile navigated to: {final_url}")
                        navigation_success = True
                        break
                    else:
                        print(f"Navigation attempt {nav_attempt + 1}: URL mismatch. Expected: {START_URL}, Got: {final_url}")
                        if nav_attempt < nav_attempts - 1:
                            time.sleep(3)
                        
                except Exception as nav_error:
                    print(f"Navigation attempt {nav_attempt + 1} failed: {nav_error}")
                    if nav_attempt < nav_attempts - 1:
                        time.sleep(3)
                    else:
                        # Even if navigation fails, return the driver if it's connected
                        print("⚠️ Navigation failed but driver is connected. You can navigate manually.")
                        return driver
            
            if navigation_success:
                print("✅ Real profile launch and navigation completed successfully!")
                return driver
            else:
                print("⚠️ Real profile launched but navigation was not fully successful.")
                return driver
                
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
            
            if attempt < max_retries - 1:
                print("Retrying with different approach...")
                time.sleep(5)
                # Kill processes again before retry
                kill_chrome_processes()
    
    print("All attempts with real profile failed. Trying temporary profile...")
    return launch_chrome_with_temp_profile()

def launch_chrome_with_temp_profile():
    """Fallback method using a temporary profile."""
    print("🔄 Launching Chrome with temporary profile as fallback...")
    
    options = Options()
    
    # Create a temporary user data directory
    temp_user_data = tempfile.mkdtemp(prefix="chrome_temp_")
    options.add_argument(f"--user-data-dir={temp_user_data}")
    
    # Add basic arguments
    options.add_argument("--remote-debugging-port=9223")  # Different port
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")

    # Make it feel more like a regular session
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Add proxy extension if needed
    if USE_PROXY and PROXY_HOST and PROXY_PORT:
        proxy_ext_zip = build_proxy_auth_extension(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        options.add_extension(proxy_ext_zip)
        print(f"✅ Proxy extension added: {PROXY_HOST}:{PROXY_PORT}")

    # Keep Chrome open when script finishes
    options.add_experimental_option("detach", True)

    try:
        print(f"📁 Temporary profile location: {temp_user_data}")
        driver = webdriver.Chrome(options=options)
        
        # Wait for Chrome to initialize
        print("⏳ Waiting for Chrome to initialize...")
        time.sleep(5)
        
        # Navigate to target URL with retries
        print(f"🌐 Navigating to: {START_URL}")
        navigation_success = False
        
        for attempt in range(3):
            try:
                driver.get(START_URL)
                time.sleep(5)
                
                final_url = driver.current_url
                if START_URL.replace("https://", "").replace("http://", "") in final_url.replace("https://", "").replace("http://", ""):
                    print(f"✅ Successfully navigated to: {final_url}")
                    navigation_success = True
                    break
                else:
                    print(f"⚠️  Navigation attempt {attempt + 1}: URL mismatch")
                    if attempt < 2:
                        time.sleep(3)
                        
            except Exception as nav_error:
                print(f"❌ Navigation attempt {attempt + 1} failed: {nav_error}")
                if attempt < 2:
                    time.sleep(3)
        
        if not navigation_success:
            print("⚠️  Navigation not fully successful, but Chrome is running")
            
        return driver
        
    except Exception as e:
        print(f"❌ Error starting Chrome with temporary profile: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Make sure Chrome is installed and updated")
        print("   2. Try running as administrator")
        print("   3. Check if antivirus is blocking Chrome")
        print("   4. Close all other Chrome instances manually")
        raise

if __name__ == "__main__":
    print("🚀 Starting Chrome with your profile and proxy...")
    print(f"Target URL: {START_URL}")
    print(f"Profile: {PROFILE_DIR}")
    print(f"Proxy: {PROXY_HOST}:{PROXY_PORT} (enabled: {USE_PROXY})")
    print("-" * 60)
    
    try:
        driver = launch_chrome_with_profile()
        
        if driver:
            try:
                final_url = driver.current_url
                print(f"\n✅ FINAL RESULT:")
                print(f"   Chrome launched successfully!")
                print(f"   Current URL: {final_url}")
                print(f"   Profile used: {PROFILE_DIR}")
                print(f"   Proxy enabled: {USE_PROXY}")
                
                # Keep the script running briefly to ensure everything is stable
                print(f"\n⏳ Waiting 10 seconds to ensure Chrome is stable...")
                time.sleep(10)
                
                print(f"\n🎉 SUCCESS! Chrome is running and ready to use.")
                print(f"   The browser will remain open after this script ends.")
                
            except Exception as status_error:
                print(f"\n⚠️  Chrome launched but status check failed: {status_error}")
                print(f"   The browser should still be running and usable.")
        else:
            print(f"\n❌ FAILED: Could not launch Chrome with any configuration.")
            
    except Exception as main_error:
        print(f"\n💥 CRITICAL ERROR: {main_error}")
        print(f"   Please check the troubleshooting tips above.")
    
    print(f"\n🏁 Script completed. Check your Chrome browser window.")
