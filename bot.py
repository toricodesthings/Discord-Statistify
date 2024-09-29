#Load required libraries
import discord, json, os, aiohttp, time, inspect
from datetime import datetime
import commands as b_commands
import apiwrapper as spotifyapi
from dotenv import load_dotenv

RED = "\033[91m"
GREEN = "\033[92m"
LIGHT_BLUE = "\033[94m"
RESET = "\033[0m"        

#Establish Spotify Web Endpoint
auth_endpoint = "https://accounts.spotify.com/api/token"
access_token = ""

#Load and Request Token - Spotify Web API
def load_token():
    file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
    
    try:
        with open(file_path, 'r') as file:
            saved_token = json.load(file)
            
            # Check if token is previous generated
            if saved_token and saved_token["access_token"] is not None:
                current_time = int(time.time())
                # Check if token is expired and attempt to generate a new one if 30 seconds before expiration
                if current_time < (saved_token["expires_at"] - 30):
                    token = saved_token["access_token"]
                    expiry_time = datetime.fromtimestamp(saved_token["expires_at"]).strftime("%d-%m-%y %H:%M:%S")
                    return token, expiry_time
                
    except FileNotFoundError:
        pass
    return None, None
    
def store_token(token, expires_at):
    file_path = os.path.join(os.path.dirname(__file__), 'accesstoken.json')
    token_data = {
        'access_token': token,
        'expires_at': expires_at
    }
    try:
        with open(file_path, 'w') as file:
            json.dump(token_data, file)
    except Exception as exc:
        print(f"{RED}Error storing token: {exc}{RESET}")
    
async def req_token(auth_e, c_id, c_secret):
    # Attempt to load previously generated token
    token, expiry = load_token()    
    
    if token and expiry:
        print(f"{LIGHT_BLUE}Passing on previously generated token\nThis token will expire at {expiry}{RESET}")
        return token, 200, None
    
    print("No token previously generated. Proceed to generation...")
    token, expiry, response_code, response_msg = await spotifyapi.generate_token(auth_e, c_id, c_secret)
    if token and response_code == 200:
        store_token(token, expiry)
    return token, response_code, response_msg

    
#-------------------------------------------------------------------------------------------------

#Load Token and Set Bot Parameters - Discord Application
load_dotenv()
bot_token, spotify_cid, spotify_csecret = os.getenv("DISCORD_TOKEN"), os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET") 
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
    except Exception as e:
        print(e)
        
    # Start Token Request
    token, response_code, response_msg = await req_token(auth_endpoint, spotify_cid, spotify_csecret)
    if not token == 0:
        global access_token
        access_token = token
        print(f"{GREEN}Spotify API access granted with token: {access_token}{RESET}")
    else:
        print(f"{RED}Spotify API access error with code: {response_code}\nError Message: {response_msg}{RESET}")

def gather_command_argument(command, cmd_func, message, author, bot, access_token, params, ):
    func_params = inspect.signature(cmd_func).parameters
    possible_args = {
        'call_type': message,
        'author': author,
        'bot': bot,
        'token': access_token
    }
    
    # Store only required parameters
    pass_args = {arg: v for arg, v in possible_args.items() if arg in func_params}
    param_iter = iter(params)
    # If requied, assign user input parameters to remaining positional arguments
    for param_name, param in func_params.items():
        if param_name in pass_args:
            continue
        if param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
            try:
                pass_args[param_name] = next(param_iter)
            except StopIteration:
                if param.default is param.empty:
                    raise ValueError(f"The command {command} is missing the required parameter. See help for more!")
    return pass_args

@bot.event
async def on_message(message):
    # Store Variables
    author = message.author
    ctx = message.content
    
    # Ignore self messages
    if author.bot:
        return

    # Command Handling Module
    if ctx.lower().startswith("s!"):
        if len(ctx) < 3:
            await message.reply("Hello there. If you need help, run /help or s!help")
        else:
            command, params = b_commands.identify_commands(ctx)

            cmd_func = globals().get(command) or getattr(__import__('commands'), command, None)
            if cmd_func and callable(cmd_func):
                try:
                    # Gather arguments and call the command
                    pass_args = gather_command_argument(command, cmd_func, message, author, bot, access_token, params)
                    await cmd_func(**pass_args)
                except ValueError as ve:
                    await message.reply(ve)
            else:
                await message.reply(f"The command you entered '{command}' is invalid.")
                   
# Slash Commands

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
    await b_commands.list(interaction, author, bot, "artists")
    
@tree.command(name="get_artist_byid", description="Search Artist by URI code")
@discord.app_commands.describe(id="Enter the Artist URI, URL, or Artist ID:")
async def slash_command(interaction: discord.Interaction, id: str):    
    author = interaction.user
    await b_commands.get(interaction, author, id, access_token)

# Run the bot using your bot token
bot.run(bot_token)
