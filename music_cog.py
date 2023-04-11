from ast import alias
import discord
from discord.ext import commands
import pytube as pt
import requests

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot:commands.Bot = bot
    
        self.is_playing:bool = False
        self.is_paused:bool = False

        self.current_song = None

        # [[song, channel]]
        self.music_queue:list[list[str]] = []
        self.FFMPEG_OPTIONS:dict[str, str] = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = None

     #searching the item on youtube
    def search_yt(self, item) -> dict[str, any]:
        try:
            search:pt.Search = pt.Search(item)
            while search.results:
                video:pt.YouTube = search.results.pop(0)
                # only videos that are longer than 1 minute to filter out shorts
                if video.length > 60:
                    return {'source': video.streams.get_audio_only().url, 'title': video.title}
                if not search.results:
                    search.get_next_results()
            return False
        except Exception:
            print('an exception occured while searching youtube')
            return False

    def play_next(self) -> None:
        if len(self.music_queue) > 0:
            self.is_playing = True

            #remove the first element as you are currently playing it
            self.current_song = self.music_queue.pop(0)
            m_url = self.current_song[0]['source']

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
            self.current_song = None

    # infinite loop checking 
    async def play_music(self, ctx) -> None:
        if len(self.music_queue) > 0:
            target_channel = self.music_queue[0][1]
            # try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await target_channel.connect()
                # in case we fail to connect
                if self.vc == None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(target_channel)
            
            #remove the first element as you are currently playing it
            self.current_song = self.music_queue.pop(0)
            m_url = self.current_song[0]['source']
            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
            
            self.is_playing = True
        else:
            self.is_playing = False

    async def add_song_queue(self, ctx, query, front=False) -> None:
        # user must be in a voice channel to add song to queue
        if ctx.author.voice is None:
            await ctx.send("You must be in a voice channel!")
        elif self.is_paused:
            self.vc.resume()
        else:
            await ctx.send(f'Searching for "{query}"...')
            song:dict[str, any] = self.search_yt(query)
            title:str = "title"  # use this to access the title of the song
            if not song:
                await ctx.send(f"{query} is invalid or not found")
            else:
                await ctx.send(f'Added "{song[title]}" to the queue')
                if front:
                    self.music_queue.insert(0, [song, ctx.author.voice.channel])
                else:
                    self.music_queue.append([song, ctx.author.voice.channel])
                if self.is_playing == False:
                    await self.play_music(ctx)

    @commands.command(name="play", aliases=["p","P"], help="Plays selected song from youtube")
    async def play(self, ctx, *args) -> None:
        # print(self.is_playing, self.is_paused)
        print('play command')
        query:str = " ".join(args)
        await self.add_song_queue(ctx, query)

    @commands.command(name="priority_play", aliases=["prio_play","prio_p","priop"], help="adds song to the front of the queue")
    async def priority_play(self, ctx, *args) -> None:
        print('priority_play command')
        query:str = " ".join(args)
        if ctx.author.guild_permissions.administrator == False:
            await ctx.send("You do not have permission to use this command")
            return
        await self.add_song_queue(ctx, query, front=True)

    @commands.command(name="current", aliases=["c","C"], help="Displays the current song being played")
    async def current(self, ctx) -> None:
        print('current command')
        if self.is_playing:
            # debugging
            if self.current_song is None:
                print('something went wrong. current song is None but something is playing')
                return
            await ctx.send(f'Now playing: {self.current_song[0]["title"]}')
        else:
            await ctx.send("No song is currently playing")

    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx, *args) -> None:
        print('pause command')
        if self.is_playing:
            await ctx.send("Pausing playback")
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()

    @commands.command(name = "resume", aliases=["r","R"], help="Resumes playing with the discord bot")
    async def resume(self, ctx, *args) -> None:
        print('resume command')
        if self.is_paused:
            await ctx.send("Resuming playback")
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()

    @commands.command(name = "skip", aliases=["s","S"], help="Skips the current song being played")
    async def skip(self, ctx) -> None:
        print('skip command')
        if self.vc != None and self.vc:
            await ctx.send("Skipping song")
            self.vc.stop()
            # try to play next in queue if it exists
            await self.play_music(ctx)

    @commands.command(name="queue", aliases=["q"], help="Displays the current songs in queue")
    async def queue(self, ctx) -> None:
        print('queue command')
        retval:str = "Song Queue: ("
        if len(self.music_queue) < 10:
            retval += f'{len(self.music_queue)}/'
        else:
            retval += '10/'
        retval += f'{len(self.music_queue)})\n'
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
    async def clear(self, ctx) -> None:
        print('clear command')
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        self.current_song = None
        await ctx.send("Music queue cleared")

    @commands.command(name="leave", aliases=["disconnect", "dc"], help="Kick the bot from VC")
    async def leave(self, ctx) -> None:
        print('leave command')
        self.is_playing = False
        self.is_paused = False
        self.music_queue = []
        self.current_song = None
        await ctx.send("Leaving voice channel :(")
        await self.vc.disconnect()
