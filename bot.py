#Load required libraries
import discord, json, os, inspect, asyncio
from botmodules import slash_commands
from botmodules import commands as b_commands
from wrapper import authorizer as auth
from datetime import datetime
from dotenv import load_dotenv

#TERMINAL COLOR CODE
RED, GREEN, LIGHT_BLUE, RESET = "\033[91m", "\033[92m", "\033[94m", "\033[0m" 

#Establish Global Variable access_token
access_token = ""
TOKEN_REFRESH_TASK = None

#-------------------------------------------------------------------------------------------------

#Load Token and Set Bot Parameters - Discord Application
load_dotenv()
bot_token, spotify_cid, spotify_csecret = os.getenv("DISCORD_TOKEN"), os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET") 
bot = discord.Client(intents=discord.Intents.all())

def load_settings():
    root_folder = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(root_folder, "settings.json")
    
    default = {
        "monthly_listener_scraping": False,
        "per_track_playcount_scraping": False,
        "syncslash_onstart": False
    } 
    try:
        with open(file_path, "r") as file:
            settings_from_file = json.load(file)
            print("Loaded Settings File! Passing it...")
            return settings_from_file  # Return the loaded settings as a dictionary
                
    except FileNotFoundError:
        print(f"{RED}settings.json not found, using default settings values.{RESET}")
        return default

    except json.JSONDecodeError:
        print(f"{RED}Error decoding settings.json. Check the file format. Using default settings values{RESET}")
        return default

async def refresh_token():
    """
    Periodically refresh the Spotify API access token.
    """
    global access_token
    while True:
        try:
            token, response_code, response_msg = await auth.request_token(spotify_cid, spotify_csecret)
            if token != 0:
                access_token = token
                print(f"{GREEN}Spotify API token refreshed: {access_token}{RESET}")
            else:
                print(f"{RED}Failed to refresh Spotify API token. Code: {response_code}, Message: {response_msg}{RESET}")
        except Exception as e:
            print(f"{RED}Unexpected error during token refresh: {e}{RESET}")
        
        await asyncio.sleep(3590)

#Report when Bot is Ready and Sync Slash Commands
@bot.event
async def on_ready():
    """
    Establishes required functions and request for Spotify API access token when bot finishes connecting to Discord
    """
    global TOKEN_REFRESH_TASK
    print(f"{GREEN}{bot.user.name} has connected to Discord Successfully!{RESET}")
    
    # Start Token Request
    token, response_code, response_msg = await auth.request_token(spotify_cid, spotify_csecret)
    if token != 0:
        global access_token
        access_token = token
        print(f"{GREEN}Spotify API access granted with token: {access_token}{RESET}")
    else:
        print(f"{RED}Spotify API access error with code: {response_code}\nError Message: {response_msg}")
        print(f"Bot has no access to Spotify API, please troubleshoot and restart!{RESET}")
        return
    
    if TOKEN_REFRESH_TASK is None or TOKEN_REFRESH_TASK.done():
        TOKEN_REFRESH_TASK = asyncio.create_task(refresh_token())
    else:
        print(f"{LIGHT_BLUE}Token refresh task is already running.{RESET}")
    
    settings = load_settings()
    print(b_commands.sync_settings(settings))
    
    try:
        await slash_commands.setup_slash_commands(access_token, bot)
    except Exception as e:
        print(e)    

    if settings.get("syncslash_onstart", False) is True:
        # Load and Sync Slash Commands Module and Pass access_token to Module
        try:
            synced = await slash_commands.automatic_sync(bot)
            print(f"{LIGHT_BLUE}Bot has automatically synced {len(synced)} command(s){RESET}")
        except Exception as e:
            print(e)    
    else:
        print(f"{LIGHT_BLUE}Slash commands are not synced automatically. You may do this manually by running /sync{LIGHT_BLUE}")
        
    print(f"{GREEN}Bot is Ready{RESET}")
        
def gather_command_argument(command, cmd_func, message, author, bot, token, params):
    """
    Gathers and maps arguments to the parameters of a command function.

    Args:
        command (str): The name of the command being executed.
        cmd_func (function): The function to execute for the command.
        message (discord.Message): The message object containing the command.
        author (discord.User): The user who issued the command.
        bot (discord.Client): The bot instance.
        token (str): The access token for authorization.
        params (list): The additional parameters passed with the command.

    Returns:
        dict: A dictionary of arguments to pass to the command function.
    
    Raises:
        ValueError: If a required parameter is missing and no default value is provided.
    """
    # Get the parameters of the command function
    func_params = inspect.signature(cmd_func).parameters

    # Define potential arguments
    possible_args = {
        'call_type': message, 
        'author': author,
        'bot': bot,
        'token': access_token,
    }

    # Filter arguments to match the command function's signature
    pass_args = {arg: possible_args[arg] for arg in func_params if arg in possible_args}

    # Iterate over remaining params
    param_iter = iter(params)
    for param_name, param in func_params.items():
        if param_name not in pass_args and param.kind in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
            if param.default is not param.empty:
                # Assign default if no parameter is available
                pass_args[param_name] = next(param_iter, param.default)
            else:
                # Assign remaining parameters as a single string for specific cases
                if param_name == "searchinput":
                    pass_args[param_name] = " ".join(param_iter)
                    break  # Remaining params captured
                else:
                    try:
                        pass_args[param_name] = next(param_iter)
                    except StopIteration:
                        raise ValueError(f"The command '{command}' is missing a required parameter. See help for details.")

    return pass_args


@bot.event
async def on_message(message):
    """
    Handles incoming messages and processes commands prefixed with 's!'.

    Args:
        message (discord.Message): The message object from Discord.
    """
    # Ignore messages from bots
    if message.author.bot:
        return

    # Extract the message content
    ctx = message.content.strip()
    
    # Handle commands starting with 's!'
    if ctx.lower().startswith("s!"):
        if len(ctx) < 3:
            await message.reply("Hello there. If you need help, run `/help` or `s!help`.")
            return

        # Identify the command and parameters
        command, params = b_commands.identify_commands(ctx)
        cmd_func = globals().get(command) or getattr(b_commands, command, None)

        # Validate the command
        if not (cmd_func and callable(cmd_func)):
            await message.reply(f"The command you entered '{command}' is invalid.")
            return

        try:
            # Prepare and pass arguments to the command function
            pass_args = gather_command_argument(
                command=command,
                cmd_func=cmd_func,
                message=message,
                author=message.author,
                bot=bot,
                token=access_token,
                params=params
            )
            await cmd_func(**pass_args)

        except ValueError as ve:
            # Handle ValueErrors raised by command execution
            await message.reply(str(ve))

# Run the bot using bot token located in .env
if __name__ == "__main__":
    bot.run(bot_token)
