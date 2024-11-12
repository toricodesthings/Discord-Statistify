#Load required libraries
import discord, json, os, time, inspect
from botmodules import slash_commands
from botmodules import commands as b_commands
from wrapper import authorizer as auth
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
    # Define potential arguments and filter based on function's required parameters
    possible_args = {
        'call_type': message,
        'author': author,
        'bot': bot,
        'token': access_token
    }
    pass_args = {arg: possible_args[arg] for arg in func_params if arg in possible_args}

    param_iter = iter(params)
    for param_name, param in func_params.items():
        if param_name not in pass_args and param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
            if param.default is not param.empty:
                pass_args[param_name] = next(param_iter, param.default)
            else:
                try:
                    pass_args[param_name] = next(param_iter)
                except StopIteration:
                    raise ValueError(f"The command {command} is missing a required parameter. See help for more!")

    return pass_args

@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    ctx = message.content
    # Command Handling
    if ctx.lower().startswith("s!"):
        if len(ctx) < 3:
            await message.reply("Hello there. If you need help, run /help or s!help")
            return

        command, params = b_commands.identify_commands(ctx)
        cmd_func = globals().get(command) or getattr(b_commands, command, None)

        if not (cmd_func and callable(cmd_func)):
            await message.reply(f"The command you entered '{command}' is invalid.")
            return

        try:
            # Gather arguments and call the command
            pass_args = gather_command_argument(command, cmd_func, message, message.author, bot, access_token, params)
            await cmd_func(**pass_args)
        except ValueError as ve:
            await message.reply(str(ve))

                
# Run the bot using your bot token
bot.run(bot_token)
