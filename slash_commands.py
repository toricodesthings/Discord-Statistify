import discord
import commands as b_commands  
from discord.ui import Select, View

access_token = ""

async def setup_slash_commands(token, bot):
    tree = discord.app_commands.CommandTree(bot)
    global access_token
    access_token = token

    @tree.command(name="ping", description="Pings Statisfy")
    async def slash_command(interaction: discord.Interaction):    
        author = interaction.user
        await b_commands.ping(interaction, bot)

    @tree.command(name="help", description="Access the Help Menu")
    async def slash_command(interaction: discord.Interaction):    
        author = interaction.user
        await b_commands.help(interaction, author)

    @tree.command(name="list_artist", description="List Saved Artist")
    async def slash_command(interaction: discord.Interaction):    
        author = interaction.user
        await b_commands.list(interaction, author, "artists")
        
    @tree.command(name="get_artist_byid", description="Search and Retrieve Artist by URI code")
    @discord.app_commands.describe(id="Enter the Artist URI, URL, or Artist ID:")
    async def slash_command(interaction: discord.Interaction, id: str):    
        author = interaction.user
        await b_commands.get(interaction, author, bot, "artists", id, access_token)
        
    @tree.command(name="save_artist_byid", description="Save Artist by URI code")
    @discord.app_commands.describe(id="Enter the Artist URI, URL, or Artist ID:")
    async def slash_command(interaction: discord.Interaction, id: str):    
        author = interaction.user
        await b_commands.save(interaction, "artists", id, access_token)
        
    synced = await tree.sync()  # Sync commands with Discord
    return synced