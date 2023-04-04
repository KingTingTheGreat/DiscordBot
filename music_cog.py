from ast import alias
import discord
from discord.ext import commands
import pytube as pt

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        self.is_playing = False
        self.is_paused = False

        # [[song, channel]]
        self.music_queue = []
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = None

     #searching the item on youtube
    def search_yt(self, item):
        try:
            video = pt.Search(item).results[0]
            return {'source': video.streams.get_audio_only().url, 'title': video.title}
        except Exception:
            print('an exception occured while searching youtube')
            return False

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            #get the first url
            m_url = self.music_queue[0][0]['source']

            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking 
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            #try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                #in case we fail to connect
                if self.vc == None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @commands.command(name="play", aliases=["p","P"], help="Plays selected song from youtube")
    async def play(self, ctx, *args):
        print('play command')
        query = " ".join(args)
        
        if ctx.author.voice is None:
            #you need to be connected so that the bot knows where to go
            await ctx.send("You must be in a voice channel!")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            title = "title"  # use this to access the title of the song
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.send(f'Added "{song[title]}" to the queue')
                self.music_queue.append([song, ctx.author.voice.channel])
                
                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="priority_play", aliases=["prio_play","prio_p","priop"], help="adds song to the front of the queue")
    async def priority_play(self, ctx, *args):
        print('priority_play command')
        query = " ".join(args)
        
        if ctx.author.voice is None:
            #you need to be connected so that the bot knows where to go
            await ctx.send("You must be in a voice channel!")
        elif self.is_paused:
            self.vc.resume()
        else:
            if ctx.author.guild_permissions.administrator == False:
                await ctx.send("You do not have permission to use this command")
                return
            else:
                await ctx.send("Hello, admin")
            song = self.search_yt(query)
            title = "title"  # use this to access the title of the song
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format try another keyword. This could be due to playlist or a livestream format.")
            else:
                await ctx.send(f'Added "{song[title]}" to the queue')
                self.music_queue.insert(0, [song, ctx.author.voice.channel])
                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args):
        print('pause command')
        if self.is_playing:
            ctx.send("Pausing playback")
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()

    @commands.command(name = "resume", aliases=["r","R"], help="Resumes playing with the discord bot")
    async def resume(self, ctx, *args):
        print('resume command')
        if self.is_paused:
            ctx.send("Resuming playback")
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()

    @commands.command(name = "skip", aliases=["s","S"], help="Skips the current song being played")
    async def skip(self, ctx):
        print('skip command')
        if self.vc != None and self.vc:
            ctx.send("Skipping song")
            self.vc.stop()
            # try to play next in queue if it exists
            await self.play_music(ctx)


    @commands.command(name="queue", aliases=["q"], help="Displays the current songs in queue")
    async def queue(self, ctx):
        print('queue command')
        retval = ""
        for i in range(0, len(self.music_queue)):
            # display first 10 songs in the queue
            if i >= 10: 
                break
            retval += self.music_queue[i][0]['title'] + "\n"

        if retval:
            await ctx.send(retval)
        else:
            await ctx.send("No music in queue")

    @commands.command(name="clear", help="Stops the music and clears the queue")
    async def clear(self, ctx):
        print('clear command')
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue cleared")

    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from VC")
    async def leave(self, ctx):
        print('leave command')
        self.is_playing = False
        self.is_paused = False
        self.music_queue = []
        ctx.send("Leaving voice channel :(")
        await self.vc.disconnect()
