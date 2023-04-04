import discord
from discord.ext import commands
from help_cog import help_cog
from music_cog import music_cog
import asyncio

async def add_cogs(bot):
    await bot.add_cog(help_cog(bot))
    await bot.add_cog(music_cog(bot))

if __name__ == "__main__":
    bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())

    #remove the default help command so that we can write out own
    bot.remove_command('help')

    #register the class with the bot
    asyncio.run(add_cogs(bot))

    #start the bot with token
    with open("token.txt", "r") as f:
        token = f.read()
        token.strip()
        bot.run(token)
