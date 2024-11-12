# discord-statistify

WIP Spotify Statistics Discord Bot utilizing Spotify Web API and Possible Scraping

This is a work-in-progress discord that connects with Spotify's Web API to retrieve data about artists, playlist, songs, and many more. Web API Access is built in and requires no premade libraries, however, users will need to create both a Discord Web Application and Spotify Web Application in their respective developer portals for the bot to function. See sections "Preparation" for more info and see section "Library Requirements" to install the required python libraries.

## Preparation
Setting up the bot requires two keys, one from Discord Developer Portal, and one from Spotify Web API. Before that, clone this repo.

### Spotify Web API Setup
To set up a Spotify Developer account and obtain an API key:

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Create a new app to get your **Client ID** and **Client Secret**. Keep these a SECRET.
3. Input those into the .env file

## To-Dos:
+ ~~Track data fetch and audio analysis~~
+ ~~Make save command per user based~~
+ ~~Expand get command to playlist~~
+ ~~Expand get command to user~~
+ ~~Expand get command to albums~~
+ ~Add buttons to save in all get commands~
+ Search function for categories
+ ~Expand save command to tracks, artists, and playlists~
+ Add Web Scraping for Monthly Listener
+ Add Web Scraping for Tracks
+ Clean up & Add Proper Commenting

## Lib Links 
* https://pypi.org/project/aiohttp/
* https://pypi.org/project/discord.py/
* https://pypi.org/project/python-dotenv/
* https://pypi.org/project/playwright/

## A Few Final Notes
+ Bot is has majority of functions built but is unoptimized and is missing some documentation for now.
+ Feel free to contribute any improvements or fork this repo
+ I will consider adding Spotify Audio Books data in the future, but it's not that relevant for me right now
+ A rebuild in JS of certain modules will happen to be used with my personal website
+ This bot will have the ability to scrape for the two public but relevant data using playwright, playcount and monthly listener. However, this is for educational purposes only and the setting is off by default (and only the Official Spotify API data will be used)! The scraper is also NOT resistant to website updates and might break but I will try to maintain it. When Spotify's Public API adds these data, I will update the code to use the API instead. Finally, do note that turning scraping will slow down fetching commands considerably as it takes time to load these dynamically-loaded information in a simulated browser.
+This project uses the [Spotify Web API](https://developer.spotify.com/documentation/web-api/) to access data about artists, albums, and tracks. All data is retrieved via Spotify's public API under its [Developer Terms of Service](https://developer.spotify.com/terms/).