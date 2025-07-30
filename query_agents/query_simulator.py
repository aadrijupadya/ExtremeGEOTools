# from playwright.sync_api import sync_playwright
# import time
# import random
# import json
# import re
# import sys
# from datetime import datetime
# from typing import List, Dict, Any
# from playwright.sync_api import Error as PlaywrightError

# #this object aims to simulate the behavior of a user interacting with a search engine and analyzing the results

# class QuerySimulator:
#     # platform: the search engine to use
#     # input_file: the file containing the queries to run
#     # output_file: the file to write the results to
#     # proxy_file: the file containing proxy servers
#     def __init__(self, platform="perplexity", input_file="queries.txt", output_file=None, proxy_file="proxies.txt"):
#         self.platform = platform
#         self.results = []
#         self.brand_keywords = [
#             "Extreme Networks", "Extreme", "ExtremeNetworks",
#             "enterasys", "avaya", "cisco", "juniper", "arista",
#             "hpe", "hp", "dell", "netgear", "ubiquiti"
#         ]
        
#         # Setup file I/O
#         self.input_file = input_file
#         self.proxy_file = proxy_file
#         self.proxies = []
#         self.current_proxy_index = 0
#         self.proxy_failures = {}  # Track failed proxies
        
#         if output_file is None:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             output_file = f"simulation_output_{self.platform}_{timestamp}.txt"
#         self.output_file = output_file
        
#         # Redirect stdout to file
#         self.original_stdout = sys.stdout
#         self.log_file = open(output_file, 'w', encoding='utf-8')
#         sys.stdout = self.log_file
        
#         # Load proxies
#         self.load_proxies()
    
#     def load_proxies(self) -> List[Dict[str, str]]:
#         """Load proxies from file and parse them"""
#         try:
#             with open(self.proxy_file, 'r', encoding='utf-8') as f:
#                 proxy_lines = [line.strip() for line in f if line.strip()]
            
#             for line in proxy_lines:
#                 # Parse proxy format: host:port or protocol://host:port
#                 if '://' in line:
#                     # Format: protocol://host:port
#                     protocol, rest = line.split('://', 1)
#                     if ':' in rest:
#                         host, port = rest.rsplit(':', 1)
#                     else:
#                         host, port = rest, '80'
#                 else:
#                     # Format: host:port (assume http)
#                     if ':' in line:
#                         host, port = line.rsplit(':', 1)
#                         protocol = 'http'
#                     else:
#                         host, port, protocol = line, '80', 'http'
                
#                 # Determine if it's SOCKS proxy based on common SOCKS ports
#                 if port in ['1080', '1081', '4145', '5145']:
#                     # SOCKS proxy
#                     proxy_dict = {
#                         'server': f"socks5://{host}:{port}"
#                     }
#                 else:
#                     # HTTP proxy
#                     proxy_dict = {
#                         'server': f"http://{host}:{port}"
#                     }
                
#                 self.proxies.append(proxy_dict)
#                 self.proxy_failures[len(self.proxies) - 1] = 0
            
#             self.log(f"Loaded {len(self.proxies)} proxies from {self.proxy_file}")
#             for i, proxy in enumerate(self.proxies):
#                 self.log(f"  Proxy {i+1}: {proxy['server']}")
            
#             return self.proxies
            
#         except FileNotFoundError:
#             self.log(f"Warning: Proxy file '{self.proxy_file}' not found. Running without proxy.")
#             return []
#         except Exception as e:
#             self.log(f"Error loading proxies: {e}")
#             return []
    
#     def get_next_proxy(self) -> Dict[str, str]:
#         """Get the next proxy in rotation, skipping failed ones"""
#         if not self.proxies:
#             return None
        
#         # Try to find a working proxy
#         attempts = 0
#         max_attempts = len(self.proxies)
        
#         while attempts < max_attempts:
#             proxy = self.proxies[self.current_proxy_index]
            
#             # Skip proxies with too many failures
#             if self.proxy_failures[self.current_proxy_index] < 3:
#                 self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
#                 return proxy
            
#             # Move to next proxy
#             self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
#             attempts += 1
        
#         # If all proxies have failed, reset failure counts and try again
#         self.log("All proxies have failed. Resetting failure counts...")
#         for key in self.proxy_failures:
#             self.proxy_failures[key] = 0
        
#         return self.proxies[0] if self.proxies else None
    
#     def mark_proxy_failed(self, proxy_index: int):
#         """Mark a proxy as failed"""
#         if proxy_index in self.proxy_failures:
#             self.proxy_failures[proxy_index] += 1
#             self.log(f"Proxy {proxy_index + 1} failed (failure count: {self.proxy_failures[proxy_index]})")
    
#     def get_current_proxy_index(self, proxy: Dict[str, str]) -> int:
#         """Get the index of the current proxy"""
#         for i, p in enumerate(self.proxies):
#             if p['server'] == proxy['server']:
#                 return i
#         return -1

#     #logs messages to both the console and the log file
#     def log(self, message: str):
#         """Log message to both file and console"""
#         timestamp = datetime.now().strftime("%H:%M:%S")
#         formatted_message = f"[{timestamp}] {message}"
#         print(formatted_message)
#         # Also print to console
#         self.original_stdout.write(formatted_message + '\n')
#         self.original_stdout.flush()
    
#     #attempts to read queries from the input file, throws an error if the file is not found or if there is an error reading the file
#     def read_queries_from_file(self) -> List[str]:
#         """Read queries from input file"""
#         try:
#             with open(self.input_file, 'r', encoding='utf-8') as f:
#                 queries = [line.strip() for line in f if line.strip()]
#             self.log(f"Loaded {len(queries)} queries from {self.input_file}")
#             return queries
#         except FileNotFoundError:
#             self.log(f"Error: Input file '{self.input_file}' not found")
#             return []
#         except Exception as e:
#             self.log(f"Error reading queries: {e}")
#             return []
    
#     # uses playwright to setup a stealth browser for automation with proxy support
#     def setup_browser(self, proxy: Dict[str, str] = None, retries: int = 3):
#         """Setup stealth browser for automation with proxy support"""
#         for attempt in range(retries):
#             try:
#                 self.log("Starting Playwright...")
#                 self.p = sync_playwright().start()
                
#                 # Get proxy for this session
#                 if proxy is None:
#                     proxy = self.get_next_proxy()
                
#                 if proxy:
#                     self.log(f"Using proxy: {proxy['server']}")
                
#                 self.log("Launching browser...")
#                 # Use a more typical human viewport
#                 browser_args = [
#                     '--disable-blink-features=AutomationControlled',
#                     '--disable-web-security',
#                     '--disable-features=VizDisplayCompositor',
#                     '--no-sandbox',
#                     '--disable-setuid-sandbox',
#                     '--disable-dev-shm-usage',
#                     '--disable-accelerated-2d-canvas',
#                     '--no-first-run',
#                     '--no-zygote',
#                     '--disable-gpu'
#                 ]
                
#                 self.browser = self.p.chromium.launch(
#                     headless=False,
#                     args=browser_args
#                 )
                
#                 # Setup context with proxy
#                 context_options = {
#                     'viewport': {'width': 1280, 'height': 1200},
#                     'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#                     'extra_http_headers': {
#                         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#                         'Accept-Language': 'en-US,en;q=0.5',
#                         'Accept-Encoding': 'gzip, deflate, br',
#                         'DNT': '1',
#                         'Connection': 'keep-alive',
#                         'Upgrade-Insecure-Requests': '1',
#                     }
#                 }
                
#                 # Add proxy to context if available
#                 if proxy:
#                     context_options['proxy'] = proxy
                
#                 self.context = self.browser.new_context(**context_options)
#                 self.page = self.context.new_page()
#                 self.page.add_init_script("""
#                     Object.defineProperty(navigator, 'webdriver', {
#                         get: () => undefined,
#                     });
#                 """)
                
#                 # Test the proxy by making a simple request
#                 if proxy:
#                     try:
#                         self.page.goto("https://httpbin.org/ip", timeout=15000)
#                         ip_info = self.page.locator("body").inner_text()
#                         self.log(f"Proxy test successful. IP: {ip_info}")
#                     except Exception as e:
#                         self.log(f"Proxy test failed: {e}")
#                         # Mark proxy as failed
#                         proxy_index = self.get_current_proxy_index(proxy)
#                         if proxy_index >= 0:
#                             self.mark_proxy_failed(proxy_index)
#                         raise
                
#                 return True
                
#             except Exception as e:
#                 self.log(f"Browser setup attempt {attempt + 1} failed: {e}")
                
#                 # Clean up failed attempt
#                 try:
#                     if hasattr(self, 'browser'):
#                         self.browser.close()
#                     if hasattr(self, 'p'):
#                         self.p.stop()
#                 except:
#                     pass
                
#                 if attempt < retries - 1:
#                     # Try with a different proxy
#                     proxy = self.get_next_proxy()
#                     self.log(f"Retrying with different proxy...")
#                     time.sleep(2)
#                 else:
#                     raise Exception(f"Failed to setup browser after {retries} attempts")
        
#         return False

#     def human_type(self, selector, text):
#         self.page.locator(selector).click()
#         for char in text:
#             self.page.keyboard.type(char)
#             time.sleep(random.uniform(0.05, 0.18))  # Simulate human typing speed

#     def random_mouse_move_and_scroll(self):
#         width, height = 1280, 900
#         for _ in range(random.randint(2, 4)):
#             x = random.randint(0, width)
#             y = random.randint(0, height)
#             self.page.mouse.move(x, y)
#             time.sleep(random.uniform(0.08, 0.25))
#         # Random scroll
#         scroll_amount = random.randint(100, 600)
#         self.page.mouse.wheel(0, scroll_amount)
#         time.sleep(random.uniform(0.1, 0.3))

#     def navigate_to_platform(self):
#         """Navigate to the specified platform"""
#         if self.platform == "perplexity":
#             url = "https://www.perplexity.ai"
#         elif self.platform == "chatgpt":
#             url = "https://chat.openai.com"
#         else:
#             raise ValueError(f"Unsupported platform: {self.platform}")
            
#         self.log(f"Navigating to {self.platform}...")
#         try:
#             # Use simpler navigation without waiting for networkidle
#             self.page.goto(url, timeout=30000)
#             self.log("Page loaded successfully!")
#             # Wait a bit for page to stabilize
#             time.sleep(2.5)
#             return True
#         except Exception as e:
#             self.log(f"Error navigating to {self.platform}: {e}")
#             self.log("Trying to continue anyway...")
#             return True  # Continue even if navigation had issues
    
#     def find_input_field(self):
#         """Find the input field on the page"""
#         selectors_to_try = [
#             "textarea",
#             "input[type='text']",
#             "[contenteditable='true']",
#             "input[placeholder*='ask']",
#             "input[placeholder*='question']",
#             "input",
#             "textarea[placeholder*='ask']",
#             "textarea[placeholder*='question']"
#         ]
        
#         for selector in selectors_to_try:
#             try:
#                 self.page.wait_for_selector(selector, timeout=2000)
#                 self.log(f"Input field found: {selector}")
#                 return selector
#             except:
#                 continue
#         # If no selector found, try to find any input-like element
#         try:
#             elements = self.page.query_selector_all("input, textarea, [contenteditable]")
#             if elements:
#                 self.log(f"Found {len(elements)} potential input elements")
#                 return "input"
#         except:
#             pass
#         return None

#     def submit_query(self, query: str):
#         selector = self.find_input_field()
#         if not selector:
#             self.log("Could not find input field - trying generic approach")
#             try:
#                 self.page.click("body")
#                 for char in query:
#                     self.page.keyboard.type(char)
#                     time.sleep(random.uniform(0.05, 0.18))
#                 self.page.keyboard.press("Enter")
#                 self.log(f"Query submitted via keyboard: {query}")
#                 return True
#             except Exception as e:
#                 self.log(f"Keyboard submission failed: {e}")
#                 return False
#         try:
#             # Human-like mouse movement and scrolling before typing
#             self.random_mouse_move_and_scroll()
#             # Occasional idle pause
#             if random.random() < 0.2:
#                 idle_time = random.uniform(0.7, 2.0)
#                 self.log(f"Idling for {idle_time:.2f} seconds before typing...")
#                 time.sleep(idle_time)
#             # Human-like typing
#             if selector == "[contenteditable='true']":
#                 self.page.locator(selector).click()
#                 self.page.locator(selector).fill("")
#                 self.human_type(selector, query)
#             else:
#                 self.page.locator(selector).fill("")
#                 self.human_type(selector, query)
#             # Random mouse move after typing
#             if random.random() < 0.5:
#                 self.random_mouse_move_and_scroll()
#             time.sleep(random.uniform(0.15, 0.35))
#             submission_success = False
#             try:
#                 self.page.keyboard.press("Enter")
#                 submission_success = True
#                 self.log(f"Query submitted via Enter key: {query}")
#             except Exception as e:
#                 self.log(f"Enter key submission failed: {e}")
#             if not submission_success:
#                 submit_selectors = [
#                     "button[type='submit']",
#                     "button:has-text('Send')",
#                     "button:has-text('Submit')",
#                     "button:has-text('Ask')",
#                     "button[aria-label*='send']",
#                     "button[aria-label*='submit']",
#                     "[data-testid='send-button']",
#                     ".send-button",
#                     ".submit-button"
#                 ]
#                 for submit_selector in submit_selectors:
#                     try:
#                         if self.page.locator(submit_selector).is_visible(timeout=1000):
#                             self.page.locator(submit_selector).click()
#                             submission_success = True
#                             self.log(f"Query submitted via submit button ({submit_selector}): {query}")
#                             break
#                     except:
#                         continue
#             if not submission_success:
#                 try:
#                     self.page.keyboard.press("Control+Enter")
#                     submission_success = True
#                     self.log(f"Query submitted via Ctrl+Enter: {query}")
#                 except Exception as e:
#                     self.log(f"Ctrl+Enter submission failed: {e}")
#             if not submission_success:
#                 try:
#                     self.page.locator(selector).click()
#                     time.sleep(0.1)
#                     self.page.keyboard.press("Enter")
#                     submission_success = True
#                     self.log(f"Query submitted via click + Enter: {query}")
#                 except Exception as e:
#                     self.log(f"Click + Enter submission failed: {e}")
#             if submission_success:
#                 return True
#             else:
#                 self.log("All submission methods failed")
#                 return False
#         except Exception as e:
#             self.log(f"Error submitting query: {e}")
#             return False
    
#     def extract_response(self):
#         """Extract response from the platform"""
#         selectors_to_try = [
#             "div.markdown",
#             ".prose",
#             "[data-testid='answer']",
#             ".answer",
#             ".response",
#             "div[class*='answer']",
#             "div[class*='response']",
#             ".chat-message",
#             "[data-testid='message']",
#             "div[class*='message']",
#             "div[class*='content']",
#             "p",  # Try paragraphs as fallback
#             "div"  # Try any div as last resort
#         ]
        
#         for selector in selectors_to_try:
#             try:
#                 # Much shorter timeout
#                 self.page.wait_for_selector(selector, timeout=3000)
#                 response = self.page.locator(selector).inner_text()
#                 if response and len(response.strip()) > 5:  # Lower threshold
#                     self.log(f"Response extracted using: {selector}")
#                     return response
#             except:
#                 continue
        
#         # If no response found, try to get any text from the page
#         try:
#             body_text = self.page.locator("body").inner_text()
#             if len(body_text) > 50:  # If we have substantial text
#                 self.log("Using body text as response")
#                 return body_text
#         except:
#             pass
            
#         return None
    
#     def extract_sources(self, response: str) -> List[str]:
#         """Extract source URLs from response"""
#         # Look for URLs in the response
#         url_pattern = r'https?://[^\s\)]+'
#         urls = re.findall(url_pattern, response)
        
#         # Also look for source mentions
#         source_patterns = [
#             r'source[s]?\s*:\s*(https?://[^\s\)]+)',
#             r'from\s+(https?://[^\s\)]+)',
#             r'according\s+to\s+(https?://[^\s\)]+)',
#             r'cited\s+from\s+(https?://[^\s\)]+)'
#         ]
        
#         for pattern in source_patterns:
#             matches = re.findall(pattern, response, re.IGNORECASE)
#             urls.extend(matches)
        
#         return list(set(urls))  # Remove duplicates
    
#     def analyze_brand_mentions(self, response: str) -> Dict[str, Any]:
#         """Analyze brand mentions in the response"""
#         analysis = {
#             'extreme_networks_mentions': 0,
#             'competitor_mentions': {},
#             'brand_visibility_score': 0,
#             'mentions': []
#         }
        
#         response_lower = response.lower()
        
#         # Count Extreme Networks mentions
#         for keyword in ["extreme networks", "extreme", "extremenetworks"]:
#             count = response_lower.count(keyword.lower())
#             analysis['extreme_networks_mentions'] += count
#             if count > 0:
#                 analysis['mentions'].append({
#                     'brand': 'Extreme Networks',
#                     'keyword': keyword,
#                     'count': count
#                 })
        
#         # Count competitor mentions
#         competitors = {
#             'cisco': ['cisco'],
#             'juniper': ['juniper'],
#             'arista': ['arista'],
#             'hpe': ['hpe', 'hewlett packard enterprise'],
#             'dell': ['dell'],
#             'netgear': ['netgear'],
#             'ubiquiti': ['ubiquiti']
#         }
        
#         for competitor, keywords in competitors.items():
#             count = 0
#             for keyword in keywords:
#                 count += response_lower.count(keyword.lower())
#             if count > 0:
#                 analysis['competitor_mentions'][competitor] = count
#                 analysis['mentions'].append({
#                     'brand': competitor,
#                     'keyword': keywords[0],
#                     'count': count
#                 })
        
#         # Calculate brand visibility score
#         total_mentions = analysis['extreme_networks_mentions'] + sum(analysis['competitor_mentions'].values())
#         if total_mentions > 0:
#             analysis['brand_visibility_score'] = (analysis['extreme_networks_mentions'] / total_mentions) * 100
        
#         return analysis
    
#     def run_query(self, query: str, wait_time: int = 5) -> dict:
#         self.log(f"\n--- Running Query: {query} ---")
#         if not self.submit_query(query):
#             return None
#         # Human-like idle after submitting
#         if random.random() < 0.3:
#             idle_time = random.uniform(0.5, 1.5)
#             self.log(f"Idling for {idle_time:.2f} seconds after submitting...")
#             time.sleep(idle_time)
#         self.log(f"Waiting {wait_time} seconds for response...")
#         time.sleep(wait_time)
#         response = self.extract_response()
#         if not response:
#             self.log("Could not extract response")
#             return None
#         sources = self.extract_sources(response)
#         brand_analysis = self.analyze_brand_mentions(response)
#         result = {
#             'query': query,
#             'response': response,
#             'sources': sources,
#             'brand_analysis': brand_analysis,
#             'timestamp': datetime.now().isoformat(),
#             'platform': self.platform
#         }
#         self.results.append(result)
#         return result

#     def run_query_batch(self, queries: list, wait_time: int = 5, rotate_proxy_every: int = 5):
#         """Run queries with proxy rotation"""
#         self.log(f"Starting batch of {len(queries)} queries with proxy rotation every {rotate_proxy_every} queries...")
        
#         for i, query in enumerate(queries, 1):
#             self.log(f"\n[{i}/{len(queries)}] Processing query...")
            
#             # Rotate proxy if needed
#             if i % rotate_proxy_every == 1 and i > 1:  # Rotate after first batch
#                 self.log("Rotating to next proxy...")
#                 try:
#                     self.cleanup_browser()
#                     time.sleep(2)  # Brief pause
#                     self.setup_browser()
#                     self.navigate_to_platform()
#                 except Exception as e:
#                     self.log(f"Error during proxy rotation: {e}")
#                     # Try to continue with current setup
            
#             try:
#                 if hasattr(self, 'page') and self.page.is_closed():
#                     self.log("[ALERT] Page was closed unexpectedly. Stopping simulation.")
#                     break
                    
#                 result = self.run_query(query, wait_time)
#                 if result:
#                     self.log(f"✓ Query completed successfully")
#                     self.log(f"  - Extreme Networks mentions: {result['brand_analysis']['extreme_networks_mentions']}")
#                     self.log(f"  - Sources found: {len(result['sources'])}")
#                     self.log(f"  - Brand visibility score: {result['brand_analysis']['brand_visibility_score']:.1f}%")
#                 else:
#                     self.log(f"✗ Query failed")
                    
#             except PlaywrightError as e:
#                 self.log(f"[ALERT] Playwright error: {e}. The browser or page may have been closed. Stopping simulation.")
#                 break
#             except Exception as e:
#                 self.log(f"[ALERT] Unexpected error: {e}. Continuing with next query...")
#                 # Try to recover
#                 try:
#                     self.cleanup_browser()
#                     self.setup_browser()
#                     self.navigate_to_platform()
#                 except:
#                     self.log("Failed to recover. Stopping simulation.")
#                     break
                    
#             if i < len(queries):
#                 delay = random.uniform(2, 5)  # Longer delay between queries
#                 if random.random() < 0.3:
#                     self.log(f"Idling for {delay:.2f} seconds before next query...")
#                 time.sleep(delay)
    
#     def generate_report(self, filename: str = None):
#         """Generate a comprehensive report"""
#         if not filename:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             filename = f"query_analysis_report_{self.platform}_{timestamp}.json"
        
#         report = {
#             'summary': {
#                 'total_queries': len(self.results),
#                 'platform': self.platform,
#                 'timestamp': datetime.now().isoformat(),
#                 'input_file': self.input_file,
#                 'output_file': self.output_file,
#                 'proxy_file': self.proxy_file,
#                 'total_proxies': len(self.proxies),
#                 'proxy_failures': self.proxy_failures
#             },
#             'brand_visibility_summary': {
#                 'total_extreme_mentions': sum(r['brand_analysis']['extreme_networks_mentions'] for r in self.results),
#                 'total_competitor_mentions': {},
#                 'average_visibility_score': 0
#             },
#             'source_analysis': {
#                 'total_sources': sum(len(r['sources']) for r in self.results),
#                 'unique_sources': list(set([url for r in self.results for url in r['sources']]))
#             },
#             'detailed_results': self.results
#         }
        
#         # Calculate competitor totals
#         all_competitors = set()
#         for result in self.results:
#             all_competitors.update(result['brand_analysis']['competitor_mentions'].keys())
        
#         for competitor in all_competitors:
#             total = sum(r['brand_analysis']['competitor_mentions'].get(competitor, 0) for r in self.results)
#             report['brand_visibility_summary']['total_competitor_mentions'][competitor] = total
        
#         # Calculate average visibility score
#         scores = [r['brand_analysis']['brand_visibility_score'] for r in self.results]
#         report['brand_visibility_summary']['average_visibility_score'] = sum(scores) / len(scores) if scores else 0
        
#         # Save report
#         with open(filename, 'w') as f:
#             json.dump(report, f, indent=2)
        
#         self.log(f"\n📊 Report generated: {filename}")
#         self.log(f"📈 Total Extreme Networks mentions: {report['brand_visibility_summary']['total_extreme_mentions']}")
#         self.log(f"🔗 Total sources found: {report['source_analysis']['total_sources']}")
#         self.log(f"📊 Average visibility score: {report['brand_visibility_summary']['average_visibility_score']:.1f}%")
#         self.log(f"🔄 Proxies used: {len(self.proxies)}")
        
#         return report
    
#     def cleanup_browser(self):
#         """Clean up browser resources only"""
#         try:
#             if hasattr(self, 'page'):
#                 self.page.close()
#             if hasattr(self, 'context'):
#                 self.context.close()
#             if hasattr(self, 'browser'):
#                 self.browser.close()
#             if hasattr(self, 'p'):
#                 self.p.stop()
#         except Exception as e:
#             self.log(f"Error during browser cleanup: {e}")
    
#     def cleanup(self):
#         """Clean up all resources and restore stdout"""
#         self.cleanup_browser()
        
#         # Restore stdout and close log file
#         sys.stdout = self.original_stdout
#         if hasattr(self, 'log_file'):
#             self.log_file.close()

# # Example usage
# if __name__ == "__main__":
#     # Initialize simulator with proxy support
#     simulator = QuerySimulator(
#         platform="perplexity",
#         input_file="queries.txt",
#         output_file="simulation_log.txt",
#         proxy_file="proxies.txt"
#     )
    
#     try:
#         # Read queries from file
#         queries = simulator.read_queries_from_file()
#         if not queries:
#             print("No queries found. Exiting.")
#             exit(1)
        
#         simulator.setup_browser()
#         simulator.navigate_to_platform()
#         simulator.log("Attempting to run queries with proxy rotation...")
        
#         # Run queries with proxy rotation every 3 queries
#         simulator.run_query_batch(queries, rotate_proxy_every=3)
#         simulator.generate_report()
        
#     except Exception as e:
#         simulator.log(f"Unexpected error: {e}")
#         print(f"Error: {e}")
#     finally:
#         simulator.cleanup()

# Changes to make based on your new situation (Cloudflare Warp enabled):
# 1. Skip proxy loading and logic since you now rely on a clean VPN IP (Warp)
# 2. Disable proxy testing and rotation
# 3. Add IP verification step for logging purposes
# 4. Optionally: Make proxy use configurable via flag

# Updated: proxy logic removed, added IP fetch from https://api.ipify.org

from playwright.sync_api import sync_playwright
import time
import random
import json
import re
import sys
from datetime import datetime
from typing import List, Dict, Any
from playwright.sync_api import Error as PlaywrightError

class QuerySimulator:
    def __init__(self, platform="perplexity", input_file="queries.txt", output_file=None):
        self.platform = platform
        self.results = []
        self.brand_keywords = [
            "Extreme Networks", "Extreme", "ExtremeNetworks",
            "enterasys", "avaya", "cisco", "juniper", "arista",
            "hpe", "hp", "dell", "netgear", "ubiquiti"
        ]

        self.input_file = input_file
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"simulation_output_{self.platform}_{timestamp}.txt"
        self.output_file = output_file

        self.original_stdout = sys.stdout
        self.log_file = open(output_file, 'w', encoding='utf-8')
        sys.stdout = self.log_file

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        self.original_stdout.write(formatted_message + '\n')
        self.original_stdout.flush()

    def read_queries_from_file(self) -> List[str]:
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                queries = [line.strip() for line in f if line.strip()]
            self.log(f"Loaded {len(queries)} queries from {self.input_file}")
            return queries
        except FileNotFoundError:
            self.log(f"Error: Input file '{self.input_file}' not found")
            return []

    def setup_browser(self):
        try:
            self.log("Starting Playwright...")
            self.p = sync_playwright().start()
            browser_args = [
                '--disable-blink-features=AutomationControlled'
            ]
            self.browser = self.p.chromium.launch(headless=False, args=browser_args)
            context_options = {
                'viewport': {'width': 1280, 'height': 1200},
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            self.context = self.browser.new_context(**context_options)
            self.page = self.context.new_page()
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)

            # Log current IP
            self.page.goto("https://api.ipify.org?format=json", timeout=10000)
            ip = self.page.locator("body").inner_text()
            self.log(f"Current IP: {ip}")

            return True
        except Exception as e:
            self.log(f"Error setting up browser: {e}")
            return False

    def cleanup(self):
        try:
            if hasattr(self, 'page'):
                self.page.close()
            if hasattr(self, 'context'):
                self.context.close()
            if hasattr(self, 'browser'):
                self.browser.close()
            if hasattr(self, 'p'):
                self.p.stop()
        except Exception as e:
            self.log(f"Error during cleanup: {e}")
        sys.stdout = self.original_stdout
        if hasattr(self, 'log_file'):
            self.log_file.close()

# Usage
if __name__ == "__main__":
    simulator = QuerySimulator(
        platform="perplexity",
        input_file="queries.txt"
    )

    try:
        queries = simulator.read_queries_from_file()
        if not queries:
            print("No queries found. Exiting.")
            exit(1)
        if simulator.setup_browser():
            simulator.log("Browser setup complete.")
            # Ready for additional querying logic...
    finally:
        simulator.cleanup()
