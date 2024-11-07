import discord, json, os, asyncio
import apiwrapper as spotifyapi
from urllib.parse import urlparse
from discord.ui import View, Select, Button

# -------------------DISCORD UI Generation----------------------------
async def generate_artist_dropdown(author, call_type, saved_artists, token, reply_type):
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
        await fetch_artists(call_type, artisturi, author, token, reply_type, True)
        
    selections.callback = select_callback
    view = View()
    view.add_item(selections)

    # Send the dropdown menu to the user
    await reply_type(
        "Please specify which saved artist you want to retrieve:",
        view=view,
        ephemeral=True
    )
    
async def generate_artists_get_buttons(call_type, allembeds, reply_type, msg):
    
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
    
async def generate_tracks_get_buttons(call_type, allembeds, reply_type, msg):
    
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
    file_path = os.path.join(os.path.dirname(__file__), 'saved_data', 'savedartists.json')
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("savedartists.json not found, make sure it's not deleted.")
    except json.JSONDecodeError:
        return []

def format_track_duration(ms):
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    return f"{minutes}:{seconds:02}"

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

# Add artist to existing list for speific user
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

    raise ValueError("The artist parameter must be a valid Spotify Artist URI, URL, or ID")
        
def extract_track_id(u_input):
    if len(u_input) == 22 and u_input.isalnum():
        return u_input
    if "spotify:track:" in u_input:
        # Extract ID from URI
        return u_input.split(":")[-1]
    if "open.spotify.com" in u_input:
        # Extract ID from URL
        return urlparse(u_input).path.split("/")[2]

    raise ValueError("The track parameter must be a valid Spotify Track URI, URL, or ID")

def extra_playlist_id(u_input):
    if len(u_input) == 22 and u_input.isalnum():
        return u_input
    if "spotify:playlist:" in u_input:
        # Extract ID from URI
        return u_input.split(":")[-1]
    if "open.spotify.com" in u_input:
        # Extract ID from URL
        return urlparse(u_input).path.split("/")[2]

    raise ValueError("The track parameter must be a valid Spotify Playlist URI, URL, or ID")

# Retrieve a List of Presaved Artist Function
def retrieve_artists():
    presaved_artists = load_ps_artist()
    user_saved_artists = []
    for _, artists in presaved_artists.items():
        user_saved_artists.extend(artists)
    
    return user_saved_artists

def format_get_artist(author, response):
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
    avatar_url = author.avatar.url
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
    return embed

def format_list_artist(author, saved_artists_list):
    embed = discord.Embed(
        title="Saved Artists",
        description=f"List of {author.display_name}'s presaved artists (use help find out how to save artists)",
        color=discord.Color.green(),
    )
    avatar_url = author.avatar.url
    for index, a in enumerate(saved_artists_list):
        embed.add_field(name=f"`{index+1}` - {a["artist"]}", value=f"Artist ID: `{a["artist_url"]}`", inline=False)
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)

    return embed

def format_track_audiofeatures(author, response, audiofeatures_response, allembeds):
    album_name = response['album']['name']
    album_type = response['album']['album_type']
    track_name = response['name']
    
    #Audio Features
    acousticness = round(audiofeatures_response['acousticness'] * 100, 2)
    danceability = round(audiofeatures_response['danceability'] * 100, 2)
    energy = round(audiofeatures_response['energy'] * 100, 2)
    instrumentalness = round(audiofeatures_response['instrumentalness'] * 100, 2)
    liveness = round(audiofeatures_response['liveness'] * 100, 2)
    speechiness = round(audiofeatures_response['speechiness'] * 100, 2)
    valence_positiveness = round(audiofeatures_response['valence'] * 100, 2)
    loudness_level = round(audiofeatures_response['loudness'],2)
    track_tempo = round(audiofeatures_response['tempo'])
    
    notation = ["C", "C#/Db", "D", "D#/Eb", "E/Fb", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]
    track_key = notation[audiofeatures_response['key']]
    track_mode = ("Major" if audiofeatures_response['mode'] == 1
                  else "Minor")
    time_signature = audiofeatures_response['time_signature']

    
    notes = []
    
    if acousticness > 50:
        notes.append("Track is likely an acoustic version")
    else:
        notes.append("Track is not an acoustic track")
    if instrumentalness > 50:
        notes.append("Track is likely an instrumental/instrumental version")
    else:
        notes.append("Track is likely to have lyrics")
    if liveness > 80:
        notes.append("Track is likely played live")
    else:
        notes.append("Track is likely recorded in a studio")
    if speechiness > 66:
        notes.append("Track is likely pure spoken words")
    
    embed = discord.Embed(
        title=f"{track_name}'s Audio Analysis",  
        description=f"From: {album_name} - `{album_type.capitalize()}`",
        color=discord.Color.pink()
    )
    
    embed.add_field(name="Loudness Level", value=f"`{loudness_level} LUFS`", inline=True)
    embed.add_field(name="Track Tempo", value=f"`{track_tempo} BPM`", inline=True)
    embed.add_field(name="Time Signature", value=f"`{time_signature}/4`", inline=True)
    embed.add_field(name="Key Signature", value=f"`{track_key} {track_mode}`", inline=True)
    
    embed.add_field(name="---------------------------------------", value="", inline = False)
    
    embed.add_field(name="Acousticness", value=f"`{acousticness}%`", inline=True)
    embed.add_field(name="Danceability", value=f"`{danceability}%`", inline=True)
    embed.add_field(name="Energy", value=f"`{energy} %`", inline=True)
    embed.add_field(name="Instrumentalness", value=f"`{instrumentalness}%`", inline=True)
    embed.add_field(name="Liveness", value=f"`{liveness}%`", inline=True)
    embed.add_field(name="Speechiness", value=f"`{speechiness}%`", inline=True)
    embed.add_field(name="Valence/Positivivity", value=f"`{valence_positiveness}%`", inline=True)
    
    embed.add_field(name = "Notes", value = "\n".join(x for x in notes), inline = False)
    
    
    embed.set_thumbnail(url=response['album']['images'][0]['url'])
    avatar_url = author.avatar.url
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
    allembeds.append(embed)
    
    return allembeds

def format_get_track(author, response, audiofeatures_response):
    album_name = response['album']['name']
    album_type = response['album']['album_type']
    track_name = response['name']
    track_url = response['external_urls']['spotify']
    track_uri = response['uri']
    artist_names = ", ".join(artist['name'] for artist in response['artists'])
    release_date = response['album']['release_date']
    duration = format_track_duration(response['duration_ms'])
    popularity = response.get('popularity', 'N/A')

    # Embed creation with album and track details
    embed = discord.Embed(
        title=f"{track_name}",  
        description=f"From: **{album_name}** - `{album_type.capitalize()}`",
        color=discord.Color.blue()
    )

    # Setting album image as the embed image
    embed.set_thumbnail(url=response['album']['images'][0]['url'])
    
    # Setting author's avatar URL for footer
    avatar_url = author.avatar.url
    embed.add_field(name="Spotify URL", value=track_url, inline=False)
    embed.add_field(name="Artist(s)", value=f"`{artist_names}`", inline=False)
    embed.add_field(name="Duration", value=f"`{duration}`", inline=True)
    embed.add_field(name="Popularity", value=f"`{popularity}/100`", inline=True)
    embed.add_field(name="Release Date", value=f"`{release_date}`", inline=True)
    embed.add_field(name="Spotify Track URI", value=f"`{track_uri}`", inline=False)
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
    
    allembeds = [embed]

    # Adding audio features
    allembeds = format_track_audiofeatures(author, response, audiofeatures_response, allembeds)
    
    return allembeds

def format_get_playlist(author, response):

    playlist_name = response['name']
    playlist_image_url = response['images'][0]['url'] if response['images'] else None
    follower_count = response['followers']['total']
    is_collaborative = "Yes" if response['collaborative'] else "No"
    owner_name = response['owner']['display_name']
    owner_url = response['owner']['external_urls']['spotify']
    playlist_url = response['external_urls']['spotify']
    
    # Formatting tracks
    track_list = []
    for item in response['tracks']['items']:
        track_info = item['track']
        track_name = track_info['name']
        artists = ", ".join(artist['name'] for artist in track_info['artists'])
        track_list.append(f"**{track_name}** - `{artists}`\n")

    # Limiting track list display if too long
    max_tracks_display = 12  # Set max number of tracks to display in embed
    displayed_tracks = track_list[:max_tracks_display]
    track_field_value = "\n".join(displayed_tracks)
    
    if len(track_list) > max_tracks_display:
        track_field_value += f"\n...and {len(track_list) - max_tracks_display} more tracks"
        
    embed = discord.Embed(
        title=playlist_name,
        description=f"Playlist by [{owner_name}]({owner_url})",
        color=discord.Color.orange()
    )

    if playlist_image_url:
        embed.set_thumbnail(url=playlist_image_url)
        
    embed.add_field(name="Spotify URL", value=playlist_url, inline=False)
    embed.add_field(name="Followers", value=f"`{follower_count}`", inline=True)
    embed.add_field(name="Collaborative", value=f"`{is_collaborative}`", inline=True)

    embed.add_field(name="Tracks", value=track_field_value, inline=False)

    avatar_url = author.avatar.url
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)

    return [embed]
    
        
# ------------------- BOT ASYNC FUNCTIONS ----------------------------

async def format_track_embed_helper_albums(albumid, token):
    album_tracks_data, response_code = await spotifyapi.request_album_tracklist(albumid, token)
    if album_tracks_data and response_code == 200:
        return album_tracks_data, True
    else:
        return None, False
        
async def format_track_embed(author, response, token):
    embeds = []
    
    for track in response['tracks']:
        album = track['album']
        album_name = album['name']
        track_name = track['name']
        track_url = track['external_urls']['spotify']
        album_uri = album['uri']
        track_uri = track['uri']
        popularity = track.get('popularity', 'N/A')
        
        artist_names = ", ".join(artist['name'] for artist in track['artists'])

        # Ignore track name if it matches the album name
        display_track_name = "" if album_name == track_name else track_name

        # Format the track duration
        duration = format_track_duration(track['duration_ms'])
        
        # Check if the album contains multiple tracks
        if album['total_tracks'] > 1:

            album_tracks, response_succeed = await format_track_embed_helper_albums(album['id'], token)

            if album_tracks and response_succeed:
                tracks = []
                for t in album_tracks['items']:
                    padded_track_num = (str((t['track_number'])).rjust(2, "0"))
                    tracks.append(padded_track_num + ". " + t['name'])
                    
                track_list = "\n".join(tracks)
            else:
                track_list = "Could not retrieve track list."
        else:
            track_list = display_track_name

        embed = discord.Embed(
            title=(f"{album_name}" if track_list == display_track_name
                   else f"{album_name} (Album)"),
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url=album['images'][0]['url'])
        avatar_url = author.avatar.url

        # Add fields with inline alignment
        embed.add_field(name="Spotify URL", value=track_url, inline=False)
        embed.add_field(name="Artist(s)", value=f"`{artist_names}`", inline=False)
        if track_list:
            embed.add_field(name="Track List", value=track_list, inline=False) 
        embed.add_field(name="Duration", value=f"`{duration}`", inline=True)
        embed.add_field(name="Popularity", value=f"`{popularity}/100`", inline=True)
        embed.add_field(name="Release Date", value=f"`{album['release_date']}`", inline=True)
        embed.add_field(name="Spotify Album URI", value=f"`{album_uri}`", inline=False)
        embed.add_field(name="Spotify Track URI", value=f"`{track_uri}`", inline=False)
        embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
        embeds.append(embed)
    
    return embeds

async def fetch_artists(call_type, artist_uri, author, token, reply_type, is_slash_withsaved):
    # Fetch artist information and top tracks
    data, response_code_a = await spotifyapi.request_artist_info(artist_uri, token)
    track_data, response_code_t = await spotifyapi.request_artist_toptracks(artist_uri, token)

    if data and response_code_a == 200:
        allembeds = [format_get_artist(author, data)]

        if track_data and response_code_t == 200:
            track_embeds_list = await format_track_embed(author, track_data, token)
            allembeds.extend(track_embeds_list)
            track_fetch_failmsg = None
        else:
            track_fetch_failmsg = "Could you not fetch for track data, only artist data will be displayed"

        if is_slash_withsaved:
            await call_type.edit_original_response(content = "Fetching...", view = None)
            msg = await call_type.followup.send(content = track_fetch_failmsg, embed = allembeds[0], ephemeral=False)
        else:
            if isinstance(call_type, discord.Interaction):
                await reply_type(content = track_fetch_failmsg, embed=allembeds[0], ephemeral=False)
                msg = await call_type.original_response()
            else:
                msg = await reply_type(embed=allembeds[0])

    
        await generate_artists_get_buttons(call_type, allembeds, reply_type, msg)
        return  
    
    else:
        print("wait what")
        print(data, response_code_a)
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
            await reply_type(bot_msg)
        
async def fetch_track(call_type, track_uri, author, token, reply_type):
    data, response_code_t = await spotifyapi.request_track_info(track_uri, token)
    audio_data, response_code_taf = await spotifyapi.request_track_audiofeatures(track_uri, token)
    
    if data and response_code_t == 200:
        if audio_data and response_code_taf == 200:
            allembeds = format_get_track(author, data, audio_data)
            if isinstance(call_type, discord.Interaction):
                await reply_type(embed = allembeds[0], ephemeral=False)
                msg = await call_type.original_response()
            else:
                msg = await reply_type(embed=allembeds[0])
                
            await generate_tracks_get_buttons(call_type, allembeds, reply_type, msg)
    
            return
        
    # Error Handling 
    if response_code_t == 400 and response_code_taf == 400:
        bot_msg = "Invalid artist URI." 
    elif response_code_t == 404 and response_code_taf == 400:
        bot_msg = "Cannot find track, check if you used a track id"    
    else:
        bot_msg = f"API Requests failed with status codes: {response_code_t} & {response_code_taf}"
    await reply_type(bot_msg)
    
async def fetch_playlist(call_type, playlist_uri, author, token, reply_type):

    data, response_code = await spotifyapi.request_playlist_info(playlist_uri, token)
    
    if data and response_code == 200:
        allembeds = format_get_playlist(author, data)
        if isinstance(call_type, discord.Interaction):
            await reply_type(embed = allembeds[0], ephemeral=False)
            msg = await call_type.original_response()
        else:
            msg = await reply_type(embed=allembeds[0])
            
        #await generate_tracks_get_buttons(call_type, allembeds, reply_type, msg)

        return
        
    # Error Handling 
    if response_code == 400:
        bot_msg = "Invalid artist URI." 
    elif response_code == 404:
        bot_msg = "Cannot find playlist, check if you used a playlist id"    
    else:
        bot_msg = f"API Requests failed with status codes: {response_code}"
    await reply_type(bot_msg)

async def wait_for_user_input(call_type, author, bot):
    def check(m):
        return m.author == author and m.channel == call_type.channel
    try:

        interaction_msg = await bot.wait_for("message", timeout=10.0, check=check)
        return interaction_msg.content
    except asyncio.TimeoutError:
        reply_type = get_reply_method(call_type)
        await reply_type("Sorry, you took too long to respond. Please try again.")

# Bot Latency Function
async def ping(call_type, bot):
    ping = round(bot.latency * 1000, 2)
    bot_msg = f"Pong! Bot latency is currently `{ping} ms`"
    reply_type = get_reply_method(call_type)
    await reply_type(bot_msg)

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


    reply_type = get_reply_method(call_type)
    await reply_type(embed=embed)

# List Saved Artists
async def list(call_type, author, listtarget, *args):
    saved_artists_list = retrieve_artists()
    listembed = format_list_artist(author, saved_artists_list)
    
    reply_type = get_reply_method(call_type)
    if_error = f"The parameter of the list function `{listtarget}` is invalid."
    if listtarget.lower() == 'artists':
        await reply_type(embed=listembed)
    else:
        await reply_type(if_error)

async def get_saved_module(call_type, reply_type, author, bot, token):
    if isinstance(call_type, discord.Message):
    
        saved_artists_list = retrieve_artists()
        listembed = format_list_artist(author, saved_artists_list)
        
        await reply_type("Please specify (by number) which saved element you want to retrieve:", embed=listembed)
        
        # Await for user input
        interaction_msg = await wait_for_user_input(call_type, author, bot)
        artisturi, fail = retrieve_saved(author, interaction_msg)
        
        if fail:
            await reply_type(fail)
            return
        return artisturi
    
    
    elif isinstance(call_type, discord.Interaction):
        saved_artists_list = retrieve_artists()
        await generate_artist_dropdown(author, call_type, saved_artists_list, token, reply_type)

    

# Get Artist Info        
async def get(call_type, author, bot, searchtarget, u_input, token, *args):
    reply_type = get_reply_method(call_type)
    bot_msg = None

    if searchtarget.lower() == 'artists':
        try:
            artisturi = extract_artist_id(u_input)
            
            if artisturi == "use_saved":
                artisturi = await get_saved_module(call_type, reply_type, author, bot, token)
                return
            
        except ValueError as value_error:
            await reply_type(value_error)
            return

        await fetch_artists(call_type, artisturi, author, token, reply_type, False)
        return
    
    elif searchtarget.lower() == 'tracks':
        try:
            trackuri = extract_track_id(u_input)
            
        except ValueError as value_error:
            await reply_type(value_error)
            return
        
        await fetch_track(call_type, trackuri, author, token, reply_type)
        return
    
    elif searchtarget.lower() == "playlists":
        try:
            playlisturi = extra_playlist_id(u_input)
        except ValueError as value_error:
            await reply_type(value_error)
            return
        
        await fetch_playlist(call_type, playlisturi, author, token, reply_type)
        return
    
    else:
        await reply_type(f"The parameter of the get command `{searchtarget}` is invalid.")

# Temporary Save Artist (Will Update Later)
async def save(call_type, author, savetarget, u_input, token, *args):
    reply_type = get_reply_method(call_type)
    
    if savetarget.lower() == 'artists':
        try:
            artisturi = extract_artist_id(u_input)
            
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
                
            await reply_type(statusmsg)
        
        except ValueError as value_error:        
            await reply_type(value_error)
            
        return
    await reply_type(f"The parameter of the save command `{savetarget}` is invalid.")
