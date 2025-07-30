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

print("Navigating to Perplexity...")
try:
    # Navigate to Perplexity with longer timeout
    page.goto("https://www.perplexity.ai", wait_until="networkidle", timeout=60000)
    print("Page loaded successfully!")
except Exception as e:
    print(f"Error navigating to Perplexity: {e}")
    input("Press Enter to close browser...")
    browser.close()
    p.stop()
    exit(1)

print("Page loaded. Waiting 5 seconds for page to stabilize...")
time.sleep(5)

print("Please log in manually if needed, then press Enter...")
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
    # Wait for the textarea/input to be visible and ready
    # Perplexity might use different selectors, so we'll try a few
    try:
        page.wait_for_selector("textarea", timeout=10000)
        print("Textarea found!")
        selector = "textarea"
    except:
        try:
            page.wait_for_selector("input[type='text']", timeout=10000)
            print("Text input found!")
            selector = "input[type='text']"
        except:
            try:
                page.wait_for_selector("[contenteditable='true']", timeout=10000)
                print("Contenteditable div found!")
                selector = "[contenteditable='true']"
            except Exception as e:
                print(f"Could not find input field: {e}")
                input("Press Enter to close browser...")
                browser.close()
                p.stop()
                exit(1)
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
    
    if selector == "[contenteditable='true']":
        # For contenteditable elements, we need to click first
        page.locator(selector).click()
        page.locator(selector).fill(QUERY)
    else:
        page.locator(selector).fill(QUERY)
    
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
time.sleep(15)  # Perplexity might take longer to respond

print("Extracting answer...")
# Grab the full response text - Perplexity might use different selectors
try:
    # Try different possible selectors for Perplexity's response
    selectors_to_try = [
        "div.markdown",
        ".prose",
        "[data-testid='answer']",
        ".answer",
        ".response",
        "div[class*='answer']",
        "div[class*='response']"
    ]
    
    answer = None
    for selector in selectors_to_try:
        try:
            answer = page.locator(selector).inner_text()
            if answer and len(answer.strip()) > 10:  # Make sure we got a substantial answer
                print(f"Found answer using selector: {selector}")
                break
        except:
            continue
    
    if answer:
        print("Perplexity Answer:\n", answer)
    else:
        print("Could not extract answer with any known selector")
        print("You may need to manually check the response")
        
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