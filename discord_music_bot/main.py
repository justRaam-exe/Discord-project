import discord
from discord.ext import commands
import asyncio
import yt_dlp
from urllib.parse import urlparse

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='#', intents=intents)

guild_queue = {}

def clean_youtube_url(url):
    parsed = urlparse(url)
    return f"https://{parsed.netloc}{parsed.path}"

@bot.event
async def on_ready():
    print(f'✅ Bot berhasil login sebagai {bot.user.name}')

async def play_next(ctx):
    guild_id = ctx.guild.id
    if guild_queue.get(guild_id):
        url = guild_queue[guild_id].pop(0)
        await play_song(ctx, url)
    else:
        await asyncio.sleep(300)
        voice = ctx.voice_client
        if voice and not voice.is_playing():
            await voice.disconnect()
            await ctx.send("💤 Tidak ada lagu yang diputar, bot keluar otomatis.")

async def play_song(ctx, url):
    if "spotify.com" in url:
        await ctx.send("❌ Maaf, link Spotify tidak didukung. Gunakan link YouTube.")
        return

    url = clean_youtube_url(url)
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice is None:
        await ctx.send("❌ Bot belum masuk ke voice channel.")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            title = info.get('title', 'Tanpa Judul')

        def after_playing(error):
            fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"Error dalam play_next: {e}")

        voice.play(discord.FFmpegPCMAudio(audio_url, executable="ffmpeg"), after=after_playing)
        await ctx.send(f"🎶 Sekarang memutar: {title}")

    except Exception as e:
        await ctx.send(f"❌ Gagal memutar lagu: {str(e)}")
        print(f"Error saat play_song: {e}")

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"✅ Bot masuk ke voice channel: {channel}")
    else:
        await ctx.send("❌ Kamu harus join voice channel dulu.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bot keluar dari voice channel.")
    else:
        await ctx.send("❌ Bot tidak sedang berada di voice channel.")

@bot.command()
async def play(ctx, *, url):
    if ctx.voice_client is None:
        await ctx.invoke(bot.get_command('join'))

    guild_id = ctx.guild.id
    if guild_id not in guild_queue:
        guild_queue[guild_id] = []

    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        guild_queue[guild_id].append(url)
        await ctx.send("⏳ Lagu ditambahkan ke antrean.")
    else:
        await play_song(ctx, url)

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        guild_queue[ctx.guild.id] = []
        await ctx.send("⏹ Musik dihentikan dan antrean dikosongkan.")
    else:
        await ctx.send("❌ Tidak ada musik yang sedang diputar.")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ Musik dijeda.")
    else:
        await ctx.send("❌ Tidak ada musik yang sedang diputar.")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Musik dilanjutkan.")
    else:
        await ctx.send("❌ Musik tidak dalam keadaan dijeda.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Lagu dilewati.")
    else:
        await ctx.send("❌ Tidak ada lagu untuk dilewati.")

bot.run("ISI DENGAN TOKEN DISCORD ANDA")