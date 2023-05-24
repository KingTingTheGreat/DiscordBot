import discord
from discord.ext import commands
from ast import alias

class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = """
```
Hello! I am TheMusicIndustry, a bot that can play music from YouTube. 
Here are some of my commands:
.help - displays all the available commands
.play(p) - finds the song on youtube and adds it to queue
.playlist(pl) - finds the playlist on youtube and adds all the songs to queue
.queue(s) - displays the current music queue up to 10 songs
.skip(s) - skips the current song being played
.clear - stops music playback and clears queue
.disconnect(dc) - disconnects the bot from voice channel and clears queue
.pause - pauses the current song being played
.resume - resumes the current song being played
.current(c) - displays the current song being played
```
"""
        self.text_channel_list = []

    #some debug info so that we know the bot has started    
    @commands.Cog.listener()
    async def on_ready(self):
        print('bot is ready')
        return # uncomment this line to enable the help message on startup
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == "general":
                    self.text_channel_list.append(channel)
        await self.send_to_all(self.help_message)        

    @commands.command(name="help", help="Displays all the available commands")
    async def help(self, ctx):
        print(f'{ctx.author.name} - help')
        await ctx.send(self.help_message)

    async def send_to_all(self, msg):
        print('send_to_all command')
        for text_channel in self.text_channel_list:
            await text_channel.send(msg)

    @commands.command(name="send_message", aliases=["sm"], help="Sends a message to all the text channels")
    async def send_message(self, ctx, *args):
        """
        format of command call: .sm server%$channel%$message
        """
        print(f'{ctx.author.name} - send_message')
        # check if user is admin (or ridoot)
        if ctx.author.guild_permissions.administrator == False and ctx.author.name != 'ridoot':
            print('user does not have adequate permissions')
            return
        await ctx.send(f"Hello, {ctx.author.name}")
        full_arg = ' '.join(args)
        if full_arg.count('%$') != 2:
            await ctx.send("Invalid args. Please try again.")
            return
        target_server, target_channel, message = full_arg.split('%$')
        print(f"target_server: {target_server}")
        print(f"target_channel: {target_channel}")
        print(f"message: {message}")
        # find server/guild
        for guild in self.bot.guilds:
            # stripping quotes because of how discord.py handles guild names
            if guild.name.strip('"') != target_server:
                continue
            if ctx.author not in guild.members:
                # user is not in this server
                await ctx.send(f"You must be in the specified server: {target_server}")
                print(f"User is not in the specified server: {target_server}")
                return
            # find channel
            for channel in guild.text_channels:
                if channel.name != target_channel:
                    continue
                # send message
                await channel.send(message)
                break
            else:
                # channel not found
                await ctx.send(f"Channel not found: {target_channel}")
                print(f"Channel not found: {target_channel}")
            
        