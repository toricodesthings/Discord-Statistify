# discord-statistify

WIP Spotify Statistics Discord Bot utilizing Spotify Web API and Optional Web Scraping

This is a work-in-progress discord that connects with Spotify's Web API to retrieve data about artists, playlist, songs, and many more. Web API Access is built in and requires no premade libraries, however, users will need to create both a Discord Web Application and Spotify Web Application in their respective developer portals for the bot to function. See sections "Preparation" for more info and see section "Library Requirements" to install the required python libraries.

*This is my first big educational/personal project that integrates API retrieval, Web Scraping and Discord*

## Features
+ Custom API Wrapper to Fetch Data from Spotify's Public API
+ Ability to Save each Data on a per user basis
+ Ability to Search for specific Data within Discord
+ Display Metrics not available on Spotify Player like Audio Features
+ More to come...

## Preparation
Setting up the bot requires two keys, one from Discord Developer Portal, and one from Spotify Web API. Before that, clone this repo.

### Spotify Web API Setup
You'll need to set up a Spotify Developer account and obtain an API key. Follow these steps:

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Create a new app to get your **Client ID** and **Client Secret**. **Keep the Client Secret secure and never share it publicly**
3. Input those two keys into the .env file

### Discord Bot Setup
To use the Discord API, you’ll need to set up a bot and get a **Bot Token** from Discord. Follow these steps:

1. **Create a Discord Application**:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications).
   - Click on **New Application**, name your bot, and save.

2. **Set Up a Bot User**:
   - In your application’s settings, navigate to **Bot** on the left sidebar.
   - Click **Add Bot** to create a bot user for your application.

3. **Get Your Bot Token**:
   - Under the **Bot** settings, you’ll see a **Token** section.
   - Click **Copy** to retrieve your Bot Token. **Keep this token secure and never share it publicly**, as it grants control over your bot.
   - Input the token into the .env file

4. **Add Your Bot to a Server**:
   - In the OAuth2 settings, select **OAuth2 URL Generator**.
   - Under **OAuth2 Scopes**, check the **bot** scope.
   - Under **OAuth2 Bot Permissions**, select the permissions your bot needs (I recommend just ticking Administrator)
   - Copy the generated URL, paste it in your browser, and invite the bot to your server.

For more details, refer to [Discord’s Guide on Getting Started](https://discord.com/developers/docs/getting-started).

### Installing Dependencies

This project uses several dependencies that are listed in the `requirements.txt` file. To install them, make sure you have **Python 3** and **pip** installed, then follow these steps:

1. Open a terminal or command prompt in the project directory.
2. Run the following command to install all dependencies:

   ```bash
   pip install -r requirements.txt

### Run the Bot!

Open the bot.py directly or use the included .bat if on Windows.

## To-Dos:
+ ~~Track data fetch and audio analysis~~
+ ~~Make save command per user based~~
+ ~~Expand get command to playlist~~
+ ~~Expand get command to user~~
+ ~~Expand get command to albums~~
+ ~Add buttons to save in all get commands~
+ Search function for categories
+ ~Expand save command to tracks, artists, and playlists~
+ ~Add Web Scraping for Monthly Listener~
+ ~Add Web Scraping for Tracks~
+ Clean up & Add Proper Commenting

## Lib Links 
* https://pypi.org/project/aiohttp/
* https://pypi.org/project/discord.py/
* https://pypi.org/project/python-dotenv/
* https://pypi.org/project/playwright/

## A Few Final Notes
+ Bot has majority of functions built but is not yet noptimized and is missing some documentation for now.
+ Feel free to contribute any improvements or fork this repo
+ I will consider adding Spotify Audio Books data in the future, but it's not that relevant for me right now
+ A rebuild in JS of certain modules will happen to be used with my personal website
+ This bot will have the ability to scrape for the two public but relevant data using playwright, playcount and monthly listener. However, this is for educational purposes only and the setting is off by default (and only the Official Spotify API data will be used)! The scraper is also NOT resistant to website updates and might break but I will try to maintain it. When Spotify's Public API adds these data, I will update the code to use the API instead. Finally, do note that turning scraping On will slow down fetching commands considerably as it takes time to load these dynamically-loaded information in a simulated browser.

## Attribution
This project uses
+ [Spotify Web API](https://developer.spotify.com/documentation/web-api/) to access data about artists, albums, playlists, users and tracks. All data is retrieved via Spotify's public API under its [Developer Terms of Service](https://developer.spotify.com/terms/).
+ [Discord API](https://discord.com/developers/docs/intro) to access relevant data. These services are used under their respective [Developer Terms of Service](https://developer.spotify.com/terms/) and [Discord Developer Terms of Service](https://discord.com/developers/docs/policies-and-agreements).
+ This project includes web scraping techniques to collect data from public web pages on Spotify. The data collected is solely for **educational and non-commercial purposes** to demonstrate web scraping methodologies.

