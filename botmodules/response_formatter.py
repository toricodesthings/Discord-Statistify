import discord
from wrapper import apiwrapper as spotifyapi

#Misc Command - Change Track Duration from ms to s
def format_track_duration(ms):
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    return f"{minutes}:{seconds:02}"


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

#Create Embed for Artist (& And Artist Top tracks)
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
        track_url = track_info['external_urls']['spotify']
        artists = ", ".join(artist['name'] for artist in track_info['artists'])
        track_list.append(f"**{track_name}** by `{artists}` | [Link]({track_url})\n")

    embeds = []
    max_first_embed_tracks = 8  
    max_following_embed_tracks = 10  

    first_embed_tracks = track_list[:max_first_embed_tracks]
    track_field_value = "\n".join(first_embed_tracks)
    
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
    embed.add_field(name="Tracks", value=track_field_value, inline=False)

    avatar_url = author.avatar.url
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
    
    embeds.append(embed)

    # Add additional embeds only if there are more than 10 tracks
    remaining_tracks = track_list[max_first_embed_tracks:]
    page_number = 1
    if remaining_tracks:
        page_number += 1
        for i in range(0, len(remaining_tracks), max_following_embed_tracks):
            embed = discord.Embed(
                title=f"{playlist_name} (Continued)",
                description=f"Track List Page {page_number}",
                color=discord.Color.orange()
            )
            if playlist_image_url:
                embed.set_thumbnail(url=playlist_image_url)
            embed.add_field(name="Tracks List", value="\n".join(remaining_tracks[i:i + max_following_embed_tracks]), inline=False)
            embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
            embeds.append(embed)
            page_number += 1

    return embeds

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
    # Extracting album data from the response
    album_name = response.get("name", "Unknown Album")
    album_url = response["external_urls"]["spotify"]
    album_type = response.get("album_type", "Unknown").capitalize()
    total_tracks = response.get("total_tracks", 0)
    release_date = response.get("release_date", "Unknown Date")
    album_image_url = response["images"][0]["url"] if response["images"] else None
    artists = ", ".join([artist["name"] for artist in response["artists"]])
    genres = ", ".join(response.get("genres", [])) if response.get("genres") else "N/A"
    popularity = response.get("popularity", "Not available")
    
    # Formatting track list
    track_list = []
    track_list_for_dropdown = []
    for item in response["tracks"]["items"]:
        track_name = item["name"]
        track_url = item["external_urls"]["spotify"]
        track_uri = item["uri"]
        
        
        
        track_artists = ", ".join(artist["name"] for artist in item["artists"])

        # Format each track entry
        track_list.append(
            f"**{track_name}** by `{track_artists}` | [Link]({track_url})\n"
            f"*URI:* `{track_uri}`"
        )
        
        track_list_for_dropdown.append((track_name, track_uri))

    # Embed list initialization
    embeds = []
    max_first_embed_tracks = 4  # First embed track limit
    max_following_embed_tracks = 6  # Following embed track limit

    # Create the first embed with album information and up to 4 tracks
    first_embed_tracks = track_list[:max_first_embed_tracks]
    track_field_value = "\n\n".join(first_embed_tracks)

    # Create the main embed
    embed = discord.Embed(
        title=album_name,
        description=f"Album by [{artists}]({response['artists'][0]['external_urls']['spotify']})",
        color=discord.Color.purple()
    )

    embed.add_field(name="Spotify URL", value=album_url, inline=False)
    embed.add_field(name="Total Tracks", value=f"`{total_tracks}`", inline=True)
    embed.add_field(name="Release Date", value=f"`{release_date}`", inline=True)
    embed.add_field(name="Genres", value=f"`{genres}`", inline=True)
    embed.add_field(name="Popularity", value=f"`{popularity}/100`", inline=True)
    embed.add_field(name="Tracks List", value=track_field_value, inline=False)

    # Set album cover as the thumbnail
    if album_image_url:
        embed.set_thumbnail(url=album_image_url)

    # Footer with requestor's info
    avatar_url = author.avatar.url if author.avatar else None
    embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)

    # Add the first embed to the list of embeds
    embeds.append(embed)

    # Additional embeds for remaining tracks (if any), 6 tracks per page
    remaining_tracks = track_list[max_first_embed_tracks:]
    page_number = 1
    if remaining_tracks:
        page_number += 1
        for i in range(0, len(remaining_tracks), max_following_embed_tracks):
            # Create a new embed for each additional page of tracks
            embed = discord.Embed(
                title=f"{album_name} (Continued)",
                description=f"Track List Page {page_number}",
                color=discord.Color.purple()
            )
            if album_image_url:
                embed.set_thumbnail(url=album_image_url)
            embed.add_field(name="Tracks List", value="\n\n".join(remaining_tracks[i:i + max_following_embed_tracks]), inline=False)
            embed.set_footer(text=f"Requested by {author.display_name}", icon_url=avatar_url)
            
            embeds.append(embed)
            page_number += 1

    return embeds, track_list_for_dropdown