import discord
from discord.ext import commands
from discord import app_commands, ui
from datetime import datetime
import random
import re

from ...utils.config import config
from ...models.ticket_models import Ticket

class MidmanTicketModal(ui.Modal, title='Create Midman Ticket'):
    """Modal for creating midman tickets"""
    
    transaction = ui.TextInput(
        label='What is the transaction?',
        placeholder='Describe the transaction...',
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True
    )
    
    amount = ui.TextInput(
        label='How much is the transaction amount?',
        placeholder='Enter amount...',
        max_length=10,
        required=True
    )
    
    transact_partner = ui.TextInput(
        label='Transact Partner (Username/ID/Mention)',
        placeholder='Enter partner username, ID, or mention...',
        max_length=100,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            amount = float(self.amount.value)
            if amount <= 0:
                await interaction.followup.send(
                    f"{config.EMOJIS['warning']} Transaction amount must be a valid positive number.",
                    ephemeral=True
                )
                return
                
        except ValueError:
            await interaction.followup.send(
                f"{config.EMOJIS['warning']} Transaction amount must be a valid number.",
                ephemeral=True
            )
            return
        
        # Find transact partner
        transact_user = await self.find_member(interaction.guild, self.transact_partner.value)
        manual_add_required = False
        
        if not transact_user:
            manual_add_required = True
            
        # Create ticket
        ticket_id = f"MM-{random.randint(100000, 999999)}"
        member = interaction.user
        
        # Create channel with permissions
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.get_role(config.MM_SUPPORT_ROLE): discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, manage_messages=True
            )
        }
        
        # Add transact partner if found
        if transact_user:
            overwrites[transact_user] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )
            
        category_channel = interaction.guild.get_channel(config.TICKET_CATEGORY)
        
        channel = await interaction.guild.create_text_channel(
            name=f"mm-ticket-{member.display_name}",
            category=category_channel,
            overwrites=overwrites
        )
        
        # Create ticket in database
        ticket = Ticket(
            ticket_id=ticket_id,
            user_id=member.id,
            channel_id=channel.id,
            ticket_type="mm",
            category="Midman",
            order=self.transaction.value,
            quantity=1,
            notes="None provided",
            amount=amount,
            transact_partner=transact_user.id if transact_user else None
        )
        
        await interaction.client.ticket_manager.create_ticket(ticket.to_dict())
        
        # Send initial message
        embed = discord.Embed(
            title="Midman Ticket",
            color=0x0099ff
        )
        
        embed.add_field(
            name=f"{config.EMOJIS['dot']} Transaction :",
            value=self.transaction.value,
            inline=False
        )
        embed.add_field(
            name=f"{config.EMOJIS['dot']} Amount :",
            value=f"₱{amount}",
            inline=False
        )
        embed.add_field(
            name=f"{config.EMOJIS['dot']} Transact Partner :",
            value=transact_user.mention if transact_user else "Not added yet",
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
        embed.set_footer(text="Is this your Transact Partner?")
        
        content = f"{member.mention}"
        if transact_user:
            content += f" {transact_user.mention}"
        content += f" <@&{config.MM_SUPPORT_ROLE}>"
        
        await channel.send(content=content, embed=embed)
        
        # Notify if manual add required
        if manual_add_required:
            await channel.send(
                f"{config.EMOJIS['warning']} Can't add the transact partner. Let the Midman handler add it manually using /ticket add."
            )
        elif transact_user:
            await channel.send(
                f"{config.EMOJIS['verify']} Transact partner {transact_user.mention} added to the ticket."
            )
            
        # Send click button for payment
        click_button = discord.ui.Button(
            custom_id=f"click_button_{ticket_id}",
            label="Click",
            style=discord.ButtonStyle.primary,
            emoji=config.EMOJIS["verify"]
        )
        
        view = discord.ui.View()
        view.add_item(click_button)
        
        await channel.send(
            content=f"<@&{config.MM_SUPPORT_ROLE}> Please click the Button to send your payment details.",
            view=view
        )
        
        await interaction.followup.send(
            f"{config.EMOJIS['verify']} MM ticket created: {channel.mention}",
            ephemeral=True
        )
    
    async def find_member(self, guild, search_term: str) -> discord.Member:
        """Find member by mention, ID, or username"""
        # Check if mention
        if search_term.startswith('<@') and search_term.endswith('>'):
            user_id = search_term.replace('<@', '').replace('>', '').replace('!', '')
            try:
                return await guild.fetch_member(int(user_id))
            except:
                return None
                
        # Check if user ID
        if re.match(r'^\d+$', search_term):
            try:
                return await guild.fetch_member(int(search_term))
            except:
                return None
                
        # Search by username
        search_term = search_term.lower().strip()
        async for member in guild.fetch_members(limit=None):
            if (member.name.lower() == search_term or 
                member.display_name.lower() == search_term or
                str(member).lower() == search_term):
                return member
                
        # Fuzzy search
        async for member in guild.fetch_members(limit=None):
            if (search_term in member.name.lower() or 
                search_term in member.display_name.lower()):
                return member
                
        return None

class MidmanStaffModal(ui.Modal, title='Midman Payment Details'):
    """Modal for midman staff payment details"""
    
    def __init__(self, ticket_id: str):
        super().__init__()
        self.ticket_id = ticket_id
        
    staff_name = ui.TextInput(
        label='Staff Name ( Koala | Csy | Saz | Dio | Ard )',
        placeholder='Enter your staff name...',
        max_length=50,
        required=True
    )
    
    staff_amount = ui.TextInput(
        label='Amount to Pay',
        placeholder='Enter amount...',
        max_length=10,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Validate staff name
        if self.staff_name.value.strip() not in config.STAFF_PAYMENTS:
            await interaction.followup.send(
                f"{config.EMOJIS['warning']} Staff name not found in configuration.",
                ephemeral=True
            )
            return
            
        try:
            amount = float(self.staff_amount.value)
            if amount <= 0:
                await interaction.followup.send(
                    f"{config.EMOJIS['warning']} Amount must be a valid positive number.",
                    ephemeral=True
                )
                return
                
        except ValueError:
            await interaction.followup.send(
                f"{config.EMOJIS['warning']} Amount must be a valid number.",
                ephemeral=True
            )
            return
            
        # Get ticket and update
        ticket = await interaction.client.ticket_manager.get_ticket(self.ticket_id)
        if ticket:
            await interaction.client.ticket_manager.update_ticket(
                self.ticket_id,
                {
                    "staffName": self.staff_name.value.strip(),
                    "amount": amount
                }
            )
            
            # Send payment embed to ticket channel
            channel = interaction.guild.get_channel(ticket["channelId"])
            if channel:
                staff = config.STAFF_PAYMENTS[self.staff_name.value.strip()]
                
                embed = discord.Embed(
                    title="MIDMAN PAYMENT",
                    description="Please click the 'Pay' button to pay your midman order",
                    color=0x00ff00
                )
                
                if staff.get("qr_code"):
                    embed.set_image(url=staff["qr_code"])
                
                pay_button = discord.ui.Button(
                    custom_id=f"pay_button_{self.ticket_id}_{self.staff_name.value.strip()}_{amount}",
                    label=f"Pay {amount}",
                    style=discord.ButtonStyle.success,
                    emoji=config.EMOJIS["verify"]
                )
                
                view = discord.ui.View()
                view.add_item(pay_button)
                
                content = f"<@{ticket['userId']}>"
                if ticket.get("transactPartner"):
                    content += f" <@{ticket['transactPartner']}>"
                
                await channel.send(
                    content=content,
                    embed=embed,
                    view=view
                )
        
        await interaction.followup.send(
            f"{config.EMOJIS['verify']} Payment details sent successfully!",
            ephemeral=True
        )

class MidmanTicketHandler:
    """Midman ticket interaction handler"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def handle_midman_interaction(self, interaction: discord.Interaction) -> bool:
        """Handle midman ticket interactions"""
        if not interaction.data or 'custom_id' not in interaction.data:
            return False
            
        custom_id = interaction.data['custom_id']
        
        # Midman ticket creation button
        if custom_id == 'create_mm_ticket':
            modal = MidmanTicketModal()
            await interaction.response.send_modal(modal)
            return True
            
        # Handle click button for payment details
        elif custom_id.startswith('click_button_'):
            await self.handle_click_button(interaction, custom_id)
            return True
            
        return False
        
    async def handle_click_button(self, interaction: discord.Interaction, custom_id: str):
        """Handle click button in midman tickets"""
        ticket_id = custom_id.replace('click_button_', '')
        
        # Check if user is MM support
        if not any(role.id == config.MM_SUPPORT_ROLE for role in interaction.user.roles):
            await interaction.response.send_message(
                f"{config.EMOJIS['warning']} Only Midman handlers can proceed with payment details.",
                ephemeral=True
            )
            return
            
        # Send staff modal for payment details
        modal = MidmanStaffModal(ticket_id)
        await interaction.response.send_modal(modal)