#Load required libraries
import discord
import json
import os
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv

#Establish Spotify Web Endpoint
web_endpoint = "https://api.spotify.com"
auth_endpoint = "https://accounts.spotify.com/api/token"

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
tree = discord.app_commands.CommandTree(bot)

#Load and Request Token - Spotify Web API
async def req_token(auth_e, c_id, c_secret):
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
                    return token, response.status, None
                else:
                    r = await response.text()
                    print(f"API Endpoint Error. See Spotify API reference page for details.")
                    return 0, response.status, r
    except Exception as exc:
        print(f"Encountered Unexpected Error: {exc}")
    

#Report when Bot is Ready and Sync Slash Commands
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    if len(presaved_artist) > 0:
        print(f"Loaded {len(presaved_artist)} saved artists")
    else:
        print("No presaved elements loaded, this might be an error.")
    try:
        synced = await tree.sync()
        print(f"Bot has synced {len(synced)} command(s)")
    except Exception as exc:
        print(exc)
        
    
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
    
# Help Function
async def help(message, author):
    await message.reply("This is the help function.")
    
# Bot Latency Function
async def ping(message, author):
    ping = round(bot.latency * 1000, 2)
    await message.reply(f"Pong! Bot latency is currently `{ping} ms`")
    
    
    
def list_artists(author):
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
    return embed

# List Saved Artists
async def list(message, author, list_param, *args):
    if list_param == 'artists':
        r = list_artists(author)
        await message.reply(embed=r)
    else:
        await message.reply(f"The parameter of the list function `{list_param}` is invalid.")

@bot.event
async def on_message(message):
    #Store Variables
    author = message.author
    context = message.content.lower()
    #Ignore self messages
    if author.bot:
        return
    
    #Command Module
    if context.startswith("s!"):
        if len(context) < 3:
            await message.reply("Hello there. If you need help, run /help or s!help")
        else:
            command, params = identify_commands(context)
            try:
                cmd_func = globals().get(command)
                if cmd_func is not None and callable(cmd_func):
                    if params:
                        await cmd_func(message, author, *params)
                    else:
                        await cmd_func(message, author)
                else:
                    await message.reply(f"The command you entered '{command}' is invalid.")
            except AttributeError:
                await message.reply(f"The command you entered '{command}' is invalid.")


@tree.command(name="ping", description="test command")
async def slash_command(interaction: discord.Interaction):    
    await ping
    await interaction.response.send_message("Pong!")

# Run the bot using your bot token
bot.run(bot_token)
