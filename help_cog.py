import discord
from discord.ext import commands
from ast import alias

class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = """
```
General commands:
.help - displays all the available commands
.play(p) - finds the song on youtube and plays it in your current channel. Will resume playing the current song if it was paused
.queue(s) - displays the current music queue
.skip(s) - skips the current song being played
.clear - Stops the music and clears the queue
.leave(l, disconnect) - Disconnected the bot from the voice channel
.pause - pauses the current song being played or resumes if already paused
.resume - resumes playing the current song
.current(c) - displays the current song being played
```
"""
        self.text_channel_list = []

    #some debug info so that we know the bot has started    
    @commands.Cog.listener()
    async def on_ready(self):
        return # uncomment this line to enable the help message
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == "general":
                    self.text_channel_list.append(channel)
        await self.send_to_all(self.help_message)        

    @commands.command(name="help", help="Displays all the available commands")
    async def help(self, ctx):
        print('help command')
        await ctx.send(self.help_message)

    async def send_to_all(self, msg):
        for text_channel in self.text_channel_list:
            await text_channel.send(msg)

    @commands.command(name="send_message", aliases=["sm"], help="Sends a message to all the text channels")
    async def send_message(self, ctx, *args):
        """
        format of command call: .sm server%$channel%$message
        """
        # check if user is admin (or ridoot)
        if ctx.author.guild_permissions.administrator == False and ctx.author.name != 'ridoot':
            return
        await ctx.send(f"Hello, {ctx.author.name}")
        full_arg = ' '.join(args)
        if full_arg.count('%$') != 2:
            await ctx.send("Invalid args. Please try again.")
            return
        target_server, target_channel, message = full_arg.split('%$')
        # find server/guild
        for guild in self.bot.guilds:
            if guild.name != target_server:
                continue
            if ctx.author not in guild.members:
                # user is not in this server
                await ctx.send("You must be in the specified server")
                return
            # find channel
            for channel in guild.text_channels:
                if channel.name != target_channel:
                    continue
                # send message
                await channel.send(message)
            
        