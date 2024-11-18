SPOTIFY_WEB_ENDPOINT = "https://open.spotify.com"
#Monthly Listener Scraper
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import requests

#Scrape #1: Monthly Listener
async def scrape_monthly_listeners(artist_id):
    artist_url = f"{SPOTIFY_WEB_ENDPOINT}/artist/{artist_id}"
    
    print(artist_url)
    monthly_listeners = "N/A"  # Default
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(artist_url, headers=headers)
        response.raise_for_status()

        async with async_playwright() as session:
            browser = await session.chromium.launch_persistent_context(
                user_data_dir="/tmp/playwright",  # Use persistent context to avoid repeated loading
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = await browser.new_page()
        
            async def block_unnecessary(route):
                if route.request.resource_type in ["image", "font", "media"]:
                    await route.abort()
                else:
                    await route.continue_()

            await page.route("**/*", block_unnecessary)

            try:
                await page.goto(artist_url, timeout=10000)  
                await page.wait_for_selector("span:has-text('monthly listeners')", timeout=10000) 
                monthly_listeners_txt = await page.inner_text("span:has-text('monthly listeners')")

                monthly_listeners = ''.join(filter(str.isdigit, monthly_listeners_txt)) 
                if not monthly_listeners:
                    monthly_listeners = "N/A"
                
            except TimeoutError:
                msg = "Error: Monthly listener request timed out"
                return monthly_listeners, msg
            except Exception as err:
                msg = f"Unexpected Error Occurred: {err}"
                return monthly_listeners, msg
            finally:
                await browser.close()

        return monthly_listeners, None

    except requests.exceptions.RequestException as e:
        print(f"URL Error: Unable to access the URL: {e}. Web Address may have changed or Spotify is down.")
        monthly_listeners = "N/A"
        return monthly_listeners, None


#Scrape #2: Track Playcount
async def scrape_track_playcount(track_id):
    track_url = f"{SPOTIFY_WEB_ENDPOINT}/tracks/{track_id}"
    play_count = "N/A" #Default
    try:
        # Check if the URL is valid and accessible
        response = requests.get(track_url)
        response.raise_for_status()
        
        async with async_playwright() as session:
            browser = await session.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.wait_for_selector("span[data-testid='playcount']", timeout=10000)
            
                play_count_element = await page.query_selector("span.encore-text.encore-text-body-small.encore-internal-color-text-subdued.w1TBi3o5CTM7zW1EB3Bm")
                play_count = await play_count_element.inner_text() if play_count_element else "N/A"
                
                await browser.close()
                
                return play_count, None
            except PlaywrightTimeoutError:
                msg = "Error: Playcount request timed out"
                return play_count, msg
            except Exception as err:
                msg = f"Unexpected Error Occurred: {err}"
                return play_count, msg
            finally:
                await browser.close()
                
    except requests.exceptions.RequestException as e:
        print(f"URL Error: Unable to access the URL: {e}. Web Address may have changed or Spotify is down.")
        monthly_listeners = "N/A"
        
        return monthly_listeners, None