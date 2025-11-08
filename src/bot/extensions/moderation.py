import discord
from discord.ext import commands
from discord import app_commands
import asyncio

from ..utils.config import config

class Moderation(commands.Cog):
    """Moderation commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(member="Member to kick", reason="Reason for kicking")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Kick member command"""
        
        await interaction.response.defer()
        
        try:
            await member.kick(reason=reason)
            
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"{member.mention} has been kicked.",
                color=0xffa500
            )
            embed.add_field(name="Reason", value=reason)
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to kick that member.")
    
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.describe(member="Member to ban", reason="Reason for banning")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Ban member command"""
        
        await interaction.response.defer()
        
        try:
            await member.ban(reason=reason)
            
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{member.mention} has been banned.",
                color=0xff0000
            )
            embed.add_field(name="Reason", value=reason)
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to ban that member.")
    
    @app_commands.command(name="clear", description="Clear messages from a channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to clear (max 100)")
    async def clear(self, interaction: discord.Interaction, amount: int = 5):
        """Clear messages command"""
        
        if amount > 100:
            await interaction.response.send_message("❌ Cannot delete more than 100 messages at once.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            deleted = await interaction.channel.purge(limit=amount + 1)
            await interaction.followup.send(f"🗑️ Deleted {len(deleted) - 1} messages.", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to delete messages: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))