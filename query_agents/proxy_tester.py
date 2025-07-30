from playwright.sync_api import sync_playwright
import time

# List of proxies to test
proxies_list = [
    "212.183.88.135:80",
    "104.254.140.182:80", 
    "172.67.74.230:80",
    "170.106.155.14:1080",
    "45.55.41.15:10743",
    "156.225.72.135:80",
    "103.111.219.245:4145"
]

def test_proxy_with_playwright(proxy_address):
    """Test proxy using Playwright browser"""
    
    host, port = proxy_address.split(':')
    proxy_config = {
        "server": f"http://{proxy_address}",
        # For SOCKS proxies, you might need to specify the protocol
        # "server": f"socks5://{proxy_address}" for SOCKS5
    }
    
    try:
        with sync_playwright() as p:
            # Launch browser with proxy
            browser = p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security'
                ]
            )
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            # Test endpoints that work well with browsers
            test_sites = [
                "http://httpbin.org/ip",
                "https://api.ipify.org?format=json",
                "http://icanhazip.com"
            ]
            
            for site in test_sites:
                try:
                    # Set longer timeout for proxy connections
                    response = page.goto(site, timeout=30000, wait_until='load')
                    
                    if response and response.status == 200:
                        # Get page content
                        content = page.content()
                        
                        # Extract IP from different formats
                        if 'httpbin' in site:
                            # Look for JSON response
                            if '"origin":' in content:
                                import re
                                ip_match = re.search(r'"origin":\s*"([^"]+)"', content)
                                if ip_match:
                                    ip = ip_match.group(1)
                                    browser.close()
                                    return True, f"{ip} (via {site.split('//')[1].split('/')[0]})"
                        
                        elif 'ipify' in site:
                            # JSON format
                            if '"ip":' in content:
                                import re
                                ip_match = re.search(r'"ip":\s*"([^"]+)"', content)
                                if ip_match:
                                    ip = ip_match.group(1)
                                    browser.close()
                                    return True, f"{ip} (via {site.split('//')[1].split('/')[0]})"
                        
                        else:
                            # Plain text IP
                            text = page.inner_text('body').strip()
                            if text and '.' in text and len(text.split('.')) == 4:
                                browser.close()
                                return True, f"{text} (via {site.split('//')[1].split('/')[0]})"
                
                except Exception as e:
                    continue  # Try next site
            
            browser.close()
            return False, "All test sites failed"
            
    except Exception as e:
        return False, f"Browser error: {str(e)}"

def test_socks_proxy_with_playwright(proxy_address):
    """Test SOCKS proxy specifically"""
    
    try:
        with sync_playwright() as p:
            # For SOCKS proxies, try both SOCKS4 and SOCKS5
            for protocol in ['socks5', 'socks4']:
                try:
                    proxy_config = {"server": f"{protocol}://{proxy_address}"}
                    
                    browser = p.chromium.launch(
                        headless=True,
                        proxy=proxy_config,
                        args=['--no-sandbox']
                    )
                    
                    context = browser.new_context()
                    page = context.new_page()
                    
                    response = page.goto("http://icanhazip.com", timeout=15000)
                    
                    if response and response.status == 200:
                        ip = page.inner_text('body').strip()
                        browser.close()
                        return True, f"{ip} (via {protocol.upper()})"
                    
                    browser.close()
                    
                except:
                    continue
        
        return False, "SOCKS connection failed"
        
    except Exception as e:
        return False, f"SOCKS error: {str(e)}"

def main():
    print("Testing proxies with Playwright + Chromium...\n")
    print("Note: This requires 'pip install playwright' and 'playwright install chromium'\n")
    print(f"{'Proxy':<25} {'Status':<12} {'Result/IP'}")
    print("-" * 70)
    
    working_proxies = []
    failed_proxies = []
    
    for proxy in proxies_list:
        print(f"{proxy:<25} ", end="", flush=True)
        
        # Determine if likely SOCKS proxy
        port = int(proxy.split(':')[1])
        is_likely_socks = port in [1080, 4145] or port > 8080
        
        if is_likely_socks:
            success, result = test_socks_proxy_with_playwright(proxy)
        else:
            success, result = test_proxy_with_playwright(proxy)
        
        if success:
            print(f"{'✅ PASS':<12} {result}")
            working_proxies.append(proxy)
        else:
            print(f"{'❌ FAIL':<12} {result}")
            failed_proxies.append((proxy, result))
        
        # Small delay between tests
        time.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY:")
    print(f"Working proxies: {len(working_proxies)}")
    print(f"Failed proxies: {len(failed_proxies)}")
    
    if working_proxies:
        print("\n✅ Working proxies:")
        for proxy in working_proxies:
            print(f"  - {proxy}")
        
        print("\nTo use working proxies in Playwright:")
        print("browser = p.chromium.launch(proxy={'server': 'http://PROXY:PORT'})")
    
    if failed_proxies:
        print("\n❌ Failed proxies:")
        for proxy, error in failed_proxies[:5]:  # Show first 5 errors
            print(f"  - {proxy} ({error})")

if __name__ == "__main__":
    main()