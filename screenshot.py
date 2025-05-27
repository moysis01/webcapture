import os
import datetime
import time
import argparse
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import base64
from PIL import Image
from io import BytesIO

class WebPageCapture:
    def __init__(self, headless=True, timeout=30, wait_for_network=True):
        # Configure Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")  # Updated headless syntax
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Add user agent to prevent anti-bot measures
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
        
        self.driver = None
        try:
            self.driver = webdriver.Chrome(service=Service(), options=chrome_options)
            self.driver.set_page_load_timeout(timeout)
        except Exception as e:
            print(f"Error initializing Chrome driver: {e}")
            raise
            
        self.timeout = timeout
        self.wait_for_network = wait_for_network
        
    def capture(self, url, output_format='png', output_path=None, quality=90, width=1920, height=None):
        """
        Capture a webpage screenshot or PDF
        
        Args:
            url (str): URL to capture
            output_format (str): 'png', 'jpg', or 'pdf'
            output_path (str): Custom output path, or None for auto-generated
            quality (int): JPEG quality (1-100) if jpg format
            width (int): Viewport width
            height (int): Viewport height (None for full page)
        
        Returns:
            str: Path to saved file
        """
        if not self.driver:
            print("Driver not initialized")
            return None
            
        # Validate URL
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        try:
            parsed_url = urlparse(url)
            if not parsed_url.netloc:
                print("Invalid URL format")
                return None
        except Exception:
            print("Invalid URL")
            return None
            
        # Validate format
        if output_format not in ['png', 'jpg', 'pdf']:
            print(f"Invalid format: {output_format}. Using png instead.")
            output_format = 'png'
            
        # Generate output path if not provided
        if not output_path:
            domain = parsed_url.netloc.replace("www.", "")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
            if output_format == 'pdf':
                output_path = os.path.join(desktop, f"{domain}_{timestamp}.pdf")
            else:
                output_path = os.path.join(desktop, f"{domain}_{timestamp}.{output_format}")
                
        # Load the webpage
        print(f"Loading {url}...")
        try:
            self.driver.get(url)
            
            # Wait for page to be fully loaded
            if self.wait_for_network:
                self._wait_for_page_load()
                
            # Set viewport size
            if width and height:
                self.driver.set_window_size(width, height)
            elif width:
                # Get page height for full page capture
                total_height = self.driver.execute_script(
                    "return Math.max(document.body.scrollHeight, "
                    "document.documentElement.scrollHeight, "
                    "document.body.offsetHeight, "
                    "document.documentElement.offsetHeight, "
                    "document.body.clientHeight, "
                    "document.documentElement.clientHeight);"
                )
                self.driver.set_window_size(width, total_height)
                
            # Small delay to ensure rendering is complete
            time.sleep(1)
                
            # Capture based on format choice
            if output_format == 'pdf':
                success = self._capture_pdf(output_path)
            else:
                success = self._capture_image(output_path, output_format, quality)
                
            if success:
                print(f"Saved to: {output_path}")
                return output_path
                
        except TimeoutException:
            print(f"Timeout loading page: {url}")
        except WebDriverException as e:
            print(f"WebDriver error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            
        return None
            
    def _wait_for_page_load(self):
        """Wait for page to be fully loaded including network idle"""
        try:
            # First wait for document ready state
            WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Then check for network idle (optional but helps with SPAs)
            time.sleep(2)  # Additional buffer for network requests
            
        except TimeoutException:
            print("Timeout waiting for page to load completely")
            # Continue anyway, we'll capture what we have
            
    def _capture_image(self, output_path, format_choice, quality=90):
        """Capture screenshot as PNG or JPG"""
        try:
            # Try to use CDP for full page screenshot first (better quality)
            self.driver.execute_cdp_cmd("Page.enable", {})
            screenshot = self.driver.execute_cdp_cmd("Page.captureScreenshot", 
                                                    {"captureBeyondViewport": True,
                                                     "fromSurface": True})
            image_data = base64.b64decode(screenshot['data'])
            image = Image.open(BytesIO(image_data))

            # Save as PNG or JPG
            if format_choice == 'jpg':
                image = image.convert('RGB')
                image.save(output_path, 'JPEG', quality=quality)
            else:
                image.save(output_path, 'PNG')
                
            return True
            
        except Exception as e:
            print(f"Error in CDP screenshot, falling back to default: {e}")
            try:
                # Fallback to regular screenshot
                self.driver.save_screenshot(output_path)
                return True
            except Exception as e2:
                print(f"Screenshot error: {e2}")
                return False

    def _capture_pdf(self, output_path):
        """Generate PDF of the webpage"""
        try:
            # Advanced PDF options
            pdf_options = {
                "printBackground": True,
                "preferCSSPageSize": True,
                "marginTop": 0,
                "marginBottom": 0,
                "marginLeft": 0,
                "marginRight": 0,
                "scale": 1.0
            }
            
            result = self.driver.execute_cdp_cmd("Page.printToPDF", pdf_options)
            
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(result['data']))
            return True
            
        except Exception as e:
            print(f"PDF generation error: {e}")
            return False

    def close(self):
        """Close browser and clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

def run_interactive():
    """Run in interactive mode with user prompts"""
    try:
        capture = WebPageCapture(headless=True, timeout=45, wait_for_network=True)
        
        while True:
            url = input("\nPlease enter the URL of the webpage (or 'exit' to quit): ")
            if url.lower() in ['exit', 'quit', 'q']:
                break
                
            format_choice = input("Choose output format (png, jpg, pdf) [default: png]: ").lower() or 'png'
            
            if format_choice == 'jpg':
                quality = input("JPEG quality (1-100) [default: 90]: ") or 90
                try:
                    quality = int(quality)
                    if quality < 1 or quality > 100:
                        quality = 90
                except ValueError:
                    quality = 90
            else:
                quality = 90
                
            custom_path = input("Custom output path (or press Enter for desktop): ").strip() or None
            
            capture.capture(url, format_choice, custom_path, quality)
            
        capture.close()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'capture' in locals() and capture.driver:
            capture.close()

def run_cli():
    """Run as command line tool with arguments"""
    parser = argparse.ArgumentParser(description='Capture webpage screenshots or PDFs')
    parser.add_argument('url', help='URL of the webpage to capture')
    parser.add_argument('--format', choices=['png', 'jpg', 'pdf'], default='png',
                        help='Output format (png, jpg, or pdf)')
    parser.add_argument('--output', help='Custom output path')
    parser.add_argument('--quality', type=int, default=90, help='JPEG quality (1-100)')
    parser.add_argument('--width', type=int, default=1920, help='Viewport width')
    parser.add_argument('--height', type=int, help='Viewport height (defaults to full page)')
    parser.add_argument('--timeout', type=int, default=30, help='Page load timeout in seconds')
    
    args = parser.parse_args()
    
    try:
        capture = WebPageCapture(headless=True, timeout=args.timeout)
        capture.capture(args.url, args.format, args.output, args.quality, args.width, args.height)
        capture.close()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    
    # Check if running with arguments
    if len(sys.argv) > 1:
        sys.exit(run_cli())
    else:
        run_interactive()
