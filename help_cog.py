import discord
from discord.ext import commands

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
```
"""
        self.text_channel_list = []

    #some debug info so that we know the bot has started    
    @commands.Cog.listener()
    async def on_ready(self):
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