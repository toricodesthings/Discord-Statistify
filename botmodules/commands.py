import discord, json, os, asyncio
from wrapper import datascraper as scraper
from wrapper import apiwrapper as spotifyapi
from botmodules import response_formatter as embedder
from urllib.parse import urlparse
from discord.ui import View, Select, Button

#================Bot Command Default Globals================
#Global settings for fetch command
SETTINGS = {
    "ml_scrape": False,
    "pertrack_scrape": False   
}

#Sync Global Settings for Bot
def sync_settings(new_settings):
    SETTINGS["ml_scrape"] = new_settings.get("monthly_listener_scraping", False)
    SETTINGS["pertrack_scrape"] = new_settings.get("per_track_playcount_scraping", False)
    
    return "Settings successfully synced in Commands' Module"

#================DISCORD UI Generation================
#Custom View Class for Dropdown
class CustomView(View):
    def __init__(self, *items):
        super().__init__(*items)
        self.msg = None

    def set_message(self, msg):
        self.msg = msg

#================DROPDOWN MENU================
#Saved Retrieval
#Generate Dropdown for Saved Pathway
async def generate_dropdown(author, call_type, saved_data, token, reply_func, data_type):
    data_type = data_type.rstrip("s")
    label_key = data_type
    url_key = f"{data_type}_url"
    
    selections = Select(
        placeholder=f"Select a {data_type}...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label=item[label_key], value=item[url_key])
            for item in saved_data
        ]
    )
    
    async def select_callback(interaction: discord.Interaction):
        selected_uri = selections.values[0]
        await interaction.response.defer()  # Acknowledge the interaction to prevent timeout
        selections.disabled = True
        view = View()
        view.add_item(selections)
        
        # Fetch function mapping based on data type
        fetch_function_mapping = {
            "artist": fetch_artists,
            "track": fetch_tracks,
            "playlist": fetch_playlists,
            "album": fetch_albums
        }
        
        fetch_function = fetch_function_mapping.get(data_type)
        
        if fetch_function == fetch_tracks:
            await fetch_function(call_type, selected_uri, author, token, interaction.followup.send, False, True)
        else:
            await fetch_function(call_type, selected_uri, author, token, interaction.followup.send, True)
        
    selections.callback = select_callback
    view = View()
    view.add_item(selections)

    # Send the dropdown menu to the user
    await reply_func(
        f"Please specify which saved {data_type} you want to retrieve:",
        view=view,
        ephemeral=True
    )
    
#Track Retrievals
#Track Selection Dropdown for Artist, Playlist and Album modules
async def generate_track_selection(author, call_type, track_items, token, reply_func):
    
    # Create a dropdown menu with track options
    selections = Select(
        placeholder="Select a track...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label=track_name, value=track_uri)
            for track_name, track_uri in track_items
        ]
    )

    # Handle track selection and fetch track information
    async def select_callback(interaction: discord.Interaction):
        selected_track_id = selections.values[0]
        await interaction.response.defer()
        selections.disabled = True
        view = View()
        view.add_item(selections)
        await fetch_tracks(call_type, extract_id(selected_track_id, "Track"), author, token, reply_func, True)
    
        
    selections.callback = select_callback
    view = View()
    view.add_item(selections)

    await reply_func(
        "Please select a track for more info:",
        view=view,
    )
#================DROPDOWN MENU================

#Generate Previous, Next, and Get Track Info Buttons for Get Function
async def generate_getmodules_buttons(author, call_type, allembeds, track_items, reply_func, token, 
                                      data_name, data_id, data_type):
    
    view = CustomView()

        
    async def track_info_click(call_type):
        await generate_track_selection(author, call_type, track_items, token, reply_func)
        await call_type.response.defer()
            
    async def save_button_click(call_type):
        statusmsg, saved = append_saved(author, data_id, data_name, data_type)
        
        if saved is True:
            save_button.disabled = True
            await update_embed(call_type)
            await reply_func(statusmsg)
            
            return

        await reply_func(statusmsg)
        await call_type.response.defer()

    get_track_info_button = Button(label="Get Track Info", style=discord.ButtonStyle.secondary)
    save_button = Button(label = "Save", style=discord.ButtonStyle.secondary)
    get_track_info_button.callback = track_info_click
    save_button.callback = save_button_click
        

    if len(allembeds) > 1:
        state = {"current_page": 0}  # Store current page state here
        
        async def prev_click(call_type):
            if state["current_page"] > 0:
                state["current_page"] -= 1
                await update_embed(call_type)

        async def next_click(call_type):
            if state["current_page"] < len(allembeds) - 1:
                state["current_page"] += 1
                await update_embed(call_type)
                
        async def update_embed(call_type):

            current_page = state["current_page"]  # Retrieve the current page from state
            prev_button.disabled = current_page == 0
            next_button.disabled = current_page == len(allembeds) - 1
            
            await view.msg.edit(embed=allembeds[current_page], view=view)
            await call_type.response.defer()

            
        prev_button = Button(label="⬅️ Previous", style=discord.ButtonStyle.primary)
        next_button = Button(label="Next ➡️", style=discord.ButtonStyle.primary)
        prev_button.callback = prev_click
        next_button.callback = next_click
        prev_button.disabled = True

        view.add_item(prev_button)
        view.add_item(get_track_info_button)
        view.add_item(save_button)
        view.add_item(next_button)
    else:
        async def update_embed(call_type):
            await view.msg.edit(embed=allembeds[0], view=view)
            await call_type.response.defer()

        view.add_item(get_track_info_button)
        view.add_item(save_button)

    return view

async def generate_settings_buttons(author, call_type, settingsdata):

    view = CustomView()

    # Callback factory for button interactions
    async def button_callback(call_type, setting_key: str):
        # Toggle the value
        current_value = settingsdata[setting_key]
        settingsdata[setting_key] = not current_value
        updated_embed = embedder.format_settings(author, settingsdata)

        # Update the JSON with the new setting
        modify_setting(settingsdata)
        sync_settings(settingsdata)

        # Update the button label and style
        for item in view.children:
            if item.custom_id == setting_key:
                item.label = f"{setting_key.replace('_', ' ').title()} ({'On' if not current_value else 'Off'})"
                item.style = discord.ButtonStyle.green if not current_value else discord.ButtonStyle.red

        # Update the message with the new button states
        await view.msg.edit(embed=updated_embed, view=view)
        await call_type.response.defer()

    # Add buttons dynamically based on the settings
    for setting, value in settingsdata.items():
        button = Button(
            label=f"{setting.replace('_', ' ').title()} ({'On' if value else 'Off'})",
            style=discord.ButtonStyle.green if value else discord.ButtonStyle.red,
            custom_id=setting  # Use the setting key as the button's custom ID
        )
        # Add callback with the current setting's key
        button.callback = lambda interaction, k=setting: button_callback(interaction, k)

        view.add_item(button)

    return view
    
#Generate list Next and Previous buttons if there's more than 6 elements:
async def generate_list_buttons(author, call_type, allembeds):
    
    view = CustomView()

    state = {"current_page": 0}
    msg: None

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
        await view.msg.edit(embed=allembeds[page], view=view)
        await call_type.response.defer()

    prev_button = Button(label="⬅️ Previous", style=discord.ButtonStyle.primary)
    next_button = Button(label="Next ➡️", style=discord.ButtonStyle.primary)
    prev_button.disabled = True
    prev_button.callback = prev_click
    next_button.callback = next_click

    view.add_item(prev_button)
    view.add_item(next_button)

    return view

    
#Generate Previous and Next Buttons for Get Command - Tracks Module
async def generate_tracks_get_buttons(author, call_type, allembeds, reply_func, data_name, data_id, data_type):
    
    view = CustomView()
    
    if not len(allembeds) > 1:
        return
    state = {"current_page": 0}
    msg: None
    
    async def save_button_click(call_type):
        statusmsg, saved = append_saved(author, data_id, data_name, data_type)
        
        if saved is True:
            save_button.disabled = True
            await update_embed(call_type)
            await reply_func(statusmsg)
            
            return

        await reply_func(statusmsg)
        await call_type.response.defer()

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
        await view.msg.edit(embed=allembeds[page], view=view)
        await call_type.response.defer()

    prev_button = Button(label="⬅️ Previous", style=discord.ButtonStyle.primary)
    next_button = Button(label="Next ➡️", style=discord.ButtonStyle.primary)
    prev_button.disabled = True
    prev_button.callback = prev_click
    next_button.callback = next_click
    
    save_button = Button(label = "Save", style=discord.ButtonStyle.secondary)
    save_button.callback = save_button_click
    
    view.add_item(prev_button)
    view.add_item(save_button)
    view.add_item(next_button)

    return view

async def generate_search_button(author, call_type, allembeds, reply_func, data_list, data_type):
    """
    Generates a paginated button interface with dynamic buttons for fetching info.

    Args:
    - author: The author of the message.
    - call_type: The type of call for response handling.
    - allembeds: The list of embeds to paginate.
    - reply_func: The function to handle replies (e.g., ctx.reply).
    - data_list: The list of items to generate buttons for.
    - data_type: The type of data (e.g., 'artist', 'album').
    - token: Authorization token for fetch functions.
    - fetch_function_mapping: A dictionary mapping data types to their fetch functions.

    Returns:
    - view: The generated view with buttons.
    """
    state = {"current_page": 0}

    async def prev_click(call_type):
        if state["current_page"] > 0:
            state["current_page"] -= 1
            await update_embed(call_type)

    async def next_click(call_type):
        if state["current_page"] < len(allembeds) - 1:
            state["current_page"] += 1
            await update_embed(call_type)

    async def save_button_click(call_type):
        # Clear the view and add item buttons
        view.clear_items()
        current_page = state["current_page"]
        start_index = current_page * 4
        end_index = start_index + 4
        current_items = data_list[start_index:end_index]

        for name, spotify_id in current_items:
            button = Button(label=name, style=discord.ButtonStyle.success)

            async def save_callback(call_type, name=name, spotify_id=spotify_id, current_button=button):
                statusmsg, saved = append_saved(author, spotify_id, name, data_type)
                
                if saved is True:
                    current_button.disabled = True
                    await update_embed(call_type)
                    await reply_func(statusmsg)
                    return

                await reply_func(statusmsg)
                current_button.disabled = True
                await update_embed(call_type)
                
            button.callback = save_callback
            view.add_item(button)

        # Update the view
        await call_type.response.edit_message(embed=allembeds[current_page], view=view)

    async def update_embed(call_type):
        prev_button.disabled = state["current_page"] == 0
        next_button.disabled = state["current_page"] == len(allembeds) - 1
        
        page = state["current_page"]
        await view.msg.edit(embed=allembeds[page], view=view)
        await call_type.response.defer()

    # Pagination buttons
    prev_button = Button(label="⬅️ Previous", style=discord.ButtonStyle.primary)
    next_button = Button(label="Next ➡️", style=discord.ButtonStyle.primary)
    save_button = Button(label="Save", style=discord.ButtonStyle.secondary)

    prev_button.disabled = True
    prev_button.callback = prev_click
    next_button.callback = next_click
    save_button.callback = save_button_click

    # Initial view setup
    view = CustomView()
    view.add_item(prev_button)
    view.add_item(save_button)
    view.add_item(next_button)

    return view
#================DISCORD UI Generation================

##===============NON ASYNC Functions================

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


#================JSON ACCESS & MODIFICATION================
#Loads presaved data from JSON
def load_ps_data(data_type):
    root_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(root_folder, 'saved_data', f'saved{data_type}.json')
    
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"saved{data_type}.json not found, make sure it's not deleted.")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding saved{data_type}.json. Check if the file is correctly formatted.")
        return {}


#Add new artists to database (user based)
def modify_ps_data(new_data, data_type):    
    root_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(root_folder, 'saved_data', f'saved{data_type}.json')
    
    try:
        with open(file_path, "w") as file:
            json.dump(new_data, file, indent=4)
        return new_data  # Return the saved data if successful
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error saving {data_type}: {e}")
        return []  # Return an empty list if any error
    
    
#Retrieve Saved Values from Database based on Selection (TO BE CHANGED TO SUPPORT ALL THREE)
def retrieve_saved_on_select(author, data_type, interaction_msg):
    author_id = str(author.id)
    
    try:
        user_index = int(interaction_msg)
        presaved_data = load_ps_data(data_type)
        user_saved_data = presaved_data.get(author_id, [])
        
        # Check if the user index is within range
        if 1 <= user_index <= len(user_saved_data):
            # Dynamically access the appropriate URL key based on data_type
            selected_item_uri = user_saved_data[user_index - 1][f"{data_type.rstrip("s")}_url"]
            return selected_item_uri, None
        
        else:
            return None, "Invalid input. Please enter a valid number from the list."
            
    except ValueError:
        return None, "Invalid input. Please enter a number."

    
# Add data to existing list for speific user 
def append_saved(author, data_id, data_name, data_type):
    author_id = str(author.id)
    presaved_data = load_ps_data(data_type)
 
    data_type_formatted = data_type.rstrip("s")
    # Construct the dynamic key based on data_type
    url_key = f"{data_type_formatted}_url"

    # Check if any item in presaved_data has the same URI
    if any(item.get(url_key) == data_id for item in presaved_data.get(author_id, [])):
        return f"You have already saved `{data_name}` in your {data_type} list", True


    def sanitize_json_string(value):
        if isinstance(value, str):
            return json.dumps(value)[1:-1]  # Removes extra quotes added by json.dumps
        return value

    # Only apply `sanitize_json_string` to `data_name`
    presaved_data.setdefault(author_id, []).append({
        f"{data_type_formatted}": sanitize_json_string(data_name),
        f"{data_type_formatted}_url": data_id 
    })

    
    # Attempt to save changes
    try:
        modify_ps_data(presaved_data, data_type)
        return f"Successfully saved the {data_type_formatted} `{data_name}`", False
    except Exception as e:
        return f"Save command encountered an exception: {str(e)}", False
    
#================JSON ACCESS & MODIFICATION================

#Extract ID from User Input
def extract_id(u_input, input_type):
    valid_lengths = {"Artist": 22, "Track": 22, "Album": 22, "Playlist": 22, "User": 28}
    
    # Check for standard Spotify ID based on type length
    if len(u_input) == valid_lengths[input_type] and u_input.isalnum():
        return u_input
    
    # Check for URI format
    if f"spotify:{input_type.lower()}:" in u_input:
        return u_input.split(":")[-1]
    
    # Check for URL format
    if "open.spotify.com" in u_input:
        try:
            return urlparse(u_input).path.split("/")[2]
        except IndexError:
            raise ValueError(f"Invalid Spotify {input_type} URL format")
    
    # Check for saved keyword (applicable to some types)
    if u_input == "saved" and input_type in {"Artist", "Track", "Album", "Playlist"}:
        return "use_saved"
    
    raise ValueError(f"The {input_type} parameter must be a valid Spotify {input_type} URI, URL, or ID")
        
#Fetch an easily readable and formattable list based on data_type
def fetch_saved_list(data_type):
    """
    Retrieves saved data for a specific data type.
    
    Parameters:
        data_type (str): The type of data to retrieve (e.g., 'artist', 'track', 'playlist', 'album).
        
    Returns:
        list: A list of saved items for the given data type.
    """
    presaved_data = load_ps_data(data_type)
    user_saved_data = []
    
    for _, items in presaved_data.items():
        user_saved_data.extend(items)
    
    return user_saved_data

        
# ------------------- BOT ASYNC FUNCTIONS ----------------------------

async def fetch_artists(call_type, artist_uri, author, token, reply_func, is_slash_withsaved=False):
    # Fetch artist information and top tracks
    data, response_code_a = await spotifyapi.request_artist_info(artist_uri, token)
    track_data, response_code_t = await spotifyapi.request_artist_toptracks(artist_uri, token)

    if data and response_code_a == 200:
        data_name, data_id, data_type = data["name"], data["uri"], "Artist"
                    
        if SETTINGS.get("ml_scrape"):  
            content = f"Selected {data_name}. "
            note = "Retrieval of Monthly Listener Data is `On`, response might take some time."
            
            if isinstance(call_type, discord.Interaction):
                if is_slash_withsaved:
                    await call_type.edit_original_response(content=content+note, view=None)
                else:
                    await reply_func(content=content+note)
            else:
                await reply_func(note)
        
            try:
                monthly_listener, msg = await scraper.scrape_monthly_listeners(artist_uri)
            except Exception as e:
                monthly_listener, msg = "N/A", None
                print(f"Encountered unexpected scraper error {e}")
        else:
            monthly_listener, msg = None, None
        
        allembeds = [embedder.format_get_artist(author, data, monthly_listener, msg)]
        
        if track_data and response_code_t == 200:
            track_embeds_list, tracks_list = await embedder.format_track_embed(author, track_data, token)
            allembeds.extend(track_embeds_list)
            track_fetch_failmsg = None
        else:
            track_fetch_failmsg = "Could you not fetch for track data, only artist data will be displayed"
        
        view = await generate_getmodules_buttons(author, call_type, allembeds, tracks_list, reply_func, token, 
                                                 data_name, extract_id(data_id, data_type), "artists")
        if SETTINGS["ml_scrape"]:
            if is_slash_withsaved:
                msg = await call_type.followup.send(content=track_fetch_failmsg, embed=allembeds[0], view=view)
                view.set_message(msg)
            else:
                if isinstance(call_type, discord.Interaction):
                    msg = await call_type.followup.send(embed=allembeds[0], view=view)
                else:
                    msg = await reply_func(embed=allembeds[0], view=view)
                view.set_message(msg)
        else:
            if is_slash_withsaved:
                if SETTINGS["ml_scrape"]:
                    content = f"Selected {data["name"]}. Retrieval of Monthly Listener Data is `On`, response might take some time."
                else: 
                    content = f"Selected {data["name"]}."
                await call_type.edit_original_response(content = content, view = None)
                msg = await call_type.followup.send(content = track_fetch_failmsg, embed = allembeds[0], view = view)
                view.set_message(msg)
            else:
                if is_slash_withsaved:
                    await call_type.edit_original_response(content = f"Selected {data["name"]}", view = None)
                    msg = await call_type.followup.send(content = track_fetch_failmsg, embed = allembeds[0], view = view)
                    view.set_message(msg)
                else:
                    if isinstance(call_type, discord.Interaction):
                        await reply_func(embed=allembeds[0], view = view)
                        msg = await call_type.original_response()
                        view.set_message(msg)
                    else:
                        msg = await reply_func(embed=allembeds[0], view = view)
                        view.set_message(msg)

        return  
        
    else:
        if response_code_a == 400 and response_code_t == 400:
            bot_msg = "Invalid artist URI." 
        elif response_code_a == 404:
            bot_msg = "Cannot find artist, check if you used an artist id"
        else:
            bot_msg = f"API Requests failed with status codes: {response_code_a} & {response_code_t}"
            
        if is_slash_withsaved:
            await call_type.edit_original_response(content = f"Selected {data["name"]}", view = None)
            await call_type.followup.send(content = bot_msg)

        else:
            await reply_func(bot_msg)
        
async def fetch_tracks(call_type, track_uri, author, token, reply_func, dropdown_pathway=False, is_slash_withsaved=False):
    data, response_code_t = await spotifyapi.request_track_info(track_uri, token)
    
    audio_data, response_code_taf = await spotifyapi.request_track_audiofeatures(track_uri, token)
    
    if data and response_code_t == 200:
        data_name, data_id, data_type = data["name"], data["uri"], "Track"
        
        if audio_data and response_code_taf == 200:
            
            if SETTINGS["pertrack_scrape"] and not dropdown_pathway:
                if is_slash_withsaved:
                    if SETTINGS["pertrack_scrape"]:
                        content = f"Selected {data_name}. Retrieval of Playcount Data is `On`, response might take some time."
                    else:
                        content = f"Selected {data_name}."
                    await call_type.edit_original_response(content=content, view=None)
                else:
                    if isinstance(call_type, discord.Interaction):
                        if SETTINGS["pertrack_scrape"]:
                            content = "Note: Retrieval of Playcount Data is `On`, response might take some time."
                            await reply_func(content=content)
                    else:
                        msg = await reply_func(embed=allembeds[0], view=view)
                        view.set_message(msg)
                
                try:
                    playcount, msg = await scraper.scrape_track_playcount(track_uri)
                except Exception as e:
                    playcount, msg = "N/A", None
                    print(f"Encountered unexpected scraper error {e}")
            else:
                playcount, msg = None, None
            
            allembeds = embedder.format_get_track(author, data, audio_data, playcount, msg)
            
            view = await generate_tracks_get_buttons(author, call_type, allembeds, reply_func,
                                                     data_name, extract_id(data_id, data_type), "tracks")
            
            if SETTINGS["pertrack_scrape"] and not dropdown_pathway:
                if is_slash_withsaved:
                    msg = await call_type.followup.send(embed=allembeds[0], view=view)
                    view.set_message(msg)
                else:
                    if isinstance(call_type, discord.Interaction):
                        await reply_func(embed=allembeds[0], view=view)
                        msg = await call_type.original_response()
                        view.set_message(msg)
                    else:
                        msg = await reply_func(embed=allembeds[0], view=view)
                        view.set_message(msg)
            else:
            
                if is_slash_withsaved:
                    await call_type.edit_original_response(content=f"Selected {data['name']}", view=None)
                    msg = await call_type.followup.send(embed=allembeds[0], view=view)
                    view.set_message(msg)
                else:
                    if not dropdown_pathway:
                        if isinstance(call_type, discord.Interaction):
                            await reply_func(embed=allembeds[0], view=view)
                            msg = await call_type.original_response()
                            view.set_message(msg)
                        else:
                            msg = await reply_func(embed=allembeds[0], view=view)
                            view.set_message(msg)
                    else:
                        msg = await call_type.original_response()
                        view.set_message(msg)
                        await msg.edit(embed=allembeds[0], view=view)
                        
            return
        
    # Error Handling 
    if response_code_t == 400 and response_code_taf == 400:
        bot_msg = "Invalid artist URI." 
    elif response_code_t == 404 and response_code_taf == 400:
        bot_msg = "Cannot find track, check if you used a track id"    
    else:
        bot_msg = f"API Requests failed with status codes: {response_code_t} & {response_code_taf}"
    await reply_func(bot_msg)
    
async def fetch_playlists(call_type, playlist_uri, author, token, reply_func, is_slash_withsaved=False):

    data, response_code = await spotifyapi.request_playlist_info(playlist_uri, token)
    
    if data and response_code == 200:
    
        data_name = data["name"]
        data_id = data["uri"]
        data_type = "Playlist"
        
        allembeds, track_lists = embedder.format_get_playlist(author, data)
        view = await generate_getmodules_buttons(author, call_type, allembeds, track_lists, reply_func, token,
                                                 data_name, extract_id(data_id, data_type), "playlists")
        
        if is_slash_withsaved:
            await call_type.edit_original_response(content = f"Selected {data["name"]}", view = None)
            msg = await call_type.followup.send(embed = allembeds[0], view = view)
            view.set_message(msg)
        else:
            if isinstance(call_type, discord.Interaction):
                await reply_func(embed=allembeds[0], view = view)
                msg = await call_type.original_response()
                view.set_message(msg)
            else:
                msg = await reply_func(embed=allembeds[0], view = view)
                view.set_message(msg)
        return  
    
    # Error Handling 
    if response_code == 400:
        bot_msg = "Invalid artist URI." 
    elif response_code == 404:
        bot_msg = "Cannot find playlist, check if you used a playlist id"    
    else:
        bot_msg = f"API Requests failed with status codes: {response_code}"
    await reply_func(bot_msg)
    
async def fetch_albums(call_type, album_uri, author, token, reply_func, is_slash_withsaved=False):
    data, response_code = await spotifyapi.request_album_info(album_uri, token)
    if data and response_code == 200:
        allembeds, track_lists = embedder.format_get_album(author, data)
        data_name = data.get("name", "Unknown Album")
        data_id = data["uri"]
        data_type = "Album"
        
        view = await generate_getmodules_buttons(author, call_type, allembeds, track_lists, reply_func, token,
                                                 data_name, extract_id(data_id, data_type), "albums")
        
        if is_slash_withsaved:
            await call_type.edit_original_response(content = f"Selected {data["name"]}", view = None)
            msg = await call_type.followup.send(embed = allembeds[0], view = view)
            view.set_message(msg)
        else:
            if isinstance(call_type, discord.Interaction):
                await reply_func(embed=allembeds[0], view = view)
                msg = await call_type.original_response()
                view.set_message(msg)
            else:
                msg = await reply_func(embed=allembeds[0], view = view)
                view.set_message(msg)
        return  
            
    # Error Handling 
    if response_code == 400:
        bot_msg = "Invalid artist URI." 
    elif response_code == 404:
        bot_msg = "Cannot find album, check if you used an album id"    
    else:
        bot_msg = f"API Requests failed with status codes: {response_code}"
    await reply_func(bot_msg)
    
async def fetch_users(call_type, user_uri, author, token, reply_func):
    data, response_code = await spotifyapi.request_user_info(user_uri, token)

    if data and response_code == 200:

        embed = embedder.format_get_user(author, data)
        await reply_func(embed=embed)

        return
        
    # Error Handling 
    if response_code == 400:
        bot_msg = "Invalid user URI." 
    elif response_code == 404:
        bot_msg = "Cannot find user, check if you used a user id"    
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
    embed.add_field(name="Main Commands:", value=f"""
=============================================================
**`List Artists`** lists all artists saved by user
Example: `s!list artists`
=============================================================
**`Get Artists`** retrieves artist info by `Spotify ID` or `Saved`
**`Get Tracks`** retrieves track info by `Spotify ID` or `Saved`
**`Get Playlists`** retrieves playlist info by `Spotify ID` or `Saved`
**`Get Albums`** retrieves album info by `Spotify ID` or `Saved`
**`Get Users`** retrieves user info by `Spotify ID` or `Saved`

By ID Example: `s!get artists [Spotify URL, URI or Direct ID]`
By Saved: `s!get artists saved` (Follow the prompt after)
=============================================================
**`Save Artists`** saves an artist by `Spotify ID`
**`Save Tracks`** saves an artist by `Spotify ID`
**`Save Playlists`** saves an artist by `Spotify ID`
**`Save Albums`** saves an artist by `Spotify ID`

Example: `s!save artists` [Spotify URL, URI or Direct ID]
=============================================================
**`Search Artists`** lists all artists saved by user
Example: `s!search artists Shep`
=============================================================

All of these commands has a Slash Command variant: `Type / and follow the prompt`
                    """, inline=False)
    embed.add_field(name="Misc Commands", value=f"""
\n
**`Ping`** pings the bot
**`Settings`** opens the bot settings menu
**`Help`** requests the help menu
                    """, inline=False)


    reply_func = get_reply_method(call_type)
    await reply_func(embed=embed)

# List Saved Artists
async def list(call_type, author, listtarget, *args):
    data_type = listtarget.lower().rstrip("s")
    reply_func = get_reply_method(call_type)
    
    saved_list = fetch_saved_list(listtarget)
    
    if_error = f"The parameter of the list function `{listtarget}` is invalid."
    
    # Check if saved_list is empty to confirm data_type validity
    if saved_list:
        listembeds = embedder.format_list(author, data_type, saved_list)
        if len(listembeds) > 1:
            view = generate_list_buttons(author, call_type, listembeds)
        else:
            view = None
        await reply_func(embed=listembeds[0], view = view)
    else:
        await reply_func(if_error)
    
    return

#Get Command        
async def get(call_type, author, bot, searchtarget, u_input, token, *args):
    reply_func = get_reply_method(call_type)
    
    #ALl Search Targets
    search_mappings = {
        "artists": ("Artist", fetch_artists),
        "tracks": ("Track", fetch_tracks),
        "playlists": ("Playlist", fetch_playlists),
        "albums": ("Album", fetch_albums),
        "users": ("User", fetch_users),
    }

    searchtarget = searchtarget.lower()
    
    if searchtarget in search_mappings:
        uri_type, fetch_function = search_mappings[searchtarget]
        
        try:
            # Attempt to extract the URI
            uri = extract_id(u_input, uri_type)
            
            # Special handling for saved data types that require "use_saved"
            if uri == "use_saved" and uri_type in {"Artist", "Track", "Album", "Playlist"}:
                uri = await get_saved_module(call_type, reply_func, author, bot, token, searchtarget)
                
                # Return immediately if using discord.Interaction
                if isinstance(call_type, discord.Interaction):
                    return
            
        except ValueError as value_error:
            await reply_func(value_error)
            return

        # Fetch with the determined function
        if fetch_function == fetch_tracks:
            await fetch_function(call_type, uri, author, token, reply_func, False)
        else:
            await fetch_function(call_type, uri, author, token, reply_func)
    else:
        await reply_func(f"The parameter of the get command `{searchtarget}` is invalid.")

async def get_saved_module(call_type, reply_func, author, bot, token, data_type):
    """
    Retrieves a saved item based on user interaction, generalized for multiple data types.
    
    Parameters:
        call_type (discord.Message or discord.Interaction): The type of call for interaction.
        reply_func (func): Function to send messages.
        author (object): The author object.
        bot (object): The bot instance.
        token (str): Authorization token.
        data_type (str): The type of data to retrieve (e.g., 'artist', 'track', 'playlist').
    """
    # Use the unified fetch function for retrieving saved data
    saved_data_list = fetch_saved_list(data_type)
    
    # Ensure format_list function exists for the specified data type
    if not saved_data_list:
        await reply_func(f"No saved {data_type.capitalize()} found.")
        return

    # For discord.Message interaction type
    if isinstance(call_type, discord.Message):
        list_embed = embedder.format_list(author, data_type.rstrip("s"), saved_data_list)
        await reply_func(
            f"Please specify (by number) which of the saved {data_type} you want to retrieve:",
            embed=list_embed[0]
        )
        
        # Await user input
        interaction_msg = await wait_for_user_input(call_type, author, bot)
        data_id, fail = retrieve_saved_on_select(author, data_type, interaction_msg)
        
        if fail:
            await reply_func(fail)
            return
        else:
            return data_id

    # For discord.Interaction type
    elif isinstance(call_type, discord.Interaction):
        await generate_dropdown(author, call_type, saved_data_list, token, reply_func, data_type)
        return

async def save(call_type, author, savetarget, u_input, token, *args):
    
    reply_func = get_reply_method(call_type)
    data_type = savetarget.lower()

    # Map each data type to its respective functions and error messages
    data_mappings = {
        "artists": ("Artist", spotifyapi.request_artist_info),
        "tracks": ("Track", spotifyapi.request_track_info),
        "playlists": ("Playlist", spotifyapi.request_playlist_info),
        "albums": ("Album", spotifyapi.request_album_info),
    }

    if data_type in data_mappings:
        uri_type, api_request_function = data_mappings[data_type]
        
        try:
            # Attempt to extract the URI
            data_id = extract_id(u_input, uri_type)
            
            # API Request to Fetch Data
            data, response_code = await api_request_function(data_id, token)
            
            if data and response_code == 200:
                data_name = data.get('name', f"Unknown {uri_type}")
                # Save data info
                statusmsg, saved = append_saved(author, data_id, data_name, data_type)
            else:
                # Handle invalid or failed API responses
                statusmsg = (
                    f"The {data_type} URI code you entered is invalid."
                    if response_code == 400
                    else f"Cannot save due to API request failure. Status code: {response_code}"
                )
                
            await reply_func(statusmsg)
        
        except ValueError as value_error:        
            await reply_func(value_error)
            
        return

    await reply_func(f"The parameter of the save command `{savetarget}` is invalid.")

def extract_items_for_buttons(data, data_type):

    items = data[data_type]["items"]
    
    match data_type:
        case "artists":
            return [(artist["name"], artist["id"]) for artist in items]
        case "albums":
            return [(album["name"], album["id"]) for album in items]
        case "playlists":
            return [(playlist["name"], playlist["id"]) for playlist in items]
        case "tracks":
            return [(track["name"], track["id"]) for track in items]
    
#TEMP
async def search_data(call_type, author, bot, searchinput, data_type, token, reply_func, *args):
    # Define a mapping of data types to Spotify API search types
    bot_msg = None
    
    search_types = {
        "artists": "artist",
        "albums": "album",
        "playlists": "playlist",
        "tracks": "track"
    }

    # Fetch data from Spotify API
    data, response_code = await spotifyapi.search_info(searchinput, search_types[data_type], token)

    if data and response_code == 200:
        # Format the data into embeds
        allembeds = embedder.format_search_data(author, searchinput, data, data_type)
        
        data_list = extract_items_for_buttons(data, data_type)
        
        view = await generate_search_button(author, call_type, allembeds, reply_func, data_list, data_type)
        
        # Send the first embed as a response
        if isinstance(call_type, discord.Interaction):
            await reply_func(embed=allembeds[0], view = view)
            msg = await call_type.original_response()
            view.set_message(msg)
        else:
            msg = await reply_func(embed=allembeds[0], view = view)
            view.set_message(msg)
        
        return
    
    else:
        bot_msg = f"API Requests failed with status codes: {response_code}"
    await reply_func(bot_msg)
    
async def search(call_type, author, bot, searchtarget, searchinput, token, *args):
    
    reply_func = get_reply_method(call_type)
    data_type = searchtarget.lower()
    
    possible_search = ["artists", "albums", "playlists", "tracks"]

    searchtarget = searchtarget.lower()
    
    if searchtarget in possible_search:
        await search_data(call_type, author, bot, searchinput, data_type, token, reply_func, *args)
        return
        
    await reply_func(f"The parameter of the save command `{searchtarget}` is invalid.")
    return
    
#==========SETTINGS JSON ACCESS============
def load_settings():
    root_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(root_folder, f'settings.json')
    try:
        with open(file_path, "r") as file:
            settings_from_file = json.load(file)
            return settings_from_file
        
    except FileNotFoundError:
        print(f"settings.json not found, using default settings values.")
        return None

def modify_setting(new_setting):
    root_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(root_folder, f'settings.json')
    
    try:
        with open(file_path, "w") as file:
            json.dump(new_setting, file, indent=4)
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error saving {e}")
    
async def settings(call_type, author, setting_accesstype, *args):
    reply_func = get_reply_method(call_type)
    access_type = ["set", "read"]
    
    if setting_accesstype.lower() in access_type:
        
        setting_accesstype = setting_accesstype.lower()
        if setting_accesstype == "set":
            settings_data = load_settings()
            settingembed = embedder.format_settings(author, settings_data)
            
            view = await generate_settings_buttons(author, call_type, settings_data)
            
            if isinstance(call_type, discord.Interaction):
                await reply_func(embed=settingembed, view = view)
                msg = await call_type.original_response()
                view.set_message(msg)
            else:
                msg = await reply_func(embed=settingembed, view = view)
                view.set_message(msg)
        elif setting_accesstype == "read":
            settings_data = load_settings()
            settingembed = embedder.format_settings(author, settings_data)
            await reply_func(embed=settingembed)
                
    else:
        await reply_func(f"The parameter of the settings command `{setting_accesstype}` is invalid.")
        
    return

#==========SETTINGS JSON ACCESS============