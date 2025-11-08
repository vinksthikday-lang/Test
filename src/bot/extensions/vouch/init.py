import discord
from discord.ext import commands

from .commands import VouchCommands

async def setup(bot):
    """Setup the vouch extension"""
    await bot.add_cog(VouchCommands(bot))