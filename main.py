import discord, os, yt_dlp, asyncio, logging
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

logging.basicConfig(level=logging.INFO)

ffmpeg_path = os.path.join(os.path.dirname(__file__), 'tools', 'ffmpeg.exe')

FFMPEG_OPTIONS = {
    'executable' : ffmpeg_path,
    'options' : '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'extractaudio': True,
    'audioformat': 'mp3',
    'postprocessors': [{ 
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'quiet': True, 
}

class DjWagner(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []
    
    @commands.command()
    async def play(self, ctx: commands.Context, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("You're not in a voice channel!")
        if not ctx.voice_client:
            await voice_channel.connect()
        
        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url, title))
                await ctx.send(f"Added to queue: **{title}**")
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)
    
    async def play_next(self, ctx: commands.Context):
        if self.queue:
            url, title = self.queue.pop(0)
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda _:self.client.loop.create_task(self.play_next(ctx)))
            await ctx.send(f'Now playing **{title}**')
        elif not ctx.voice_client.is_playing():
            await ctx.send("Queue is empty")
    
    @commands.command()
    async def skip(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped")

client = commands.Bot(command_prefix="!", intents=intents)

async def main(token):
    await client.add_cog(DjWagner(client))
    await client.start(token)

if __name__ == '__main__':
    token = os.getenv('bot_token', None)
    if token is None:
        print('Token was not found in the System Environmental Variables')
        quit()
    asyncio.run(main(token))
    pass