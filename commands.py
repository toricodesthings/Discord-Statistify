import discord, json, os, asyncio
import apiwrapper as spotifyapi
import response_formatter as embedder
from urllib.parse import urlparse
from discord.ui import View, Select, Button


# -------------------DISCORD UI Generation----------------------------

#Generate Dropdown when Calling
async def generate_artist_dropdown(author, call_type, saved_artists, token, reply_func):
    selections = Select(
        placeholder="Select an artist...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label=artist["artist"], value=artist["artist_url"])
            for artist in saved_artists
        ]
    )
    
    async def select_callback(interaction: discord.Interaction):
        artisturi = selections.values[0]
        selections.disabled = True
        view = View()
        view.add_item(selections)
        await fetch_artists(call_type, artisturi, author, token, reply_func, True)
        
    selections.callback = select_callback
    view = View()
    view.add_item(selections)

    # Send the dropdown menu to the user
    await reply_func(
        "Please specify which saved artist you want to retrieve:",
        view=view,
        ephemeral=True
    )
    
#Generate Previous and Next Buttons for Get Command - Artists Module
async def generate_artists_get_buttons(call_type, allembeds, reply_func, msg):
    
    if not len(allembeds) > 1:
        return
    state = {"current_page": 0}
    
    async def prev_click(call_type):
        if state["current_page"] > 0:
            state["current_page"] -= 1
            await update_embed(call_type)

    async def next_click(call_type):
        if state["current_page"] < len(allembeds) - 1:
            state["current_page"] += 1
            await update_embed(call_type)
    
    async def update_embed(call_type):
        prev_button.disabled = state["current_page"] == 0
        next_button.disabled = state["current_page"] == len(allembeds) - 1
        
        page = int(state["current_page"])
        await msg.edit(embed=allembeds[page], view=view)
        await call_type.response.defer()

    prev_button = Button(label="⬅️ Previous", style=discord.ButtonStyle.primary)
    next_button = Button(label="Next ➡️", style=discord.ButtonStyle.primary)
    prev_button.disabled = True
    prev_button.callback = prev_click
    next_button.callback = next_click
    view = View()
    view.add_item(prev_button)
    view.add_item(next_button)
            
    await msg.edit(embed=allembeds[0], view=view)
    
#Generate Previous and Next Buttons for Get Command - Tracks Module
async def generate_tracks_get_buttons(call_type, allembeds, reply_func, msg):
    
    if not len(allembeds) > 1:
        return
    state = {"current_page": 0}
    
    async def prev_click(call_type):
        if state["current_page"] > 0:
            state["current_page"] -= 1
            await update_embed(call_type)

    async def next_click(call_type):
        if state["current_page"] < len(allembeds) - 1:
            state["current_page"] += 1
            await update_embed(call_type)
    
    async def update_embed(call_type):
        prev_button.disabled = state["current_page"] == 0
        next_button.disabled = state["current_page"] == len(allembeds) - 1
        
        page = int(state["current_page"])
        await msg.edit(embed=allembeds[page], view=view)
        await call_type.response.defer()

    prev_button = Button(label="⬅️ Previous", style=discord.ButtonStyle.primary)
    next_button = Button(label="Next ➡️", style=discord.ButtonStyle.primary)
    prev_button.disabled = True
    prev_button.callback = prev_click
    next_button.callback = next_click
    view = View()
    view.add_item(prev_button)
    view.add_item(next_button)
            
    await msg.edit(embed=allembeds[0], view=view)
    
#Generate Previous and Next Buttons for Get Command - Tracks Module
async def generate_playlists_get_buttons(call_type, allembeds, reply_func, msg):
    
    if not len(allembeds) > 1:
        return
    state = {"current_page": 0}
    
    async def prev_click(call_type):
        if state["current_page"] > 0:
            state["current_page"] -= 1
            await update_embed(call_type)

    async def next_click(call_type):
        if state["current_page"] < len(allembeds) - 1:
            state["current_page"] += 1
            await update_embed(call_type)
    
    async def update_embed(call_type):
        prev_button.disabled = state["current_page"] == 0
        next_button.disabled = state["current_page"] == len(allembeds) - 1
        
        page = int(state["current_page"])
        await msg.edit(embed=allembeds[page], view=view)
        await call_type.response.defer()

    prev_button = Button(label="⬅️ Previous", style=discord.ButtonStyle.primary)
    next_button = Button(label="Next ➡️", style=discord.ButtonStyle.primary)
    prev_button.disabled = True
    prev_button.callback = prev_click
    next_button.callback = next_click
    view = View()
    view.add_item(prev_button)
    view.add_item(next_button)
            
    await msg.edit(embed=allembeds[0], view=view)
        
# ------------------- Non ASYNC FUNCTIONS ----------------------------

#Convert Message to Functions
def identify_commands(ctx):
    parts = ctx[2:].split()
    # Remove the "s!" from the command
    command = parts[0].lower()  
    
    # Split paramaters if multiple
    params = parts[1:] if len(parts) > 1 else []
    return command, params

#Reply based on interactiont type (slash or legacy)
def get_reply_method(call_type):
    if isinstance(call_type, discord.Message):
        return call_type.reply
    else:
        return call_type.response.send_message

#Loads presaved artists into database for usage in commands
def load_ps_artist():
    file_path = os.path.join(os.path.dirname(__file__), 'saved_data', 'savedartists.json')
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("savedartists.json not found, make sure it's not deleted.")
    except json.JSONDecodeError:
        return []

#Loads presaved tracks into database for usage in commands
def load_ps_track():
    file_path = os.path.join(os.path.dirname(__file__), 'saved_data', 'savedtracks.json')
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("savedtracks.json not found, make sure it's not deleted.")
    except json.JSONDecodeError:
        return []

#Loads presaved playlists into database for usage in commands
def load_ps_playlist():
    file_path = os.path.join(os.path.dirname(__file__), 'saved_data', 'savedplaylists.json')
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("savedplaylists.json not found, make sure it's not deleted.")
    except json.JSONDecodeError:
        return []

#Add new artists to database (user based)
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

#Retrieve Saved Values from Database (TO BE CHANGED TO SUPPORT ALL THREE)
def retrieve_saved(author, interaction_msg):
    try:
        user_index = int(interaction_msg)
        author = str(author.id)
        user_saved_artists = []
        presaved_artists = load_ps_artist()
        for author, artists in presaved_artists.items():
            user_saved_artists.extend(artists)
        
        if 1 <= user_index <= len(user_saved_artists):
            selected_artist_uri = user_saved_artists[user_index - 1]['artist_url']
            return selected_artist_uri, None

        else:
            fail = "Invalid input. Please enter a valid number from the list."
            return None, fail
            
    except ValueError:
        fail = "Invalid input. Please enter a number."
        return None, fail

# Add data to existing list for speific user 
def append_saved(author, artist_uri, artist_name):
    author = str(author.id)
    presaved_artists = load_ps_artist()
    
    for artist in presaved_artists.get(author, []):
        if artist["artist_url"] == artist_uri:
            status = f"You have already saved the artist `{artist_name}`"
            return status
    
    new_artist = {
        "artist": artist_name,
        "artist_url": artist_uri
    } 
    if author in presaved_artists:
        presaved_artists[author].append(new_artist)
    else:
        presaved_artists[author] = [new_artist]
    try:
        modify_ps_artist(presaved_artists)
        status = f"Succesfully saved artist `{artist_name}`"
    except Exception as e:
        status = f"Save command encountered an exception: {str(e)}"
    return status

#Extract ID

def extract_id(u_input, type):
    
    if type == "Artist":
        if len(u_input) == 22 and u_input.isalnum():
            return u_input
        elif "spotify:" in u_input and (type.lower() + ":") in u_input:
            return u_input.split(":")[-1]
        elif "open.spotify.com" in u_input:
            return urlparse(u_input).path.split("/")[2]
        elif u_input == "saved":
            return "use_saved"
        

    elif type == "Track":
        if len(u_input) == 22 and u_input.isalnum():
            return u_input
        elif "spotify:" in u_input and (type.lower() + ":") in u_input:
            return u_input.split(":")[-1]
        elif "open.spotify.com" in u_input:
            # Extract ID from URL
            return urlparse(u_input).path.split("/")[2]
        elif u_input == "saved":
            return "use_saved"
        
    elif type == "Playlist":
        if len(u_input) == 22 and u_input.isalnum():
            return u_input
        elif "spotify:" in u_input and (type.lower() + ":") in u_input:
            # Extract ID from URI
            return u_input.split(":")[-1]
        elif "open.spotify.com" in u_input:
            # Extract ID from URL
            return urlparse(u_input).path.split("/")[2]
        elif u_input == "saved":
            return "use_saved"

    raise ValueError(f"The artist parameter must be a valid Spotify {type} URI, URL, or ID")
        
# Retrieve a List of Presaved Artist Function
def retrieve_artists():
    presaved_artists = load_ps_artist()
    user_saved_artists = []
    for _, artists in presaved_artists.items():
        user_saved_artists.extend(artists)
    
    return user_saved_artists
        
# ------------------- BOT ASYNC FUNCTIONS ----------------------------

async def fetch_artists(call_type, artist_uri, author, token, reply_func, is_slash_withsaved):
    # Fetch artist information and top tracks
    data, response_code_a = await spotifyapi.request_artist_info(artist_uri, token)
    track_data, response_code_t = await spotifyapi.request_artist_toptracks(artist_uri, token)

    if data and response_code_a == 200:
        allembeds = [embedder.format_get_artist(author, data)]

        if track_data and response_code_t == 200:
            track_embeds_list = await embedder.format_track_embed(author, track_data, token)
            allembeds.extend(track_embeds_list)
            track_fetch_failmsg = None
        else:
            track_fetch_failmsg = "Could you not fetch for track data, only artist data will be displayed"

        if is_slash_withsaved:
            await call_type.edit_original_response(content = f"Selected {data["name"]}", view = None)
            msg = await call_type.followup.send(content = track_fetch_failmsg, embed = allembeds[0], ephemeral=False)
        else:
            if isinstance(call_type, discord.Interaction):
                await reply_func(content = track_fetch_failmsg, embed=allembeds[0], ephemeral=False)
                msg = await call_type.original_response()
            else:
                msg = await reply_func(embed=allembeds[0])

    
        await generate_artists_get_buttons(call_type, allembeds, reply_func, msg)
        return  
    
    else:
        if response_code_a == 400 and response_code_t == 400:
            bot_msg = "Invalid artist URI." 
        elif response_code_a == 404:
            bot_msg = "Cannot find artist, check if you used an artist id"
        else:
            bot_msg = f"API Requests failed with status codes: {response_code_a} & {response_code_t}"
            
        if is_slash_withsaved:
            await call_type.edit_original_response(content = "Fetching...", view = None)
            await call_type.followup.send(content = bot_msg, ephemeral = False)

        else:
            await reply_func(bot_msg)
        
async def fetch_track(call_type, track_uri, author, token, reply_func):
    data, response_code_t = await spotifyapi.request_track_info(track_uri, token)
    audio_data, response_code_taf = await spotifyapi.request_track_audiofeatures(track_uri, token)
    
    if data and response_code_t == 200:
        if audio_data and response_code_taf == 200:
            allembeds = embedder.format_get_track(author, data, audio_data)
            if isinstance(call_type, discord.Interaction):
                await reply_func(embed = allembeds[0], ephemeral=False)
                msg = await call_type.original_response()
            else:
                msg = await reply_func(embed=allembeds[0])
                
            await generate_tracks_get_buttons(call_type, allembeds, reply_func, msg)
    
            return
        
    # Error Handling 
    if response_code_t == 400 and response_code_taf == 400:
        bot_msg = "Invalid artist URI." 
    elif response_code_t == 404 and response_code_taf == 400:
        bot_msg = "Cannot find track, check if you used a track id"    
    else:
        bot_msg = f"API Requests failed with status codes: {response_code_t} & {response_code_taf}"
    await reply_func(bot_msg)
    
async def fetch_playlist(call_type, playlist_uri, author, token, reply_func):

    data, response_code = await spotifyapi.request_playlist_info(playlist_uri, token)
    
    if data and response_code == 200:
        allembeds = embedder.format_get_playlist(author, data)
        if isinstance(call_type, discord.Interaction):
            await reply_func(embed = allembeds[0], ephemeral=False)
            msg = await call_type.original_response()
        else:
            msg = await reply_func(embed=allembeds[0])
        
        
        if len(allembeds) > 1:   
            await generate_playlists_get_buttons(call_type, allembeds, reply_func, msg)

        return
        
    # Error Handling 
    if response_code == 400:
        bot_msg = "Invalid artist URI." 
    elif response_code == 404:
        bot_msg = "Cannot find playlist, check if you used a playlist id"    
    else:
        bot_msg = f"API Requests failed with status codes: {response_code}"
    await reply_func(bot_msg)

async def wait_for_user_input(call_type, author, bot):
    def check(m):
        return m.author == author and m.channel == call_type.channel
    try:
        interaction_msg = await bot.wait_for("message", timeout=7.5, check=check)
        return interaction_msg.content
    except asyncio.TimeoutError:
        reply_func = get_reply_method(call_type)
        await reply_func("Sorry, you took too long to respond. Please try again.")

# Bot Latency Function
async def ping(call_type, bot):
    ping = round(bot.latency * 1000, 2)
    bot_msg = f"Pong! Bot latency is currently `{ping} ms`"
    reply_func = get_reply_method(call_type)
    await reply_func(bot_msg)

# Help Function
async def help(call_type, author):
    embed = discord.Embed(
        title="Statistify Help Menu",  
        description=" V All available commands and parameters are listed below V",
        color=discord.Color.green() 
    )
    embed.add_field(name="Main Artist Commands:", value=f"""
=============================================================
**`List Artists`** lists all artists saved by user
Example: `s!list artists`
=============================================================
**`Get Artists`** retrieves artist info by `Spotify ID` or `Saved`
By ID Example: `s!get artists [Spotify URL, URI or Direct ID]`
By Saved: `s!get artists saved` (Follow the prompt after)
=============================================================
**`Save Artists`** saves an artist by `Spotify ID`
Example: `s!save artists` [Spotify URL, URI or Direct ID]
=============================================================
                    """, inline=False)
    embed.add_field(name="Misc Commands", value=f"""
\n
**`Ping`** pings the bot
**`Help`** requests the help menu
                    """, inline=False)


    reply_func = get_reply_method(call_type)
    await reply_func(embed=embed)

# List Saved Artists
async def list(call_type, author, listtarget, *args):
    saved_artists_list = retrieve_artists()
    listembed = embedder.format_list_artist(author, saved_artists_list)
    
    reply_func = get_reply_method(call_type)
    if_error = f"The parameter of the list function `{listtarget}` is invalid."
    if listtarget.lower() == 'artists':
        await reply_func(embed=listembed)
    else:
        await reply_func(if_error)

async def get_saved_module(call_type, reply_func, author, bot, token):
    if isinstance(call_type, discord.Message):
    
        saved_artists_list = retrieve_artists()
        listembed = embedder.format_list_artist(author, saved_artists_list)
        await reply_func("Please specify (by number) which saved element you want to retrieve:", embed=listembed)
        
        # Await for user input
        interaction_msg = await wait_for_user_input(call_type, author, bot)
        artisturi, fail = retrieve_saved(author, interaction_msg)
    
        if fail:
            await reply_func(fail)
            return
        else:
            return artisturi
    
    
    elif isinstance(call_type, discord.Interaction):
        saved_artists_list = retrieve_artists()
        await generate_artist_dropdown(author, call_type, saved_artists_list, token, reply_func)
        
        return

    

# Get Artist Info        
async def get(call_type, author, bot, searchtarget, u_input, token, *args):
    reply_func = get_reply_method(call_type)
    bot_msg = None

    if searchtarget.lower() == 'artists':
        try:
            artisturi = extract_id(u_input, "Artist")
            
            if artisturi == "use_saved":
                artisturi = await get_saved_module(call_type, reply_func, author, bot, token) 
                
                if isinstance(call_type, discord.Interaction):
                    return
            
        except ValueError as value_error:
            await reply_func(value_error)
            return

        await fetch_artists(call_type, artisturi, author, token, reply_func, False)
        return
    
    elif searchtarget.lower() == 'tracks':
        try:
            trackuri = extract_id(u_input, "Track")
            
        except ValueError as value_error:
            await reply_func(value_error)
            return
        
        await fetch_track(call_type, trackuri, author, token, reply_func)
        return
    
    elif searchtarget.lower() == "playlists":
        try:
            playlisturi = extract_id(u_input, "Playlist")
        except ValueError as value_error:
            await reply_func(value_error)
            return
        
        await fetch_playlist(call_type, playlisturi, author, token, reply_func)
        return
    
    else:
        await reply_func(f"The parameter of the get command `{searchtarget}` is invalid.")

# Temporary Save Artist (Will Update Later)
async def save(call_type, author, savetarget, u_input, token, *args):
    reply_func = get_reply_method(call_type)
    
    if savetarget.lower() == 'artists':
        try:
            artisturi = extract_id(u_input, "Artist")
            
            # API Request to Fetch Artist Data
            data, response_code = await spotifyapi.request_artist_info(artisturi, token)
            
            if data and response_code == 200:
                artistname = data.get('name', 'Unknown Artist')
                # Save artist info
                statusmsg = append_saved(author, artisturi, artistname)
            else:
                # Handle invalid or failed API responses
                statusmsg = (
                    "The artist URI code you entered is invalid."
                    if response_code == 400
                    else f"Cannot save due to API request failure. Status code: {response_code}"
                )
                
            await reply_func(statusmsg)
        
        except ValueError as value_error:        
            await reply_func(value_error)
            
        return
    await reply_func(f"The parameter of the save command `{savetarget}` is invalid.")
