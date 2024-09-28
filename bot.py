#Load required libraries
import discord, json, os, aiohttp, time, inspect
from datetime import datetime
import commands as b_commands
from dotenv import load_dotenv

RED = "\033[91m"
GREEN = "\033[92m"
LIGHT_BLUE = "\033[94m"
RESET = "\033[0m"        

#Establish Spotify Web Endpoint
web_endpoint = "https://api.spotify.com"
auth_endpoint = "https://accounts.spotify.com/api/token"
access_token = ""

#Load and Request Token - Spotify Web API
def load_token():
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
        with open(file_path, 'r') as file:
            saved_token = json.load(file)
            if saved_token and saved_token["access_token"] is not None:
                current_time = int(time.time())
                if saved_token["expires_at"] is not None and current_time < (saved_token["expires_at"] - 30):
                    token = saved_token["access_token"]
                    expiry_time = datetime.fromtimestamp(saved_token["expires_at"]).strftime("%d-%m-%y %H:%M:%S")
                    return token, expiry_time
    except FileNotFoundError:
        return None, None
    
def store_token(token, expires_at):
    file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
    token_data = {
        'access_token': token,
        'expires_at': expires_at
    }
    with open(file_path, 'w') as file:
        json.dump(token_data, file)
    
async def req_token(auth_e, c_id, c_secret):
    
    token, expiry = load_token()    
    if token and expiry:
        print(f"{LIGHT_BLUE}Passing on previously generated token\nThis token will expire at {expiry}{RESET}")
        return token, 1, None
    else:
        print("No token previously generated. Proceed to generation...")

    #Set Parameters
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': c_id,
        'client_secret': c_secret
    }
    try: 
        print(f"Requesting token from {auth_e}...")
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_e, headers = headers, data = data) as response:
                if response.status == 200:
                    r = await response.json()
                    token = r['access_token']
                    expiry = int(time.time()) + r['expires_in']
                    store_token(token, expiry)
                    return token, response.status, None
                else:
                    error = await response.text()
                    print(f"API Endpoint Error. See Spotify API reference page for details.")
                    return 0, response.status, error
    except Exception as exc:
        print(f"Encountered Unexpected Error: {exc}")
#-------------------------------------------------------------------------------------------------

#Load Token and Set Bot Parameters - Discord Application
load_dotenv()
bot_token = os.getenv("DISCORD_TOKEN")
spotify_cid = os.getenv("CLIENT_ID")
spotify_csecret = os.getenv("CLIENT_SECRET") 
bot = discord.Client(intents=discord.Intents.all())
tree = discord.app_commands.CommandTree(bot)

#Report when Bot is Ready and Sync Slash Commands
@bot.event
async def on_ready():
    print(f"{GREEN}{bot.user.name} has connected to Discord Successfully!{RESET}")
    presaved_artist = b_commands.load_ps_artist()
    if len(presaved_artist) > 0:
        print(f"{LIGHT_BLUE}Loaded {len(presaved_artist)} saved artists{RESET}")
    else:
        print(f"{RED}No presaved elements loaded, this might be an error{RESET}")
    
    # Sync Slash Commands
    try:
        synced = await tree.sync()
        print(f"{LIGHT_BLUE}Bot has synced {len(synced)} command(s){RESET}")
    except Exception as exc:
        print(exc)
        
    # Start Token Request
    token, code, response = await req_token(auth_endpoint, spotify_cid, spotify_csecret)
    if not token == 0:
        global access_token
        access_token = token()
        print(f"{GREEN}Spotify API access granted with token: {token}{RESET}")
    else:
        print(f"{RED}Spotify API access error with code: {code}{RESET}")
        print(response)

def identify_commands(ctx):
    parts = ctx[2:].split()
    command = parts[0]  # Remove the "!" from the command
    if len(parts) > 1:
        params = parts[1:]  # The rest are parameters
        return command, params
    else:
        return command, False

@bot.event
async def on_message(message):
    #Store Variables
    author = message.author
    ctx = message.content.lower()
    
    #Ignore self messages
    if author.bot:
        return
    
    
    
    #Command Module
    if ctx.startswith("s!"):
        if len(ctx) < 3:
            await message.reply("Hello there. If you need help, run /help or s!help")
        else:
            command, params = identify_commands(ctx)
            try:
                cmd_func = globals().get(command) or getattr(__import__('commands'), command, None)
                if cmd_func is not None and callable(cmd_func):
                    func_signature = inspect.signature(cmd_func)
                    
                    global access_token
                    possible_args = {
                        'message': message,
                        'author': author,
                        'bot': bot,
                        'token': access_token,
                        'params': params 
                    }
                    if params:
                        await cmd_func(message, author, bot, *params)
                    else:
                        await cmd_func(message, author, bot)
                else:
                    await message.reply(f"The command you entered '{command}' is invalid.")
            except AttributeError:
                await message.reply(f"The command you entered '{command}' is invalid.")


@tree.command(name="ping", description="Pings Statisfy")
async def slash_command(interaction: discord.Interaction):    
    author = interaction.user
    await b_commands.ping(interaction, author, bot)

@tree.command(name="help", description="Access the Help Menu")
async def slash_command(interaction: discord.Interaction):    
    author = interaction.user
    await b_commands.help(interaction, author, bot)

@tree.command(name="list_artist", description="List Saved Artist")
async def slash_command(interaction: discord.Interaction):    
    author = interaction.user
    await b_commands.list(interaction, author, bot, "artists")

# Run the bot using your bot token
bot.run(bot_token)
