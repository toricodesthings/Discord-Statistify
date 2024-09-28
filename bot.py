#Load required libraries
import discord
import json
import os
import aiohttp
import time
from datetime import datetime
import commands as b_commands
from discord.ext import commands
from dotenv import load_dotenv

#Load Presaved Artist into database
def load_ps_artist():
    
    file_path = os.path.join(os.path.dirname(__file__), 'savedartists.json')
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("savedartists.json not found, make sure it's not deleted.")
        

#Establish Spotify Web Endpoint
web_endpoint = "https://api.spotify.com"
auth_endpoint = "https://accounts.spotify.com/api/token"

def load_token():
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return None
    
def store_token(token, expires_at):
    file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
    token_data = {
        'access_token': token,
        'expires_at': expires_at
    }
    with open(file_path, 'w') as file:
        json.dump(token_data, file)
    

#Load and Request Token - Spotify Web API
async def req_token(auth_e, c_id, c_secret):
    
    print("Checking to see if previous token is expired...")
    saved_token = load_token()
    if saved_token and saved_token["access_token"] is not None:
        current_time = int(time.time())
        if current_time < (saved_token['expires_at'] - 10) and not saved_token['expires_at'] is None:
            token = saved_token["access_token"]
            expiry_time = datetime.fromtimestamp(saved_token['expires_at']).strftime('%d-%m-%y %H:%M:%S')
            print(f"Using previously generated token: {token}\nThis token will expire at {expiry_time}")
            return token, 1, None
    else:
        print("No token previously generated. Proceed to generation...")
        
    #Set Parameters
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': c_id,
        'client_secret': c_secret
    }
    try: 
        print(f"Requesting token from {auth_e}...")
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_e, headers = headers, data = data) as response:
                if response.status == 200:
                    r = await response.json()
                    token = r['access_token']
                    expiry = current_time + r['expires_in']
                    store_token(token, expiry)
                    return token, response.status, None
                else:
                    error = await response.text()
                    print(f"API Endpoint Error. See Spotify API reference page for details.")
                    return 0, response.status, error
    except Exception as exc:
        print(f"Encountered Unexpected Error: {exc}")
#-------------------------------------------------------------------------------------------------



#Load Token and Set Bot Parameters - Discord Application
load_dotenv()
bot_token = os.getenv("DISCORD_TOKEN")
spotify_cid = os.getenv("CLIENT_ID")
spotify_csecret = os.getenv("CLIENT_SECRET") 
bot = discord.Client(intents=discord.Intents.all())
tree = discord.app_commands.CommandTree(bot)

#Report when Bot is Ready and Sync Slash Commands
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord Successfully!")
    presaved_artist = load_token()
    if len(presaved_artist) > 0:
        print(f"Loaded {len(presaved_artist)} saved artists")
    else:
        print("No presaved elements loaded, this might be an error.")
    
    # Sync Slash Commands
    try:
        synced = await tree.sync()
        print(f"Bot has synced {len(synced)} command(s)")
    except Exception as exc:
        print(exc)
        
    # Start Token Request
    token, code, response = await req_token(auth_endpoint, spotify_cid, spotify_csecret)
    if not token == 0:
        print(f"Spotify API access granted with token: {token}")
    else:
        print(f"Spotify API access error with code: {code}")
        print(response)

def identify_commands(ctx):
    parts = ctx[2:].split()
    command = parts[0]  # Remove the "!" from the command
    if len(parts) > 1:
        params = parts[1:]  # The rest are parameters
        return command, params
    else:
        return command, False



@bot.event
async def on_message(message):
    #Store Variables
    author = message.author
    ctx = message.content.lower()
    #Ignore self messages
    if author.bot:
        return
    
    #Command Module
    if ctx.startswith("s!"):
        if len(ctx) < 3:
            await message.reply("Hello there. If you need help, run /help or s!help")
        else:
            command, params = identify_commands(ctx)
            try:
                cmd_func = globals().get(command) or getattr(__import__('b_commands'), command, None)
                if cmd_func is not None and callable(cmd_func):
                    if params:
                        await cmd_func(message, author, bot, *params)
                    else:
                        await cmd_func(message, author, bot)
                else:
                    await message.reply(f"The command you entered '{command}' is invalid.")
            except AttributeError:
                await message.reply(f"The command you entered '{command}' is invalid.")


@tree.command(name="ping", description="test command")
async def slash_command(interaction: discord.Interaction):    
    author = interaction.user
    await b_commands.ping(interaction, author, bot)

# Run the bot using your bot token
bot.run(bot_token)
