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

        self.current_song:list[dict[str, any], discord.channel.VoiceChannel] = None

        # [[song, channel]]
        self.music_queue:list[list[str]] = []
        self.FFMPEG_OPTIONS:dict[str, str] = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc:discord.voice_client.VoiceClient = None

    # searching the item on youtube
    def search_video(self, item:str) -> dict[str, any]:
        print(f'search_video: {item}')
        try:
            video:pt.YouTube = pt.Search(item).results.pop(0)
            return {'source': video.streams.get_audio_only().url, 'title': video.title}

        except Exception:
            print('an exception occured while searching youtube')
            return None
        
    def play_next(self) -> None:
        if len(self.music_queue) > 0:
            self.is_playing = True

            #remove the first element as you are currently playing it
            self.current_song = self.music_queue.pop(0)
            m_url = self.current_song[0]['source']

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        # no more songs left to play
        else:
            self.is_playing = False
            self.is_paused = False
            self.current_song = None

    # infinite loop checking 
    async def play_music(self, ctx:commands.context.Context) -> None:
        if len(self.music_queue) == 0:
            self.is_playing = False
            self.is_paused = False
            self.current_song = None
            return
        if self.is_paused:
            self.vc.resume()
            self.is_paused = False
            return
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
        self.is_paused = False

    async def add_song_queue(self, ctx:commands.context.Context, query:str, front:bool=False) -> None:
        # user must be in a voice channel to add song to queue
        if ctx.author.voice is None:
            await ctx.send("You must be in a voice channel!")
            return
        await ctx.send(f'Searching for "{query}"...')
        song:dict[str, any] = self.search_video(query)
        title:str = "title"  # use this to access the title of the song
        if not song:
            await ctx.send(f"{query} is invalid or not found")
            return
        await ctx.send(f'Added "{song[title]}" to the queue')
        if front:
            self.music_queue.insert(0, [song, ctx.author.voice.channel])
        else:
            self.music_queue.append([song, ctx.author.voice.channel])
        if not self.is_playing or self.is_paused:
            await self.play_music(ctx)

    # adding songs of a playlist to queue
    async def add_playlist_queue(self, ctx:commands.context.Context, item:str) -> str:
        print(f'add_playlist_queue: {item}')
        try:
            playlist:pt.Playlist = pt.Playlist(item)
            for video in playlist.videos:
                self.music_queue.append([{'source': video.streams.get_audio_only().url, 'title': video.title}, ctx.author.voice.channel])
            return playlist.title
        except Exception:
            print('an exception occured while searching youtube')

    @commands.command(name="play", aliases=["p","P"], help="Adds a song to the end of the queue")
    async def play(self, ctx:commands.context.Context, *args) -> None:
        query:str = " ".join(args)
        print(f'{ctx.author.name} - play: {query}')
        await self.add_song_queue(ctx, query)

    @commands.command(name="priority_play", aliases=["prio_play","prio_p","priop"], help="Adds song to the front of the queue")
    async def priority_play(self, ctx:commands.context.Context, *args) -> None:
        query:str = " ".join(args)
        print(f'{ctx.author.name} - priority_play: {query}')
        if ctx.author.guild_permissions.administrator == False:
            await ctx.send("You do not have permission to use this command")
            return
        await self.add_song_queue(ctx, query, front=True)

    @commands.command(name="playlist", aliases=["plylst", "pl"], help="Adds a playlist to queue")
    async def playlist(self, ctx:commands.context.Context, *args) -> None:
        query:str = " ".join(args)
        print(f'{ctx.author.name} - playlist: {query}')
        await ctx.send(f'Searching for "{query}"...')
        title:str = await self.add_playlist_queue(ctx, query)
        if not title:
            await ctx.send(f"{query} is invalid or not found")
            return
        await ctx.send(f'Added "{title}" to the queue')
        if not self.is_playing:
            await self.play_music(ctx)

    @commands.command(name="current", aliases=["c","C"], help="Displays the current song being played")
    async def current(self, ctx:commands.context.Context) -> None:
        print(f'{ctx.author.name} - current')
        if self.is_playing:
            # debugging
            if self.current_song is None:
                print('something went wrong. current song is None but something is playing')
                return
            await ctx.send(f'Now playing: {self.current_song[0]["title"]}')
        else:
            await ctx.send("No song is currently playing")

    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self, ctx:commands.context.Context, *args) -> None:
        print(f'{ctx.author.name} - pause')
        if self.is_playing:
            await ctx.send("Pausing playback")
            self.is_playing = False
            self.is_paused = True
            # current song does not change
            self.vc.pause()

    @commands.command(name = "resume", aliases=["r","R"], help="Resumes playing with the discord bot")
    async def resume(self, ctx:commands.context.Context, *args) -> None:
        print(f'{ctx.author.name} - resume')
        if self.is_paused:
            await ctx.send("Resuming playback")
            self.is_paused = False
            self.is_playing = True
            # current song does not change
            self.vc.resume()

    @commands.command(name = "skip", aliases=["s","S"], help="Skips the current song being played")
    async def skip(self, ctx:commands.context.Context) -> None:
        print(f'{ctx.author.name} - skip')
        if self.vc != None and self.vc:
            await ctx.send("Skipping song")
            self.vc.stop()
            # try to play next in queue if it exists
            await self.play_music(ctx)

    @commands.command(name="queue", aliases=["q"], help="Displays the current songs in queue")
    async def queue(self, ctx:commands.context.Context, num=10) -> None:
        print(f'{ctx.author.name} - queue')
        retval:str = "Song Queue: ("
        if len(self.music_queue) < num:
            retval += f'{len(self.music_queue)}/'
        else:
            retval += f'{num}/'
        retval += f'{len(self.music_queue)})\n'
        for i in range(0, len(self.music_queue)):
            # display first 10 songs in the queue
            if i >= num: 
                break
            retval += self.music_queue[i][0]['title'] + "\n"
        # sending messages
        if len(retval) > 2000:  # discord message limit is 2000 characters
            await self.queue(ctx, num-1)  # try again but show one less song
        else:
            await ctx.send(retval)

    @commands.command(name="clear", help="Stops the music and clears the queue")
    async def clear(self, ctx:commands.context.Context) -> None:
        print(f'{ctx.author.name} - clear')
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send("You must be in the same voice channel as the bot to use this command")
            if ctx.author.guild_permissions.administrator == False:
                return
            await ctx.send("Admin override: clearing queue")
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        self.current_song = None
        await ctx.send("Music queue cleared")

    @commands.command(name="disconnect", aliases=["dc"], help="Disconnect the bot from VC")
    async def disconnect(self, ctx:commands.context.Context) -> None:
        if ctx.author.voice.channel != self.vc.channel:
            await ctx.send("You must be in the same voice channel as the bot to use this command")
            if ctx.author.guild_permissions.administrator == False:
                return
            await ctx.send("Admin override: disconnecting")
        print(f'{ctx.author.name} - disconnect')
        self.is_playing = False
        self.is_paused = False
        self.music_queue = []
        self.current_song = None
        await ctx.send("Disconnecting from voice channel :(")
        await self.vc.disconnect()
