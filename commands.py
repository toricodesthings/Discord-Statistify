import discord, json, os, aiohttp
from urllib.parse import urlparse

web_endpoint = "https://api.spotify.com"

# ------------------- Non ASYNC FUNCTIONS ----------------------------

def identify_commands(ctx):
    parts = ctx[2:].split()
    # Remove the "s!" from the command
    command = parts[0].lower()  
    
    # Split paramaters if multiple
    params = parts[1:] if len(parts) > 1 else []
    return command, params

def get_reply_method(call_type):
    if isinstance(call_type, discord.Message):
        return call_type.reply
    else:
        return call_type.response.send_message

# Loads presaved artist into databse for usage in commands
def load_ps_artist():
    file_path = os.path.join(os.path.dirname(__file__), 'savedartists.json')
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("savedartists.json not found, make sure it's not deleted.")    
        
def extract_artist_id(u_input):
    if len(u_input) == 22 and u_input.isalnum():
        return u_input
    if "spotify:artist:" in u_input:
        # Extract ID from URI
        return u_input.split(":")[-1]
    if "open.spotify.com" in u_input:
        # Extract ID from URL
        return urlparse(u_input).path.split("/")[2]

    raise ValueError("The artist parameter must be a valid Spotify URI, URL, or Artist ID")
        
# List Presaved Artist Function
def list_artists(author, bot):
    presaved_artists = load_ps_artist()
    embed = discord.Embed(
        title="Saved Artists",
        description="List of presaved artists (use help find out how to save artists)",
        color=discord.Color.green(),
    )
    avatar_url = author.avatar.url
    embed.set_footer(text=f"Requested by {author}", icon_url=avatar_url)
    for a in presaved_artists:
        embed.add_field(name=f"{a["artist"]}", value=f"Url: `{a["artist_url"]}`", inline=False)
    return embed

def format_get_artist(response):
    # Create an embed object
    embed = discord.Embed(
        title=response['name'],  
        description=f"{"═" * len(response['name'])}[Artist Information for {response['name']}]{"═" * len(response['name'])}",
        color=discord.Color.green() 
    )
    embed.set_thumbnail(url=response['images'][0]['url'])
    embed.add_field(name="Spotify URL", value=f"{response['external_urls']['spotify']}", inline=False)
    embed.add_field(name="Followers", value=f"`{str(response['followers']['total'])}`", inline=True)
    embed.add_field(name="Popularity Index", value=f"`{str(response['popularity'])}`", inline=True)
    if response['genres']:
        embed.add_field(name="Genres", value=f"`{'\n'.join(response['genres'])}`", inline=True)
    embed.add_field(name="Full Spotify URI", value=f"`{response['uri']}`", inline=False)

    return embed
# ------------------- BOT ASYNC FUNCTIONS ----------------------------

# Bot Latency Function
async def ping(call_type, bot):
    ping = round(bot.latency * 1000, 2)
    bot_msg = f"Pong! Bot latency is currently `{ping} ms`"
    reply_type = get_reply_method(call_type)
    await reply_type(bot_msg)

# Help Function
async def help(call_type, author):
    bot_msg = "This is the help function."
    reply_type = get_reply_method(call_type)
    await reply_type(bot_msg)

# List Saved Artists
async def list(call_type, author, bot, listtarget, *args):
    listembed = list_artists(author, bot)
    reply_type = get_reply_method(call_type)
    if_error = f"The parameter of the list function `{listtarget}` is invalid."
    if listtarget.lower() == 'artists':
        await reply_type(embed=listembed)
    else:
        await reply_type(if_error)

# Get Artist Info        
async def get(call_type, author, searchtarget, u_input, token, *args):
    global web_endpoint
    reply_type = get_reply_method(call_type)
    if searchtarget.lower() == 'artists':
        try: 
            artisturi = extract_artist_id(u_input)
            url = f"{web_endpoint}/v1/artists/{artisturi}"
            headers = {
                "Authorization": f"Bearer {token}"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        embedget = format_get_artist(data)
                    elif response.status == 400:
                        bot_msg = f"The artist URI code you entered is invalid"
                    else:
                        bot_msg = f"API Request failed with status code {response.status}"
        except ValueError:
            bot_msg = str(ValueError)
            pass

        if embedget:
            await reply_type(embed=embedget)
            
        else:
            await reply_type(bot_msg)
            
    else:
        await reply_type(f"The parameter of the info command `{searchtarget}` is invalid.")