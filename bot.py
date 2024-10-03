#Load required libraries
import discord, json, os, time, inspect, slash_commands
import commands as b_commands
import authorizer as auth
from datetime import datetime
from dotenv import load_dotenv

#TERMINAL COLOR CODE
RED, GREEN, LIGHT_BLUE, RESET = "\033[91m", "\033[92m", "\033[94m", "\033[0m" 

#Establish Global Variable access_token
access_token = ""

#-------------------------------------------------------------------------------------------------

#Load Token and Set Bot Parameters - Discord Application
load_dotenv()
bot_token, spotify_cid, spotify_csecret = os.getenv("DISCORD_TOKEN"), os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET") 
bot = discord.Client(intents=discord.Intents.all())

#Report when Bot is Ready and Sync Slash Commands
@bot.event
async def on_ready():
    print(f"{GREEN}{bot.user.name} has connected to Discord Successfully!{RESET}")
    presaved_artist = b_commands.load_ps_artist()
    if len(presaved_artist) > 0:
        print(f"{LIGHT_BLUE}Loaded {len(presaved_artist)} saved artists{RESET}")
    else:
        print(f"{RED}No presaved elements loaded, this might be an error{RESET}")
    
    # Start Token Request
    token, response_code, response_msg = await auth.request_token(spotify_cid, spotify_csecret)
    if not token == 0:
        global access_token
        access_token = token
        print(f"{GREEN}Spotify API access granted with token: {access_token}{RESET}")
    else:
        print(f"{RED}Spotify API access error with code: {response_code}\nError Message: {response_msg}{RESET}")
        
    # Load and Sync Slash Commands Module and Pass access_token to Module
    try:
        synced = await slash_commands.setup_slash_commands(access_token, bot)
        print(f"{LIGHT_BLUE}Bot has synced {len(synced)} command(s){RESET}")
    except Exception as e:
        print(e)
    
    print(f"{GREEN}Bot is Ready{RESET}")
        
def gather_command_argument(command, cmd_func, message, author, bot, access_token, params):
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
                
# Run the bot using your bot token
bot.run(bot_token)
