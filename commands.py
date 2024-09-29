import discord, json, os, asyncio
from urllib.parse import urlparse
import apiwrapper as spotifyapi




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

#Loads presaved artist into databse for usage in commands
def load_ps_artist():
    file_path = os.path.join(os.path.dirname(__file__), 'savedartists.json')
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("savedartists.json not found, make sure it's not deleted.")
    except json.JSONDecodeError:
        return []

def modify_ps_artist(new_artist):    
    file_path = os.path.join(os.path.dirname(__file__), 'savedartists.json')
    try:
        with open(file_path, "w") as file:
            json.dump(new_artist, file, indent=4)
    except FileNotFoundError:
        print("savedartists.json not found, make sure it's not deleted.")
        return []
    except json.JSONDecodeError:
        return []
        
def retrieve_saved(interaction_msg):
    try:
        user_index = int(interaction_msg)
        presaved_artists = load_ps_artist()
        if 1 <= user_index < len(presaved_artists) + 1:
            selected_artist_uri = presaved_artists[user_index - 1]['artist_url']
            return selected_artist_uri, None
        else:
            fail = "Invalid input. Please enter a valid number from the list."
            return None, fail
            
    except ValueError:
        fail = "Invalid input. Please enter a number."
        return None, fail

def append_saved(artist_uri, artist_name):
    presaved_artists = load_ps_artist()
    
    for artist in presaved_artists:
        if artist["artist_url"] == artist_uri:
            status = f"Artist `{artist_name}` has already been saved."
            return status
    
    new_artist = {
        "artist": artist_name,
        "artist_url": artist_uri
    } 
    presaved_artists.append(new_artist)
    try:
        modify_ps_artist(presaved_artists)
        status = f"Succesfully saved artist `{artist_name}`"
    except Exception as e:
        status = f"Save command encountered an exception: {str(e)}"
    return status
        
        
def extract_artist_id(u_input):
    if len(u_input) == 22 and u_input.isalnum():
        return u_input
    if "spotify:artist:" in u_input:
        # Extract ID from URI
        return u_input.split(":")[-1]
    if "open.spotify.com" in u_input:
        # Extract ID from URL
        return urlparse(u_input).path.split("/")[2]
    if u_input == "saved":
        return "use_saved"

    raise ValueError("The artist parameter must be a valid Spotify URI, URL, or Artist ID")
        
# List Presaved Artist Function
def list_artists(author):
    presaved_artists = load_ps_artist()
    embed = discord.Embed(
        title="Saved Artists",
        description="List of presaved artists (use help find out how to save artists)",
        color=discord.Color.green(),
    )
    avatar_url = author.avatar.url
    embed.set_footer(text=f"Requested by {author}", icon_url=avatar_url)
    for index, a in enumerate(presaved_artists):
        embed.add_field(name=f"`{index+1}` - {a["artist"]}", value=f"Artist ID: `{a["artist_url"]}`", inline=False)
    return embed

def format_get_artist(response):
    # Create an embed object
    artist_name = response['name']
    remaining_space = 56 - len(artist_name) - len("[Artist Information for ]")

    if remaining_space > 0:
        # Divide the remaining space equally on both sides
        side_bars = "=" * (remaining_space // 2)
        # Create the description string
        description = f"{side_bars}[Artist Information for {artist_name}]{side_bars}"
    else:
        # If the artist name is longer than the URL, just use the artist name
        description = f"[Artist Information for {artist_name}]"
        
    embed = discord.Embed(
        title=response['name'],  
        description=description,
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

async def wait_for_user_input(call_type, author, bot, user_prompt):
    reply_type = get_reply_method(call_type)
    await reply_type(user_prompt)
    def check(m):
        return m.author == author and m.channel == call_type.channel
    try:

        interaction_msg = await bot.wait_for("message", timeout=10.0, check=check)
        return interaction_msg.content
    except asyncio.TimeoutError:
        await reply_type("Sorry, you took too long to respond. Please try again.")
        
        

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
async def list(call_type, author, listtarget, *args):
    listembed = list_artists(author)
    reply_type = get_reply_method(call_type)
    if_error = f"The parameter of the list function `{listtarget}` is invalid."
    if listtarget.lower() == 'artists':
        await reply_type(embed=listembed)
    else:
        await reply_type(if_error)

# Get Artist Info        
async def get(call_type, author, bot, searchtarget, u_input, token, *args):
    reply_type = get_reply_method(call_type)
    bot_msg = None

    if searchtarget.lower() == 'artists':
        try:
            artisturi = extract_artist_id(u_input)
            
            if artisturi == "use_saved" and isinstance(call_type, discord.Message):
                listembed = list_artists(author)
                await reply_type(embed=listembed)
                
                # Await for user input
                interaction_msg = await wait_for_user_input(call_type, author, bot, 
                                                            "Please specify (by number) which saved artist you want to retrieve:")
                artisturi, fail = retrieve_saved(interaction_msg)
                if fail:
                    await reply_type(fail)
                    return
        
        except ValueError as value_error:
            await reply_type(value_error)
            return

        # API Request to Fetch Artist Data
        data, response_code = await spotifyapi.request_artist_info(artisturi, token)
        
        if data and response_code == 200:
            embedget = format_get_artist(data)
            await reply_type(embed=embedget)
        else:
            bot_msg = "Invalid artist URI." if response_code == 400 else f"API Request failed with status code {response_code}"
            await reply_type(bot_msg)
        return

    await reply_type(f"The parameter of the info command `{searchtarget}` is invalid.")

# Temporary Save Artist (Will Update Later)
async def save(call_type, author, bot, savetarget, u_input, token, *args):
    reply_type = get_reply_method(call_type)
    
    if savetarget.lower() == 'artists':
        try:
            artisturi = extract_artist_id(u_input)
            
            # API Request to Fetch Artist Data
            data, response_code = await spotifyapi.request_artist_info(artisturi, token)
            
            if data and response_code == 200:
                artistname = data.get('name', 'Unknown Artist')
                # Save artist info
                statusmsg = append_saved(artisturi, artistname)
            else:
                # Handle invalid or failed API responses
                statusmsg = (
                    "The artist URI code you entered is invalid."
                    if response_code == 400
                    else f"Cannot save due to API request failure. Status code: {response_code}"
                )
                
            await reply_type(statusmsg)
        
        except ValueError as value_error:        
            await reply_type(value_error)
            
        return
    await reply_type(f"The parameter of the save command `{savetarget}` is invalid.")
