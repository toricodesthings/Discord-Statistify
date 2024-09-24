import discord
from dotenv import load_dotenv
import json
import asyncio
import os
import aiohttp
#Establish Spotify Web Endpoint
web_endpoint = "https://api.spotify.com"
authentication_endpoint = "https://accounts.spotify.com/api/token"

#Load Presaved Artist into database
presaved_artist = []
file_path = os.path.join(os.path.dirname(__file__), 'savedartists.json')
with open(file_path, "r") as f:
    presaved_artist.append(json.load(f))


#Load Token and Set Bot Parameters - Discord Application
load_dotenv()
bot_token = os.getenv("DISCORD_TOKEN")
spotify_cid = os.getenv("CLIENT_ID")
spotify_csecret = os.getenv("CLIENT_SECRET")
bot = discord.Client(intents=discord.Intents.all())

#Load and Request Token - Spotify Web API
async def req_token(c_id, c_secret, auth_e):
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
        async with aiohttp.ClientSession() as s:
            async with s.post(auth_e, headers = headers, data = data) as response:
                if response.status == 200:
                    token = response.json()['access_token']
                else:
                    print(f"API Endpoint returned code: {response.status}")
    except Exception as exc:
        print(f"Encountered Unexpected Error: {exc}")
        
            
    return token
            
token = req_token(spotify_cid, spotify_csecret, authentication_endpoint)


#Report when Bot is Ready and Sync Slash Commands
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    if len(presaved_artist) > 0:
        print(f"Loaded {len(presaved_artist)} saved artists")
    else:
        print("No presaved elements loaded, this might be an error.")
    try:
        synced = await bot.tree.sync()
        print(f"Bot has synced {len(synced)} command(s)")
    except Exception as exc:
        print(exc)

def identify_commands(message):
    parts = message[2:].split()
    command = parts[0]  # Remove the "!" from the command
    if len(parts) > 1:
        params = parts[1:]  # The rest are parameters
        return command, params
    else:
        return command
    
# Help Function
async def help(message, author):
    await message.reply("This is the help function.")
    
# Bot Latency Function
async def ping(message, author):
    ping = bot.latency
    await message.reply(f"Pong! Bot latency is currently {ping} ms")
    
# List Saved Artists
async def list_artists(message, author):
    global presaved_artist
    embed = discord.Embed(
        title="Saved Artists",
        description="List of presaved artists (use help find out how to save artists)",
        color=discord.Color.green(),
        
    )
    
    embed.set_footer(text=f"Called by {author}")
    artist_list = ""
    for x in presaved_artist:
        artist_list += f"{x}\n"
    embed.add_field(name="Artists", value=artist_list, inline=False)
    await message.reply(embed)

@bot.event
async def on_message(message):
    #Store Variables
    author = message.author
    #Ignore self messages
    if author.bot:
        return
    
    #Command Module
    if message.startswith("!"):
        if len(message) < 2:
            print("Hello there. If you need help, run /help or s!help")
        else:
            command, params = identify_commands(message)
            try:
                if params: 
                    getattr(globals(), command)(author, *params)
                else:
                    getattr(globals(), command)(author)
            except AttributeError:
               await message.reply(f"The command you entered '{command}' is invalid.")

# Run the bot using your bot token
bot.run(bot_token)
