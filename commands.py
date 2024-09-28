import discord, json, os

web_endpoint = "https://api.spotify.com"

# ------------------- Non ASYNC FUNCTIONS ----------------------------

# Loads presaved artist into databse for usage in commands
def load_ps_artist():
    file_path = os.path.join(os.path.dirname(__file__), 'savedartists.json')
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("savedartists.json not found, make sure it's not deleted.")    
        
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

# ------------------- BOT ASYNC FUNCTIONS ----------------------------

# Bot Latency Function
async def ping(call_type, bot):
    ping = round(bot.latency * 1000, 2)
    bot_msg = f"Pong! Bot latency is currently `{ping} ms`"
    if isinstance(call_type, discord.Message):
        await call_type.reply(bot_msg)
    else:
        await call_type.response.send_message(bot_msg)

# Help Function
async def help(call_type, author):
    if isinstance(call_type, discord.Message):
        await call_type.reply("This is the help function.")
    else:
        await call_type.response.send_message(f"This is the help function.")

# List Saved Artists
async def list(call_type, author, bot, listtarget, *args):
    er = list_artists(author, bot)
    if listtarget == 'artists':
        if isinstance(call_type, discord.Message):
            await call_type.reply(embed=er)
        else:
            await call_type.response.send_message(embed=er)
            
    else:
        await call_type.reply(f"The parameter of the list function `{listtarget}` is invalid.")
        
async def search(call_type, author, bot, url, token, *args):
    return
        