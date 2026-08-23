import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import yt_dlp
import asyncio

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Your Music Voice Channel ID
VOICE_CHANNEL_ID = 1522886838438596640

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")

    # Automatically join the Music Voice Channel
    channel = bot.get_channel(VOICE_CHANNEL_ID)

    if channel is None:
        print("Voice channel not found!")
        return

    if not isinstance(channel, discord.VoiceChannel):
        print("The provided ID is not a voice channel!")
        return

    voice_client = discord.utils.get(
        bot.voice_clients,
        guild=channel.guild
    )

    if voice_client is None:
        try:
            await channel.connect()
            print(f"Auto joined voice channel: {channel.name}")
        except Exception as e:
            print(f"Auto join error: {e}")

    else:
        if voice_client.channel != channel:
            await voice_client.move_to(channel)


@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")


@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You need to join a voice channel first!")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await channel.connect()
        await ctx.send(f"Joined voice channel: {channel.name}")
    else:
        await ctx.voice_client.move_to(channel)
        await ctx.send(f"Moved to voice channel: {channel.name}")


@bot.command()
async def play(ctx, url):
    if ctx.author.voice is None:
        await ctx.send("You need to join a voice channel first!")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await channel.connect()

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["web_safari"]
            }
        },
    }

    await ctx.send("Downloading music... 🎵")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if "entries" in info:
                info = info["entries"][0]

            audio_url = info["url"]
            title = info.get("title", "Unknown Song")

    except Exception as e:
        await ctx.send(f"Error downloading music: {e}")
        return

    voice_client = ctx.voice_client

    if voice_client.is_playing():
        voice_client.stop()

    ffmpeg_options = {
        "before_options": (
            "-reconnect 1 "
            "-reconnect_streamed 1 "
            "-reconnect_delay_max 5"
        ),
        "options": "-vn"
    }

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(
            audio_url,
            **ffmpeg_options
        ),
        volume=1.0
    )

    voice_client.play(source)

    await ctx.send(f"Now playing: {title} 🎶")


@bot.command()
async def volume(ctx, level: int):
    voice_client = ctx.voice_client

    if voice_client is None:
        await ctx.send("I'm not connected to a voice channel!")
        return

    if voice_client.source is None:
        await ctx.send("No music is currently playing!")
        return

    if not 0 <= level <= 100:
        await ctx.send("Volume must be between 0 and 100.")
        return

    if isinstance(voice_client.source, discord.PCMVolumeTransformer):
        voice_client.source.volume = level / 100
        await ctx.send(f"Volume set to {level}% 🔊")
    else:
        await ctx.send("Volume control is not available for the current audio.")


@bot.command()
async def stop(ctx):
    if ctx.voice_client is None:
        await ctx.send("I'm not connected to a voice channel!")
        return

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Music stopped! ⏹️")
    else:
        await ctx.send("No music is currently playing!")


@bot.command()
async def leave(ctx):
    if ctx.voice_client is None:
        await ctx.send("I'm not connected to a voice channel!")
        return

    await ctx.voice_client.disconnect()
    await ctx.send("Left the voice channel! 👋")


bot.run(TOKEN)
