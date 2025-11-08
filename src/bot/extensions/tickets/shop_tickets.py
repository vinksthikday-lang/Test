import discord
from discord.ext import commands
from discord import app_commands, ui
from datetime import datetime
import random

from ...utils.config import config
from ...models.ticket_models import Ticket

class ShopTicketModal(ui.Modal, title='Create Support Ticket'):
    """Modal for creating shop tickets"""
    
    category = ui.TextInput(
        label='Category (e.g., Product, Service)',
        placeholder='Enter category...',
        max_length=50,
        required=True
    )
    
    order = ui.TextInput(
        label='Order Details (Order ID/Description)',
        placeholder='Describe your order...',
        max_length=100,
        required=True
    )
    
    quantity = ui.TextInput(
        label='Quantity',
        placeholder='Enter quantity...',
        max_length=10,
        required=True
    )
    
    notes = ui.TextInput(
        label='Additional Notes (Optional)',
        placeholder='Any additional information...',
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            quantity = int(self.quantity.value)
            if quantity <= 0:
                await interaction.followup.send(
                    f"{config.EMOJIS['warning']} Quantity must be a positive number.",
                    ephemeral=True
                )
                return
                
        except ValueError:
            await interaction.followup.send(
                f"{config.EMOJIS['warning']} Quantity must be a valid number.",
                ephemeral=True
            )
            return
        
        # Create ticket channel
        guild = interaction.guild
        member = interaction.user
        
        ticket_id = f"T-{random.randint(100000, 999999)}"
        
        # Create channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.get_role(config.SUPPORT_ROLE): discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, manage_messages=True
            )
        }
        
        category_channel = guild.get_channel(config.TICKET_CATEGORY)
        
        channel = await guild.create_text_channel(
            name=f"ticket-{member.display_name}",
            category=category_channel,
            overwrites=overwrites
        )
        
        # Create ticket in database
        ticket = Ticket(
            ticket_id=ticket_id,
            user_id=member.id,
            channel_id=channel.id,
            ticket_type="shop",
            category=self.category.value,
            order=self.order.value,
            quantity=quantity,
            notes=self.notes.value or "None provided"
        )
        
        await interaction.client.ticket_manager.create_ticket(ticket.to_dict())
        
        # Send initial ticket message
        embed = discord.Embed(
            title="Order Ticket",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name=f"{config.EMOJIS['dot']} Category :",
            value=self.category.value,
            inline=False
        )
        embed.add_field(
            name=f"{config.EMOJIS['dot']} Order :", 
            value=self.order.value,
            inline=False
        )
        embed.add_field(
            name=f"{config.EMOJIS['dot']} Quantity :",
            value=str(quantity),
            inline=False
        )
        embed.add_field(
            name=f"{config.EMOJIS['dot']} Additional Notes :",
            value=self.notes.value or "None provided",
            inline=False
        )
        embed.add_field(
            name=f"{config.EMOJIS['verify']} User :",
            value=member.mention,
            inline=False
        )
        embed.add_field(
            name=f"{config.EMOJIS['verify']} Created At :",
            value=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            inline=False
        )
        embed.set_footer(text="Is this your order?")
        
        # Create buttons
        yes_button = discord.ui.Button(
            custom_id=f"yes_button_{ticket_id}",
            label="Yes",
            style=discord.ButtonStyle.success,
            emoji=config.EMOJIS["verify"]
        )
        
        no_button = discord.ui.Button(
            custom_id=f"no_button_{ticket_id}",
            label="No", 
            style=discord.ButtonStyle.danger
        )
        
        view = discord.ui.View()
        view.add_item(yes_button)
        view.add_item(no_button)
        
        await channel.send(
            content=f"{member.mention} <@&{config.SUPPORT_ROLE}>",
            embed=embed,
            view=view
        )
        
        await interaction.followup.send(
            f"{config.EMOJIS['verify']} Ticket created: {channel.mention}",
            ephemeral=True
        )

class ShopTicketHandler:
    """Shop ticket interaction handler"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_shop_interaction(self, interaction: discord.Interaction) -> bool:
        """Handle shop ticket interactions"""
        if not interaction.data or 'custom_id' not in interaction.data:
            return False
            
        custom_id = interaction.data['custom_id']
        
        # Shop ticket creation button
        if custom_id == 'create_ticket':
            modal = ShopTicketModal()
            await interaction.response.send_modal(modal)
            return True
            
        # Handle other shop ticket interactions
        if custom_id.startswith('yes_button_'):
            await self.handle_yes_button(interaction, custom_id)
            return True
            
        elif custom_id.startswith('no_button_'):
            await self.handle_no_button(interaction, custom_id)
            return True
            
        return False
        
    async def handle_yes_button(self, interaction: discord.Interaction, custom_id: str):
        """Handle yes button in shop tickets"""
        ticket_id = custom_id.replace('yes_button_', '')
        
        # Disable original buttons
        original_view = discord.ui.View()
        for item in interaction.message.components[0].children:
            new_item = discord.ui.Button.from_component(item)
            new_item.disabled = True
            original_view.add_item(new_item)
            
        await interaction.message.edit(view=original_view)
        
        # Send agreement embed
        embed = discord.Embed(
            title="Please Confirm Your Order",
            description=f"Please click the 'Agree' button to confirm your order. {config.EMOJIS['warning']} Are you sure? No refunds will be issued after payment is sent.",
            color=0xFFA500
        )
        
        agree_button = discord.ui.Button(
            custom_id=f"agree_yes_{ticket_id}",
            label="Agree",
            style=discord.ButtonStyle.success,
            emoji=config.EMOJIS["verify"]
        )
        
        view = discord.ui.View()
        view.add_item(agree_button)
        
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"{config.EMOJIS['verify']} Order confirmation sent.",
            ephemeral=True
        )
        
    async def handle_no_button(self, interaction: discord.Interaction, custom_id: str):
        """Handle no button in shop tickets"""
        ticket_id = custom_id.replace('no_button_', '')
        
        try:
            # Delete ticket channel
            await interaction.channel.delete()
            await self.bot.ticket_manager.delete_ticket(ticket_id)
            
            await interaction.response.send_message(
                f"{config.EMOJIS['verify']} Ticket cancelled and deleted.",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"{config.EMOJIS['warning']} Failed to delete ticket: {str(e)}",
                ephemeral=True
            )