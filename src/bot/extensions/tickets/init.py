import discord
from discord.ext import commands
from discord import app_commands

from ...utils.config import config

class TicketSystem(commands.Cog):
    """Complete ticket system with shop and midman support"""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="setup", description="Sets up the ticket system in the current channel")
    @app_commands.default_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        """Setup ticket system command"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                f"{config.EMOJIS['wrong']} You need administrator permissions to use this command!",
                ephemeral=True
            )
            return
            
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="Service Status: Open",
            description=f"Order something or need a middleman? Open a ticket now {config.EMOJIS['alert']}",
            color=0x2bff00
        )
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1395695208511049798/1396755756920999999/dm4uz3-foekoe.gif")
        embed.set_footer(text="Koala Staff")
        
        ticket_button = discord.ui.Button(
            custom_id="create_ticket",
            label="Shop",
            style=discord.ButtonStyle.primary,
            emoji=config.EMOJIS["cart"]
        )
        
        mm_button = discord.ui.Button(
            custom_id="create_mm_ticket", 
            label="Midman",
            style=discord.ButtonStyle.secondary,
            emoji=config.EMOJIS["alert"]
        )
        
        view = discord.ui.View()
        view.add_item(ticket_button)
        view.add_item(mm_button)
        
        await interaction.channel.send(embed=embed, view=view)
        await interaction.followup.send(
            f"{config.EMOJIS['verify']} Ticket system successfully set up!",
            ephemeral=True
        )
    
    @app_commands.command(name="ticket", description="Manage tickets")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_manage(self, interaction: discord.Interaction, user: discord.Member):
        """Add user to ticket command"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Add permissions to current channel
            await interaction.channel.set_permissions(user, 
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
            
            await interaction.followup.send(
                f"{config.EMOJIS['verify']} Added {user.mention} to the ticket!",
                ephemeral=True
            )
            
            await interaction.channel.send(f"{user.mention} has been added to this ticket.")
            
        except Exception as e:
            await interaction.followup.send(
                f"{config.EMOJIS['warning']} Failed to add member: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))