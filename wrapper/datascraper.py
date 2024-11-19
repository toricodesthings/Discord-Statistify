#Monthly Listener Scraper
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import requests
SPOTIFY_WEB_ENDPOINT = "https://open.spotify.com"

#Scrape #1: Monthly Listener
async def scrape_monthly_listeners(artist_id):
    artist_url = f"{SPOTIFY_WEB_ENDPOINT}/artist/{artist_id}"
    monthly_listeners = "N/A"  # Default
    
    try:
        response = requests.get(artist_url)
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
    track_url = f"{SPOTIFY_WEB_ENDPOINT}/track/{track_id}"
    play_count = "N/A"  # Default

    try:
        # Check if the URL is valid and accessible
        response = requests.get(track_url)
        response.raise_for_status()

        async with async_playwright() as session:
            browser = await session.chromium.launch_persistent_context(
                user_data_dir="/tmp/playwright", 
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            page = await browser.new_page()

            try:
                # Navigate to the track page
                await page.goto(track_url, timeout=10000) 
                
                async def block_unnecessary(route):
                    if route.request.resource_type in ["image", "font", "media"]:
                        await route.abort()
                    else:
                        await route.continue_()
                await page.route("**/*", block_unnecessary)
                await page.wait_for_selector("span[data-testid='playcount']", timeout=10000)
                
                play_count_element = await page.query_selector("span[data-testid='playcount']")
                play_count = await play_count_element.inner_text() if play_count_element else "N/A"

                return play_count, None

            except TimeoutError:
                msg = "Error: Playcount request timed out"
                return play_count, msg
            except Exception as err:
                msg = f"Unexpected Error Occurred: {err}"
                return play_count, msg
            finally:
                await browser.close()

    except requests.exceptions.RequestException as e:
        print(f"URL Error: Unable to access the URL: {e}. Web Address may have changed or Spotify is down.")
        play_count = "N/A"
        return play_count, None
