
import discord
from discord.ext import commands
import random
import youtube_dl
import asyncio

description = '''Jazari BOT
'''

intents = discord.Intents.default()
intents.members = True
client = discord.Client()

bot = commands.Bot(command_prefix=commands.when_mentioned_or("$"), description=description, intents=intents, case_insensitive=True)


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

@bot.event
async def on_ready():
    print('Jazari Baslatiliyor...')
    print('Jazari giris yapti!')
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="$help"))


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Bir ses kanalına katılır."""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        """Bilgisayarınızın yerel dosyasından bir mp3 oynatır. """

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print('Oynatıcı hatası: %s' % e) if e else None)

        await ctx.send('Şimdi oynatılıyor: {}'.format(query))

    @commands.command()
    async def yt(self, ctx, *, url):
        """Bir Youtube URL'sinden oynatır (şuan çalışmamakta)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Oynatıcı hatası: %s' % e) if e else None)

        await ctx.send('Şimdi oynatılıyor: {}'.format(player.title))

    @commands.command()
    async def stream(self, ctx, *, url):
        """Bir URL'den yayınlar."""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Oynatıcı hatası: %s' % e) if e else None)

        await ctx.send('Şimdi oynatılıyor: {}'.format(player.title))

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Oynatıcının ses seviyesini değiştirir."""

        if ctx.voice_client is None:
            return await ctx.send("Ses kanalına bağlı değilsiniz.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Ses seviyesi: {}%".format(volume))

    @commands.command()
    async def stop(self, ctx):
        """Ses çalmayı durdurur ve ses kanalından ayrılır."""

        await ctx.voice_client.disconnect()

    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Ses kanalında değilsiniz.")
                raise commands.CommandError("Komudu uygulayan kişi ses kanalında değil.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

@bot.command()
async def add(ctx, left: int, right: int):
    """Toplama yapar."""
    await ctx.send(left + right)

@bot.command()
async def merhaba(ctx):
    """Merhaba der"""
    await ctx.send('Merhaba!')
    
@bot.command()
async def cezeri(ctx):
    """Cezeri'yi tanıtır."""
    await ctx.send('Merhaba, Cezeri Software sitesine https://cezeri.software linki ile ulaşabilirsin.\nDiscord sunucumuza katılmak için: https://discord.gg/huPGn6j')

@bot.command()
async def dov(ctx):
    """Döver."""
    await ctx.send('DÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖÖV!')


@bot.command()
async def joined(ctx, member: discord.Member):
    """Birisinin ne zaman sunucuya girdiğini bildirir."""
    await ctx.send('{0.name} şu tarihte katıldı: {0.joined_at}'.format(member))

bot.add_cog(Music(bot))
bot.run('your token here')
