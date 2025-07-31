import os
import zipfile
import tempfile
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ---------------------------
# CONFIG — EDIT THESE VALUES
# ---------------------------

# 1) Point to your real Chrome user data directory and profile name
#    Example Windows: r"C:\Users\me\AppData\Local\Google\Chrome\User Data"
#    Example macOS:   "/Users/me/Library/Application Support/Google/Chrome"
USER_DATA_DIR = r"C:\Users\MULTI 88 G\AppData\Local\Google\Chrome\User Data"   # <-- change
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

def launch_chrome_with_profile():
    options = Options()

    # Real profile (keeps cookies, sessions, installed extensions)
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument(f"--profile-directory={PROFILE_DIR}")
    
    # Add this to allow running with existing Chrome instances
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Make it feel more like a regular session (optional tweaks)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Load extra extensions if you want (unpacked folders must use --load-extension)
    unpacked = [p for p in EXTRA_EXTENSIONS if Path(p).is_dir()]
    crxes    = [p for p in EXTRA_EXTENSIONS if Path(p).is_file() and p.lower().endswith(".crx")]

    if unpacked:
        # Multiple unpacked extensions can be comma-separated
        options.add_argument("--load-extension=" + ",".join(unpacked))

    for crx in crxes:
        options.add_extension(crx)

    # Optional: add proxy with auth via a temp extension
    if USE_PROXY and PROXY_HOST and PROXY_PORT:
        proxy_ext_zip = build_proxy_auth_extension(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        options.add_extension(proxy_ext_zip)

    # Keep Chrome open when script finishes
    options.add_experimental_option("detach", True)

    # Start Chrome (Selenium Manager will fetch a compatible driver)
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Error starting Chrome: {e}")
        print("\nTroubleshooting tips:")
        print("1. Close all Chrome instances and try again")
        print("2. Use a different profile (change PROFILE_DIR)")
        print("3. Or try running Chrome with --remote-debugging-port=9222 manually first")
        raise

    # Safety: if the same profile is already open in another Chrome, Chrome will refuse to start.
    # Ensure Chrome with this profile is closed before running the script.

    driver.get(START_URL)
    return driver

if __name__ == "__main__":
    driver = launch_chrome_with_profile()
    print("Chrome launched with your real profile. Current URL:", driver.current_url)
