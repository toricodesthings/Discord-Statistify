import discord
from wrapper import apiwrapper as spotifyapi

#Misc Command - Change Track Duration from ms to s
def format_track_duration(ms):
    minutes, seconds = ms // 60000, (ms % 60000) // 1000
    return f"{minutes}:{seconds:02}"

def format_list(author, list_data_type, saved_list, chunk_size=6):
    """
    Format a list into a series of Discord embeds, paginated for readability.
    
    Args:
        author (discord.User): The author who request the list command
        list_data_type (str): The type of data being listed (e.g., "song", "video").
        saved_list (list[dict]): The list of saved items to be formatted.
        chunk_size (int): The number of items per embed page. Default is 6.
        
    Returns:
        list[discord.Embed]: A list of embeds formatted for Discord.
    """
    embeds = []
    avatar_url = author.avatar.url  # Cache avatar URL

    # Split the saved list into chunks for pagination
    for i, chunk in enumerate(
        (saved_list[j:j + chunk_size] for j in range(0, len(saved_list), chunk_size)), start=1
    ):
        embed = discord.Embed(
            title=f"Saved {list_data_type}s",
            description=(
                f"List of {author.display_name}'s presaved {list_data_type}s. "
                f"(Use the help command to learn how to save {list_data_type}s.)"
            ),
            color=discord.Color.green(),
        )

        # Add fields for each item in the current chunk
        for index, item in enumerate(chunk, start=(i - 1) * chunk_size + 1):
            embed.add_field(
                name=f"`{index}` - {item[list_data_type]}",
                value=f"{list_data_type.capitalize()} ID: `{item[f'{list_data_type}_url']}`",
                inline=False
            )

        # Add footer information
        embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
        embeds.append(embed)

    return embeds

#Create Embed for Artist (& And Artist Top tracks)
def format_get_artist(author, response, monthly_listener=None, errormsg=None):
    """
    Formats artist information into a Discord embed for display.

    Args:
        author (discord.User): The author whose requesting the artist information.
        response (dict): Artist information from the Spotify API.
        monthly_listener (int, optional): The artist's monthly listeners. Default is None.
        errormsg (str, optional): Error message for missing data. Default is None.

    Returns:
        discord.Embed: A formatted Discord embed with the artist's details.
    """
    artist_name = response['name']
    
    # Generate description with centered title and bars
    description = f"[Artist Information for {artist_name}]"
    side_bars = "=" * max((56 - len(description)) // 2, 0)
    description = f"{side_bars}{description}{side_bars}"

    # Create the embed
    embed = discord.Embed(
        title=artist_name,
        description=description,
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=response['images'][0]['url'])
    embed.add_field(name="Spotify URL", value=response['external_urls']['spotify'], inline=False)
    embed.add_field(name="Followers", value=f"`{int(response['followers']['total']):,}`", inline=True)
    
    if monthly_listener:
        embed.add_field(name="Monthly Listeners", value=f"`{int(monthly_listener):,}`", inline=True)
    
    embed.add_field(name="Popularity Index", value=f"`{response['popularity']}`", inline=True)

    # Add genres as a single field, separated by commas
    if response['genres']:
        genres = ", ".join(f"`{genre}`" for genre in response['genres'])
        embed.add_field(name="Genres", value=genres, inline=True)
    
    embed.add_field(name="Full Spotify URI", value=f"`{response['uri']}`", inline=False)

    # Include error message, if any
    if errormsg:
        embed.add_field(name="Notes", value=f"Could not retrieve monthly listener data due to an error:\n{errormsg}", inline=False)

    # Set footer with requestor's information
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=author.avatar.url)

    return embed

async def format_track_embed_helper_albums(album_id, token):
    """
    Helper function to retrieve album tracklist from Spotify API.

    Args:
        album_id (str): The ID of the album.
        token (str): Authorization token for Spotify API.

    Returns:
        tuple: Album tracks data and success flag.
    """
    album_tracks_data, response_code = await spotifyapi.request_album_tracklist(album_id, token)
    return (album_tracks_data, True) if album_tracks_data and response_code == 200 else (None, False)

async def format_track_embed(author, response, token):
    """
    Format track details into Discord embeds and track list.

    Args:
        author (discord.User): The user requesting the track details.
        response (dict): The response data containing track information.
        token (str): Authorization token for Spotify API.

    Returns:
        tuple: List of Discord embeds and list of tracks with their URIs.
    """
    embeds = []
    tracks_list = []
    author_avatar_url = author.avatar.url

    for track in response['tracks']:
        album = track['album']
        album_name = album['name']
        track_name = track['name']
        track_url = track['external_urls']['spotify']
        album_uri = album['uri']
        track_uri = track['uri']
        popularity = track.get('popularity', 'N/A')
        duration = format_track_duration(track['duration_ms'])
        artist_names = ", ".join(artist['name'] for artist in track['artists'])

        tracks_list.append((track_name, track_uri))

        # Determine the track list or fallback display
        if album['total_tracks'] > 1:
            album_tracks, response_succeed = await format_track_embed_helper_albums(album['id'], token)
            track_list = (
                "\n".join(f"{str(t['track_number']).rjust(2, '0')}. {t['name']}" for t in album_tracks['items'])
                if response_succeed and album_tracks
                else "Could not retrieve track list."
            )
        else:
            track_list = track_name if album_name != track_name else ""

        # Create and populate the embed
        embed = discord.Embed(
            title=f"{album_name} (Album)" if track_list else album_name,
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=album['images'][0]['url'])
        embed.add_field(name="Spotify URL", value=track_url, inline=False)
        embed.add_field(name="Artist(s)", value=f"`{artist_names}`", inline=False)
        if track_list:
            embed.add_field(name="Track List", value=track_list, inline=False)
        embed.add_field(name="Duration", value=f"`{duration}`", inline=True)
        embed.add_field(name="Popularity", value=f"`{popularity}/100`", inline=True)
        embed.add_field(name="Release Date", value=f"`{album['release_date']}`", inline=True)
        embed.add_field(name="Spotify Album URI", value=f"`{album_uri}`", inline=False)
        embed.add_field(name="Spotify Track URI", value=f"`{track_uri}`", inline=False)
        embed.set_footer(text=f"Requested by {author.display_name}", icon_url=author_avatar_url)

        embeds.append(embed)

    return embeds, tracks_list


def format_track_audiofeatures(author, response, audiofeatures_response, allembeds):
    """
    Formats the audio features of a track into a Discord embed.

    Args:
        author (discord.User): The user requesting the audio features.
        response (dict): The track information from the Spotify API.
        audiofeatures_response (dict): Audio features data from Spotify API.
        allembeds (list): A list to store the created embeds.

    Returns:
        list: Updated list of embeds.
    """
    album = response['album']
    album_name = album['name']
    album_type = album['album_type']
    track_name = response['name']

    # Calculate audio features (pre-rounding for efficiency)
    audio_features = {
        "Acousticness": round(audiofeatures_response['acousticness'] * 100, 2),
        "Danceability": round(audiofeatures_response['danceability'] * 100, 2),
        "Energy": round(audiofeatures_response['energy'] * 100, 2),
        "Instrumentalness": round(audiofeatures_response['instrumentalness'] * 100, 2),
        "Liveness": round(audiofeatures_response['liveness'] * 100, 2),
        "Speechiness": round(audiofeatures_response['speechiness'] * 100, 2),
        "Valence/Positivity": round(audiofeatures_response['valence'] * 100, 2),
    }
    loudness_level = round(audiofeatures_response['loudness'], 2)
    track_tempo = round(audiofeatures_response['tempo'])

    # Key signature and mode
    notation = ["C", "C#/Db", "D", "D#/Eb", "E/Fb", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]
    track_key = notation[audiofeatures_response['key']]
    track_mode = "Major" if audiofeatures_response['mode'] == 1 else "Minor"
    time_signature = audiofeatures_response['time_signature']

    # Generate notes
    notes = [
        "Track is likely an acoustic version" if audio_features["Acousticness"] > 50 else "Track is not an acoustic track",
        "Track is likely an instrumental/instrumental version" if audio_features["Instrumentalness"] > 50 else "Track is likely to have lyrics",
        "Track is likely played live" if audio_features["Liveness"] > 80 else "Track is likely recorded in a studio",
        "Track is likely pure spoken words" if audio_features["Speechiness"] > 66 else "Track includes musical content",
    ]

    # Create embed
    embed = discord.Embed(
        title=f"{track_name}'s Audio Analysis",
        description=f"From: {album_name} - `{album_type.capitalize()}`",
        color=discord.Color.pink()
    )
    embed.set_thumbnail(url=album['images'][0]['url'])
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=author.avatar.url)

    # Add primary details
    embed.add_field(name="Loudness Level", value=f"`{loudness_level} LUFS`", inline=True)
    embed.add_field(name="Track Tempo", value=f"`{track_tempo} BPM`", inline=True)
    embed.add_field(name="Time Signature", value=f"`{time_signature}/4`", inline=True)
    embed.add_field(name="Key Signature", value=f"`{track_key} {track_mode}`", inline=True)

    # Add separator
    separator = "=" * 35
    embed.add_field(name=separator, value="\u200b", inline=False)

    # Add audio feature fields
    for feature, value in audio_features.items():
        embed.add_field(name=feature, value=f"`{value}%`", inline=True)

    # Add notes
    embed.add_field(name="Notes", value="\n".join(notes), inline=False)

    # Add embed to the list
    allembeds.append(embed)

    return allembeds

def format_get_track(author, response, audiofeatures_response, playcount=None, errormsg=None):
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
    
    if playcount:
        embed.add_field(name="Playcount", value=f"`{playcount}`", inline=True)
    embed.add_field(name="Release Date", value=f"`{release_date}`", inline=True)
    embed.add_field(name="Spotify Track URI", value=f"`{track_uri}`", inline=False)
    if errormsg:
        embed.add_field(name="Notes:", value=f"Could not retrieve playcount data due to an error:\n{errormsg}", inline=False)    

    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
    
    allembeds = [embed]

    # Adding audio features
    allembeds = format_track_audiofeatures(author, response, audiofeatures_response, allembeds)
    
    return allembeds

def format_get_playlist(author, response):
    # Extracting playlist information
    playlist_name = response['name']
    playlist_image_url = response['images'][0]['url'] if response['images'] else None
    follower_count = response['followers']['total']
    is_collaborative = "Yes" if response['collaborative'] else "No"
    owner_name = response['owner']['display_name']
    owner_url = response['owner']['external_urls']['spotify']
    playlist_url = response['external_urls']['spotify']

    # Formatting tracks
    track_list = [
        f"**{item['track']['name']}** by `{', '.join(artist['name'] for artist in item['track']['artists'])}` | [Link]({item['track']['external_urls']['spotify']})\n"
        for item in response['tracks']['items']
    ]
    track_list_for_dropdown = [(item['track']['name'], item['track']['external_urls']['spotify']) for item in response['tracks']['items']]

    # Embed list initialization
    embeds = []
    max_first_embed_tracks = 8
    max_following_embed_tracks = 10

    # First embed with playlist information and initial tracks
    embed = discord.Embed(
        title=playlist_name,
        description=f"Playlist by [{owner_name}]({owner_url})\n",
        color=discord.Color.orange()
    )

    if playlist_image_url:
        embed.set_thumbnail(url=playlist_image_url)

    embed.add_field(name="Spotify URL", value=playlist_url, inline=False)
    embed.add_field(name="Followers", value=f"`{follower_count}`", inline=True)
    embed.add_field(name="Collaborative", value=f"`{is_collaborative}`", inline=True)
    embed.add_field(name="Tracks", value="\n".join(track_list[:max_first_embed_tracks]), inline=False)

    # Set footer with requester info
    avatar_url = author.avatar.url if author.avatar else None
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)

    # Append first embed to the list
    embeds.append(embed)

    # Additional embeds for remaining tracks (10 per page)
    for i in range(max_first_embed_tracks, len(track_list), max_following_embed_tracks):
        additional_embed = discord.Embed(
            title=f"{playlist_name} (Continued)",
            description=f"Track List Page {i // max_following_embed_tracks + 2}",
            color=discord.Color.orange()
        )
        additional_embed.add_field(
            name="Tracks List",
            value="\n".join(track_list[i:i + max_following_embed_tracks]),
            inline=False
        )

        if playlist_image_url:
            additional_embed.set_thumbnail(url=playlist_image_url)
        additional_embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)

        # Append each additional embed to the list
        embeds.append(additional_embed)

    return embeds, track_list_for_dropdown

def format_get_user(author, response):
    # Extracting user data from the response
    display_name = response.get("display_name", "Unknown User")
    profile_url = response["external_urls"]["spotify"]
    follower_count = response["followers"]["total"]
    user_id = response["id"]
    uri = response["uri"]
    profile_image_url = response["images"][0]["url"] if response["images"] else None

    # Create the Discord embed
    embed = discord.Embed(
        title=display_name,
        description=f"[Spotify Profile]({profile_url})",
        color=discord.Color.green()
    )

    if profile_image_url:
        embed.set_thumbnail(url=profile_image_url)

    # Add fields for detailed information
    embed.add_field(name="Followers", value=f"`{follower_count}`", inline=True)
    embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
    embed.add_field(name="Spotify URI", value=f"`{uri}`", inline=False)

    avatar_url = author.avatar.url if author.avatar else None
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)

    return embed

def format_get_album(author, response):
    # Extract album data
    album_name = response.get("name", "Unknown Album")
    album_url = response["external_urls"]["spotify"]
    total_tracks = response.get("total_tracks", 0)
    release_date = response.get("release_date", "Unknown Date")
    album_image_url = response["images"][0]["url"] if response["images"] else None
    artists = ", ".join(artist["name"] for artist in response["artists"])
    genres = ", ".join(response.get("genres", [])) if response.get("genres") else "N/A"
    popularity = response.get("popularity", "Not available")

    # Prepare track list entries
    track_list = [
        f"**{item['name']}** by `{', '.join(artist['name'] for artist in item['artists'])}` | [Link]({item['external_urls']['spotify']})"
        for item in response["tracks"]["items"]
    ]
    track_list_for_dropdown = [(item["name"], item["uri"]) for item in response["tracks"]["items"]]

    # Embed list initialization
    embeds = []
    max_first_embed_tracks = 4
    max_following_embed_tracks = 6

    # Create the first embed with album information and up to 4 tracks
    first_embed = discord.Embed(
        title=album_name,
        description=f"Album by [{artists}]({response['artists'][0]['external_urls']['spotify']})",
        color=discord.Color.purple()
    )
    first_embed.add_field(name="Spotify URL", value=album_url, inline=False)
    first_embed.add_field(name="Total Tracks", value=f"`{total_tracks}`", inline=True)
    first_embed.add_field(name="Release Date", value=f"`{release_date}`", inline=True)
    first_embed.add_field(name="Genres", value=f"`{genres}`", inline=True)
    first_embed.add_field(name="Popularity", value=f"`{popularity}/100`", inline=True)
    first_embed.add_field(name="Tracks List", value="\n\n".join(track_list[:max_first_embed_tracks]), inline=False)

    # Set album cover and footer
    if album_image_url:
        first_embed.set_thumbnail(url=album_image_url)
    avatar_url = author.avatar.url if author.avatar else None
    first_embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
    
    # Add the first embed to the list
    embeds.append(first_embed)

    # Create additional embeds for remaining tracks, with 6 tracks per embed
    for i in range(max_first_embed_tracks, len(track_list), max_following_embed_tracks):
        embed = discord.Embed(
            title=f"{album_name} (Continued)",
            description=f"Track List Page {(i - max_first_embed_tracks) // max_following_embed_tracks + 2}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Tracks List", value="\n\n".join(track_list[i:i + max_following_embed_tracks]), inline=False)
        if album_image_url:
            embed.set_thumbnail(url=album_image_url)
        embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
        
        # Add each additional embed to the list
        embeds.append(embed)

    return embeds, track_list_for_dropdown

def format_settings(author, data):
    embed = discord.Embed(
        title="Settings Overview",
        description="Here are the current settings:",
        color=discord.Color.blue()  # You can choose a different color
    )
    
    # Format key-value pairs and add to embed
    for key, value in data.items():
        # Convert boolean to a more user-friendly string
        value_str = "`Enabled`" if value else "`Disabled`"
        # Add each setting as a field in the embed
        embed.add_field(name=key.replace("_", " ").title(), value=value_str, inline=False)
    
    # Add a footer with author info
    avatar_url = author.avatar.url if author.avatar else None  # Handle cases where the user has no avatar
    embed.set_footer(
        text=f"Requested by {author.display_name}", 
        icon_url=avatar_url
    )
    
    return embed
    
def format_search_data(author, search_input, data, data_type):
    """
    Formats search results into Discord embeds for artists, albums, playlists, or tracks.

    Args:
        author (discord.User): The user requesting the search.
        search_input (str): The user's search input.
        data (dict): The search results returned from Spotify API.
        data_type (str): The type of data being searched (e.g., 'artists', 'albums', 'playlists', 'tracks').

    Returns:
        list[discord.Embed]: A list of embeds containing the search results.
    """
    embeds = []
    chunk_size = 4
    avatar_url = getattr(author.avatar, 'url', None)

    # Define data extraction and formatting functions for each data type
    def format_artist(artist):
        return {
            "name": f"__{artist['name']}__" if artist["name"].lower() == search_input.lower() else artist["name"],
            "value": (
                f"Followers: `{artist['followers']['total']}`\n"
                f"Popularity: `{artist['popularity']}`\n"
                f"Spotify ID: `{artist['id']}`\n"
                f"[Profile Link]({artist['external_urls']['spotify']})"
            ),
        }

    def format_album(album):
        artists = ", ".join(artist["name"] for artist in album["artists"])
        return {
            "name": f"{album['name']} ({album['album_type'].capitalize()})",
            "value": (
                f"**Artists:** {artists}\n"
                f"**Tracks:** `{album['total_tracks']}`\n"
                f"**Release Date:** `{album['release_date']}`\n"
                f"**Spotify ID:** `{album['id']}`\n"
                f"[Album Link]({album['external_urls']['spotify']})"
            ),
        }

    def format_playlist(playlist):
        return {
            "name": playlist["name"],
            "value": (
                f"**Collaborative:** `{playlist['collaborative']}`\n"
                f"**Created By:** `{playlist['owner']['display_name']}`\n"
                f"**Total Songs:** `{playlist['tracks']['total']}`\n"
                f"**Spotify ID:** `{playlist['id']}`\n"
                f"[Playlist Link]({playlist['external_urls']['spotify']})"
            ),
        }

    def format_track(track):
        artists = ", ".join(artist["name"] for artist in track["artists"])
        return {
            "name": f"{track['name']} by {artists}",
            "value": (
                f"**Popularity:** `{track['popularity']}`\n"
                f"**Spotify ID:** `{track['id']}`\n"
                f"[Track Link]({track['external_urls']['spotify']})"
            ),
        }

    # Mapping of data type to appropriate formatting function and data key
    data_type_mapping = {
        "artists": ("artists", "Artist Search Results", discord.Color.pink(), format_artist),
        "albums": ("items", "Album Search Results", discord.Color.purple(), format_album),
        "playlists": ("playlists", "Playlist Search Results", discord.Color.orange(), format_playlist),
        "tracks": ("tracks", "Track Search Results", discord.Color.green(), format_track),
    }

    data_key, title, color, formatter = data_type_mapping[data_type]
    items = data[data_key]["items"] if data_type == "artists" else data[data_key]
    pages = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

    for page_index, page in enumerate(pages, start=1):
        embed = discord.Embed(
            title=f"{title} - Page {page_index}",
            description=f"Results matching `{search_input}`:" if data_type != "albums" else "Here are the albums matching your search.",
            color=color,
        )
        for item in page:
            field = formatter(item)
            embed.add_field(name=field["name"], value=field["value"], inline=False)

        embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
        embeds.append(embed)

    return embeds
