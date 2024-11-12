import discord
from wrapper import apiwrapper as spotifyapi

#Misc Command - Change Track Duration from ms to s
def format_track_duration(ms):
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    return f"{minutes}:{seconds:02}"

def format_list(author, list_data_type, saved_list):
    embed = discord.Embed(
        title=f"Saved {list_data_type}s",
        description=f"List of {author.display_name}'s presaved {list_data_type} (use help find out how to save {list_data_type})",
        color=discord.Color.green(),
    )
    avatar_url = author.avatar.url
    for index, a in enumerate(saved_list):
        embed.add_field(
            name=f"`{index+1}` - {a[list_data_type]}",
            value=f"{list_data_type.capitalize()} ID: `{a[f'{list_data_type}_url']}`",
            inline=False
        )

    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)

    return embed

#Create Embed for Artist (& And Artist Top tracks)
def format_get_artist(author, response):

    artist_name = response['name']
    description = f"[Artist Information for {artist_name}]"
    remaining_space = 56 - len(description)
    
    if remaining_space > 0:
        side_bars = "=" * (remaining_space // 2)
        description = f"{side_bars}{description}{side_bars}"
    
    embed = discord.Embed(
        title=artist_name,
        description=description,
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=response['images'][0]['url'])
    embed.add_field(name="Spotify URL", value=response['external_urls']['spotify'], inline=False)
    embed.add_field(name="Followers", value=f"`{response['followers']['total']}`", inline=True)
    embed.add_field(name="Popularity Index", value=f"`{response['popularity']}`", inline=True)

    # Only add genres if they exist
    if response['genres']:
        embed.add_field(name="Genres", value="`\n".join(response['genres']) + "`", inline=True)

    embed.add_field(name="Full Spotify URI", value=f"`{response['uri']}`", inline=False)

    # Direct footer assignment
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=author.avatar.url)

    return embed

async def format_track_embed_helper_albums(albumid, token):
    album_tracks_data, response_code = await spotifyapi.request_album_tracklist(albumid, token)
    if album_tracks_data and response_code == 200:
        return album_tracks_data, True
    else:
        return None, False
        
async def format_track_embed(author, response, token):
    embeds = []
    tracks_list = []
    author_avatar_url = author.avatar.url 

    for track in response['tracks']:
        album = track['album']
        
        #Retrieve essential track and album details
        album_name = album['name']
        track_name = track['name']
        track_url = track['external_urls']['spotify']
        album_uri = album['uri']
        track_uri = track['uri']
        popularity = track.get('popularity', 'N/A')
        
        tracks_list.append((track_name, track_uri))
        artist_names = ", ".join(artist['name'] for artist in track['artists'])

        # Conditionally display track name only if it differs from album name
        display_track_name = "" if album_name == track_name else track_name

        # Format track duration once
        duration = format_track_duration(track['duration_ms'])

        # Retrieve album tracks if applicable
        if album['total_tracks'] > 1:
            album_tracks, response_succeed = await format_track_embed_helper_albums(album['id'], token)
            
            if response_succeed and album_tracks:
                # Generate padded track listing only if album tracks were successfully retrieved
                track_list = "\n".join(f"{str(t['track_number']).rjust(2, '0')}. {t['name']}" for t in album_tracks['items'])
            else:
                track_list = "Could not retrieve track list."
        else:
            track_list = display_track_name

        # Initialize embed with title and color
        embed = discord.Embed(
            title=f"{album_name} (Album)" if track_list != display_track_name else album_name,
            color=discord.Color.blue()
        )

        # Set thumbnail and add fields directly
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

        # Set footer once, using pre-accessed avatar URL
        embed.set_footer(text=f"Requested by {author.display_name}", icon_url=author_avatar_url)
        
        embeds.append(embed)

    return embeds, tracks_list

def format_track_audiofeatures(author, response, audiofeatures_response, allembeds):
    album = response['album']  # Access album details once
    album_name = album['name']
    album_type = album['album_type']
    track_name = response['name']
    
    # Audio Features - Calculated once with rounding
    acousticness = round(audiofeatures_response['acousticness'] * 100, 2)
    danceability = round(audiofeatures_response['danceability'] * 100, 2)
    energy = round(audiofeatures_response['energy'] * 100, 2)
    instrumentalness = round(audiofeatures_response['instrumentalness'] * 100, 2)
    liveness = round(audiofeatures_response['liveness'] * 100, 2)
    speechiness = round(audiofeatures_response['speechiness'] * 100, 2)
    valence_positiveness = round(audiofeatures_response['valence'] * 100, 2)
    loudness_level = round(audiofeatures_response['loudness'], 2)
    track_tempo = round(audiofeatures_response['tempo'])

    # Key signature and mode
    notation = ["C", "C#/Db", "D", "D#/Eb", "E/Fb", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]
    track_key = notation[audiofeatures_response['key']]
    track_mode = "Major" if audiofeatures_response['mode'] == 1 else "Minor"
    time_signature = audiofeatures_response['time_signature']

    # Generate notes based on thresholds
    notes = [
        "Track is likely an acoustic version" if acousticness > 50 else "Track is not an acoustic track",
        "Track is likely an instrumental/instrumental version" if instrumentalness > 50 else "Track is likely to have lyrics",
        "Track is likely played live" if liveness > 80 else "Track is likely recorded in a studio",
        "Track is likely pure spoken words" if speechiness > 66 else "Track includes musical content",
    ]

    # Embed creation
    embed = discord.Embed(
        title=f"{track_name}'s Audio Analysis",
        description=f"From: {album_name} - `{album_type.capitalize()}`",
        color=discord.Color.pink()
    )

    embed.add_field(name="Loudness Level", value=f"`{loudness_level} LUFS`", inline=True)
    embed.add_field(name="Track Tempo", value=f"`{track_tempo} BPM`", inline=True)
    embed.add_field(name="Time Signature", value=f"`{time_signature}/4`", inline=True)
    embed.add_field(name="Key Signature", value=f"`{track_key} {track_mode}`", inline=True)

    separator = "=" * 35  
    embed.add_field(name=separator, value="\u200b", inline=False)  

    audio_features = {
        "Acousticness": acousticness,
        "Danceability": danceability,
        "Energy": energy,
        "Instrumentalness": instrumentalness,
        "Liveness": liveness,
        "Speechiness": speechiness,
        "Valence/Positivity": valence_positiveness,
    }
    for feature, value in audio_features.items():
        embed.add_field(name=feature, value=f"`{value}%`", inline=True)

    # Adding notes
    embed.add_field(name="Notes", value="\n".join(notes), inline=False)

    # Thumbnail and footer
    embed.set_thumbnail(url=album['images'][0]['url'])
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=author.avatar.url)

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
