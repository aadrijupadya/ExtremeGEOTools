from playwright.sync_api import sync_playwright
import time
import random

QUERY = "OFDMA benefits"

print("Starting Playwright...")
p = sync_playwright().start()
print("Launching browser...")

# Launch browser with stealth settings
browser = p.chromium.launch(
    headless=False,
    args=[
        '--disable-blink-features=AutomationControlled',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu'
    ]
)

# Create context with stealth settings
context = browser.new_context(
    viewport={'width': 1920, 'height': 1080},
    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    extra_http_headers={
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
)

page = context.new_page()

# Add script to hide automation
page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });
""")

print("Navigating to ChatGPT...")
try:
    # Navigate to ChatGPT with longer timeout
    page.goto("https://chat.openai.com", wait_until="networkidle", timeout=60000)
    print("Page loaded successfully!")
except Exception as e:
    print(f"Error navigating to ChatGPT: {e}")
    input("Press Enter to close browser...")
    browser.close()
    p.stop()
    exit(1)

print("Page loaded. Waiting 5 seconds for page to stabilize...")
time.sleep(5)

print("Please log in manually, then press Enter...")
input()

print("Checking if page is still loaded...")
try:
    # Check if page is still accessible
    current_url = page.url
    print(f"Current URL: {current_url}")
    
    # Add random delay to seem more human
    random_delay = random.uniform(2, 4)
    print(f"Waiting {random_delay:.1f} seconds...")
    time.sleep(random_delay)
    
    print("Waiting for page to be ready...")
    # Wait for the textarea to be visible and ready
    page.wait_for_selector("textarea", timeout=30000)  # Wait up to 30 seconds
    print("Textarea found!")
except Exception as e:
    print(f"Error: {e}")
    print("Browser may have been closed or page redirected")
    input("Press Enter to close browser...")
    browser.close()
    p.stop()
    exit(1)

print("Filling query...")
# Type the query with human-like delays
try:
    # Add random delay before typing
    time.sleep(random.uniform(1, 2))
    page.locator("textarea").fill(QUERY)
    time.sleep(random.uniform(0.5, 1))
    page.keyboard.press("Enter")
    print("Query submitted!")
except Exception as e:
    print(f"Error filling query: {e}")
    input("Press Enter to close browser...")
    browser.close()
    p.stop()
    exit(1)

print("Waiting for response...")
# Wait for response to render
time.sleep(10)  # crude wait; later replace with smarter wait-for-selector

print("Extracting answer...")
# Grab the full response text
try:
    answer = page.locator("div.markdown").inner_text()
    print("ChatGPT Answer:\n", answer)
except Exception as e:
    print(f"Error extracting answer: {e}")
    print("Response might not be ready yet or selector changed")

# Keep browser open until user presses Enter
print("Script complete. Press Enter to close browser...")
input()

print("Closing browser...")
browser.close()
p.stop()
print("Done!")
