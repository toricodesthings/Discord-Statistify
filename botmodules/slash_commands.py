import discord
from botmodules import commands as b_commands  
from discord.ui import Select, View

access_token = ""

async def setup_slash_commands(token, bot):
    tree = discord.app_commands.CommandTree(bot)
    global access_token
    access_token = token

    # Use unique function names for each command
    @tree.command(name="ping", description="Pings Statisfy")
    async def ping_command(interaction: discord.Interaction):    
        author = interaction.user
        await b_commands.ping(interaction, bot)

    @tree.command(name="help", description="Access the Help Menu")
    async def help_command(interaction: discord.Interaction):    
        author = interaction.user
        await b_commands.help(interaction, author)

    @tree.command(name="list_artist", description="List Saved Artist")
    async def list_artist_command(interaction: discord.Interaction):    
        author = interaction.user
        await b_commands.list(interaction, author, "artists")
        
    @tree.command(name="get_artist_byid", description="Search and Retrieve Artist by URI code")
    @discord.app_commands.describe(id="Enter the Artist URI, URL, or Artist ID:")
    async def get_artist_byid_command(interaction: discord.Interaction, id: str):    
        author = interaction.user
        await b_commands.get(interaction, author, bot, "artists", id, access_token)
        
    @tree.command(name="get_artist_saved", description="Retrieve info of Saved Artists")
    async def get_artist_saved_command(interaction: discord.Interaction):
        author = interaction.user
        await b_commands.get(interaction, author, bot, "artists", "saved", access_token)
    
    @tree.command(name="get_track_byid", description="Search and Retrieve Track by URI code")
    @discord.app_commands.describe(id="Enter the Track URI, URL, or ID:")
    async def get_track_byid_command(interaction: discord.Interaction, id: str):    
        author = interaction.user
        await b_commands.get(interaction, author, bot, "tracks", id, access_token)
        
    @tree.command(name="get_playlist_byid", description="Search and Retrieve Public Playlist by URI code")
    @discord.app_commands.describe(id="Enter the Playlist URI, URL, or ID:")
    async def get_playlist_byid_command(interaction: discord.Interaction, id: str):    
        author = interaction.user
        await b_commands.get(interaction, author, bot, "playlists", id, access_token)
        
    @tree.command(name="get_album_byid", description="Search and Retrieve Track by URI code")
    @discord.app_commands.describe(id="Enter the Track URI, URL, or ID:")
    async def get_album_byid_command(interaction: discord.Interaction, id: str):    
        author = interaction.user
        await b_commands.get(interaction, author, bot, "albums", id, access_token)

    @tree.command(name="get_user_byid", description="Search and Retrieve Track by URI code")
    @discord.app_commands.describe(id="Enter the Track URI, URL, or ID:")
    async def get_album_byid_command(interaction: discord.Interaction, id: str):    
        author = interaction.user
        await b_commands.get(interaction, author, bot, "users", id, access_token)
        
    @tree.command(name="save_artist_byid", description="Save Artist by URI code")
    @discord.app_commands.describe(id="Enter the Artist URI, URL, or ID:")
    async def save_artist_byid_command(interaction: discord.Interaction, id: str):    
        author = interaction.user
        await b_commands.save(interaction, author, "artists", id, access_token)
        
    @tree.command(name='sync_slashcommands', description='Owner only')
    async def sync(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            await tree.sync()
            await interaction.response.send_message("Command Tree has been Synced.")
        else:
            await interaction.response.send_message('You must be the owner to use this command!')
            
    # Sync commands with Discord
    synced = await tree.sync()
    return synced