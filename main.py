import discord
from discord import Client, Intents, Interaction, app_commands, Object, Embed, Member, User, Message, Role
import os
import sys
import logging 
import asyncio
from datetime import datetime
from defines import moderator_roles, success_color, error_color, success_emoji, error_emoji
from exceptions import HasRole, NoRole
        
print(f'Python Version: {sys.version}')    
    
#logger = logging.getLogger()
#logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        
intents = Intents.all()
        
client = Client(intents=intents)

tree = app_commands.CommandTree(client)
    
#log_file = f'logs/{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}.log'

#with open(log_file, 'w+') as f:
#    pass
    
#handler = logging.FileHandler(filename=log_file, encoding='utf-8', mode='w+')
#handler.setLevel(logging.DEBUG)
#handler.setFormatter(formatter)
#logger.addHandler(handler)

guild = Object(id=os.environ.get('GUILD_ID'))

# logger.info('\n')

#logger.debug('Application started')

async def send_to_log(ctx_or_message, **kwargs): # replace with ctx
    
    if isinstance(ctx_or_message, Message):
        message = ctx_or_message
        
        title = '**Message**'
        
        if 'before' in kwargs:
            before = kwargs['before']
            description = f':information: {message.author.mention} edited message in {message.channel.mention}: \n{before.content} -> {message.content}'
        elif 'deleted' in kwargs:
            description = f':information: {message.author.mention} deleted message in {message.channel.mention}: \n{message.content}'
        else:
            description = f':information: {message.author.mention} sent message in {message.channel.mention}: \n{message.content}'
        color = 0x4287F5
    elif isinstance(ctx_or_message, Interaction):
        ctx = ctx_or_message
        
        error = ctx.command_failed
        emoji = error_emoji if error else success_emoji
        color = error_color if error else success_color
        
        title = '**Command**'
        
        match ctx.command.name:
            case 'add_role':
                description = f':{emoji}: {ctx.user.mention} {"unsuccessfully" if error else "successfully"} added {kwargs.pop("role").mention} role to {kwargs.pop("target").mention}'
            case 'ban':
                description = f':{emoji}: {ctx.user.mention} {"unsuccessfully" if error else "successfully"} banned {kwargs.pop("target").mention}.'
            case 'unban':
                description = f':{emoji}: {ctx.user.mention} {"unsuccessfully" if error else "successfully"} unbanned {kwargs.pop("target").mention}.'
            case 'kick':
                description = f':{emoji}: {ctx.user.mention} {"unsuccessfully" if error else "successfully"} kicked {kwargs.pop("target").mention}.'
            case 'remove_role':
                description = f':{emoji}: {ctx.user.mention} {"unsuccessfully" if error else "successfully"} removed {kwargs.pop("role").mention} role to {kwargs.pop("target").mention}'
            case _:
                description = f':{emoji}: {ctx.user.mention} used "{ctx.command.name}" command {"unsuccessfully" if error else "successfully"} in {ctx.channel.mention}'
        
    embed = Embed(title=title, description=description, color=color)
    
    await log_channel.send(embed=embed)

@client.event
async def on_ready():
    global log_channel
    
    log_channel = await client.fetch_channel(os.environ.get('LOG_CHANNEL_ID'))
    await tree.sync(guild=Object(id=os.environ.get('GUILD_ID')))
    print(f"Logged in as {client.user}")
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await send_to_log(message)
    
@client.event
async def on_message_edit(before, after):
    await send_to_log(after, before=before)
    
@client.event
async def on_message_delete(message):
    await send_to_log(message, deleted=True)
        
@tree.command(name='ban', description='Bans the specified user.', guild=guild)
@app_commands.checks.has_any_role(*moderator_roles)
async def ban(ctx, user: User, reason: str):
    # logger.debug(f'[COMMAND] #{ctx.channel.name} {ctx.user}: ban')
    await ctx.guild.ban(user=await client.fetch_user(user.id), reason=reason, delete_message_days=0)
    embed = Embed(color=0x38761D, description=f':white_check_mark: **{user.mention} has been banned!\n**Reason: *{reason}*')
    await ctx.response.send_message(embed=embed, ephemeral=True)
    await send_to_log(ctx, target=user)
    
@tree.command(name='unban', description='Unbans the specified user.', guild=guild)
@app_commands.checks.has_any_role(*moderator_roles)
async def unban(ctx, user: User, reason: str):
    await ctx.guild.unban(user=await client.fetch_user(user.id), reason=reason)
    embed = Embed(color=success_color, description=f':{success_emoji}: **{user.mention} has been unbanned!**\nReason: *{reason}*')
    await ctx.response.send_message(embed=embed, ephemeral=True)
    await send_to_log(ctx, target=user)
    
@tree.command(name='kick', description='Kicks the specified user.', guild=guild)
@app_commands.checks.has_any_role(*moderator_roles)
async def kick(ctx, user: Member, reason: str=None):
    await user.kick(reason=reason)
    embed = Embed(color=success_color, description=f':{success_emoji}: **{user.mention} has been kicked!**\nReason: *{reason}*')
    await ctx.response.send_message(embed=embed, ephemeral=True)
    await send_to_log(ctx, target=user)
    
@tree.command(name='add_role', description='Adds specified role to the specified user.', guild=guild)
@app_commands.checks.has_any_role(*moderator_roles)
async def add_role(ctx, user: Member, role: Role):
    if role in user.roles:
        raise HasRole
    
    await user.add_roles(role)
    embed = Embed(color=success_color, description=f':{success_emoji}: **The {role.mention} role has been added to {user.mention}!**')
    await ctx.response.send_message(embed=embed, ephemeral=True)
    await send_to_log(ctx, target=user, role=role)
    

    
@tree.command(name='remove_role', description='Removes specified role from the specified user.', guild=guild)
@app_commands.checks.has_any_role(*moderator_roles)
async def remove_role(ctx, user: Member, role: Role):
    if role not in user.roles:
        raise NoRole
    
    await user.remove_roles(role)
    embed = Embed(color=success_color, description=f':{success_emoji}: **The {role.mention} role has been removed from {user.mention}!**')
    await ctx.response.send_message(embed=embed, ephemeral=True)
    await send_to_log(ctx, target=user, role=role)
   
@ban.error
@unban.error 
@add_role.error
@remove_role.error 
async def error_handler(ctx, error):
    #logger.error(error)
    
    if isinstance(error, app_commands.MissingAnyRole):
        embed = Embed(color=error_color, description=f':{error_emoji}: **You DON\'T have permission to use this command!**')
    elif isinstance(error, app_commands.TransformerError):
        embed = Embed(color=error_color, description=f':{error_emoji}: **The specified user is NOT in the server!**')
    elif isinstance(error, app_commands.CommandInvokeError) and ctx.command.name == 'add_role':
        embed = Embed(color=error_color, description=f':{error_emoji}: **The specified user already has the role!**')
    elif isinstance(error, app_commands.CommandInvokeError) and ctx.command.name == 'remove_role':
        embed = Embed(color=error_color, description=f':{error_emoji}: **The specified user doesn\'t have the role!**')
    else:
        embed = Embed(color=error_color, description=f':{error_emoji}: **Unexpected error:"\n{type(error)}**')
    
    await ctx.response.send_message(embed=embed, ephemeral=True)
    await send_to_log(ctx)
    
if __name__ == '__main__':
    embed = Embed(color=0xEC1600, description=':x: **You DON\'T have permission to use this command!**')
    client.run(os.environ.get('BOT_TOKEN'))
    
#* ctx = interaction