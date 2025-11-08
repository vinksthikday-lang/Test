import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio

class Music(commands.Cog):
    """Music system for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        
        # YouTube DL configuration
        self.ytdl_format_options = {
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
            'source_address': '0.0.0.0'
        }
        
        self.ffmpeg_options = {
            'options': '-vn'
        }
        
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)
    
    @app_commands.command(name="play", description="Play music from YouTube")
    @app_commands.describe(query="Song name or YouTube URL")
    async def play(self, interaction: discord.Interaction, query: str):
        """Play music command"""
        
        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ You need to be in a voice channel!",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            voice_channel = interaction.user.voice.channel
            
            # Connect to voice channel
            if interaction.guild.voice_client is None:
                await voice_channel.connect()
            elif interaction.guild.voice_client.channel != voice_channel:
                await interaction.guild.voice_client.move_to(voice_channel)
            
            # Extract video info
            data = await self.bot.loop.run_in_executor(
                None, lambda: self.ytdl.extract_info(query, download=False)
            )
            
            if 'entries' in data:
                data = data['entries'][0]
            
            # Play audio
            source = discord.FFmpegPCMAudio(data['url'], **self.ffmpeg_options)
            interaction.guild.voice_client.play(source)
            
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"[{data['title']}]({data['webpage_url']})",
                color=0x00ff00
            )
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error playing music: {str(e)}")
    
    @app_commands.command(name="stop", description="Stop the music")
    async def stop(self, interaction: discord.Interaction):
        """Stop music command"""
        
        if interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("⏹️ Music stopped.")
        else:
            await interaction.response.send_message("❌ Not playing any music.")
    
    @app_commands.command(name="disconnect", description="Disconnect the bot from voice")
    async def disconnect(self, interaction: discord.Interaction):
        """Disconnect from voice command"""
        
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("🔌 Disconnected from voice channel.")
        else:
            await interaction.response.send_message("❌ Not connected to any voice channel.")

async def setup(bot):
    await bot.add_cog(Music(bot))