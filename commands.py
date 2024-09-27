import discord
    
# Bot Latency Function
async def ping(call_type, author, bot):
    ping = round(bot.latency * 1000, 2)
    bot_msg = f"Pong! Bot latency is currently `{ping} ms`"
    if isinstance(call_type, discord.Message):
        await call_type.reply(bot_msg)
    else:
        await call_type.response.send_message(bot_msg)

# Help Function
async def help(call_type, author, bot):
    if isinstance(call_type, discord.Message):
        await call_type.reply("This is the help function.")
    else:
        await call_type.response.send_message(f"This is the help function.")
        
# List Presaved Artist Function
def list_artists(author, bot):
    global presaved_artist
    embed = discord.Embed(
        title="Saved Artists",
        description="List of presaved artists (use help find out how to save artists)",
        color=discord.Color.green(),
    )
            
    embed.set_footer(text=f"Called by {author}")
    artist_list = ""
    for x in presaved_artist:
        artist_list += f"{x}\n"
    embed.add_field(name="Artists", value=artist_list, inline=False)
    return embed

# List Saved Artists
async def list(message, author, bot, list_param, *args):
    if list_param == 'artists':
        r = list_artists(author, bot)
        await message.reply(embed=r)
    else:
        await message.reply(f"The parameter of the list function `{list_param}` is invalid.")