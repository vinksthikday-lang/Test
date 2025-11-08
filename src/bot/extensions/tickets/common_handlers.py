import discord
from discord.ext import commands
from discord import ui

from ...utils.config import config

class CommonTicketHandlers:
    """Common handlers for both shop and midman tickets"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_common_interactions(self, interaction: discord.Interaction) -> bool:
        """Handle common ticket interactions"""
        if not interaction.data or 'custom_id' not in interaction.data:
            return False
            
        custom_id = interaction.data['custom_id']
        
        # Payment button handler
        if custom_id.startswith('pay_button_'):
            await self.handle_payment_button(interaction, custom_id)
            return True
            
        # Close ticket handler
        elif custom_id.startswith('close_ticket_'):
            await self.handle_close_ticket(interaction, custom_id)
            return True
            
        return False
        
    async def handle_payment_button(self, interaction: discord.Interaction, custom_id: str):
        """Handle payment buttons"""
        parts = custom_id.replace('pay_button_', '').split('_')
        if len(parts) < 3:
            await interaction.response.send_message(
                f"{config.EMOJIS['warning']} Invalid payment button.",
                ephemeral=True
            )
            return
            
        ticket_id, staff_name, amount = parts[0], parts[1], parts[2]
        
        # Get staff details
        staff = config.STAFF_PAYMENTS.get(staff_name)
        if not staff:
            await interaction.response.send_message(
                f"{config.EMOJIS['warning']} Staff payment details not found.",
                ephemeral=True
            )
            return
            
        # Check if user is staff (for staff view) or customer (for payment details)
        is_staff = any(role.id in [config.SUPPORT_ROLE, config.MM_SUPPORT_ROLE] 
                      for role in interaction.user.roles)
        
        if is_staff:
            # Staff confirming payment received
            embed = discord.Embed(
                title="Payment Received?",
                description="Has the payment been received?",
                color=0x00ff00
            )
            
            yes_button = discord.ui.Button(
                custom_id=f"payment_yes_{ticket_id}",
                label="Yes",
                style=discord.ButtonStyle.success,
                emoji=config.EMOJIS["verify"]
            )
            
            view = discord.ui.View()
            view.add_item(yes_button)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        else:
            # Customer viewing payment details
            payment_details = f"Number: {staff['number']}\nGCash Name: {staff['gcash_name']}"
            
            embed = discord.Embed(
                title="Payment Details",
                description=payment_details,
                color=0x00ff00
            )
            
            if staff.get('qr_code'):
                embed.set_image(url=staff['qr_code'])
                
            embed.set_footer(text="Send receipt after payment")
            
            copy_button = discord.ui.Button(
                custom_id=f"copy_number_{ticket_id}",
                label="Copy Number",
                style=discord.ButtonStyle.primary
            )
            
            qr_button = discord.ui.Button(
                custom_id=f"qr_code_{ticket_id}",
                label="View QR Code",
                style=discord.ButtonStyle.secondary,
                disabled=not staff.get('qr_code')
            )
            
            view = discord.ui.View()
            view.add_item(copy_button)
            view.add_item(qr_button)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
    async def handle_close_ticket(self, interaction: discord.Interaction, custom_id: str):
        """Handle ticket closing"""
        ticket_id = custom_id.replace('close_ticket_', '')
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get ticket from database
            ticket = await self.bot.ticket_manager.get_ticket(ticket_id)
            
            if not ticket:
                await interaction.followup.send(
                    f"{config.EMOJIS['warning']} Ticket not found.",
                    ephemeral=True
                )
                return
            
            # Delete channel and ticket
            channel = interaction.guild.get_channel(ticket["channelId"])
            if channel:
                await channel.delete()
            
            await self.bot.ticket_manager.delete_ticket(ticket_id)
            
            await interaction.followup.send(
                f"{config.EMOJIS['verify']} Ticket closed successfully.",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"{config.EMOJIS['warning']} Failed to close ticket: {str(e)}",
                ephemeral=True
            )