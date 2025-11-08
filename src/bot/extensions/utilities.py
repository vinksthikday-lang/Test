import discord
from discord.ext import commands
from discord import app_commands
import datetime
import platform

class Utilities(commands.Cog):
    """Utility commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="serverinfo", description="Display server information")
    async def serverinfo(self, interaction: discord.Interaction):
        """Server information command"""
        
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"🛠️ {guild.name}",
            color=0x00ff00,
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="📅 Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="🔢 Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="🚀 Boost Level", value=guild.premium_tier, inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="botinfo", description="Display bot information")
    async def botinfo(self, interaction: discord.Interaction):
        """Bot information command"""
        
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=0x7289da
        )
        
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py Version", value=discord.__version__, inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Uptime", value="Online", inline=True)
        embed.add_field(name="Developer", value="Your Name", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Display user information")
    @app_commands.describe(user="User to get information about (optional)")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        """User information command"""
        
        if not user:
            user = interaction.user
        
        embed = discord.Embed(
            title=f"👤 {user.display_name}",
            color=user.color
        )
        
        embed.add_field(name="Username", value=f"{user.name}#{user.discriminator}", inline=True)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name="Joined Server", value=user.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Top Role", value=user.top_role.mention, inline=True)
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
            
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilities(bot))