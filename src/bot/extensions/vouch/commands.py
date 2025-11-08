import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from ...utils.config import config

class VouchCooldown:
    """Cooldown management for vouch commands"""
    
    def __init__(self):
        self.cooldowns = {}
    
    def is_on_cooldown(self, user_id: int, command: str, cooldown_seconds: int = 2) -> Optional[int]:
        """Check if user is on cooldown for a command"""
        if command not in self.cooldowns:
            self.cooldowns[command] = {}
            
        now = datetime.utcnow()
        user_cooldowns = self.cooldowns[command]
        
        if user_id in user_cooldowns:
            expiration_time = user_cooldowns[user_id] + timedelta(seconds=cooldown_seconds)
            if now < expiration_time:
                return int((expiration_time - now).total_seconds())
        
        user_cooldowns[user_id] = now
        return None

class VouchCommands(commands.Cog):
    """Vouch system commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.cooldown = VouchCooldown()
        
    def is_owner(self, user_id: int) -> bool:
        """Check if user is bot owner"""
        return user_id in config.ADMIN_IDS
    
    def is_allowed_channel(self, channel_id: int) -> bool:
        """Check if channel is allowed for vouch commands"""
        return channel_id in config.ALLOWED_CHANNEL_IDS
    
    # === Vouch Command ===
    
    @app_commands.command(name="vouch", description="Vouch for a user with proof")
    @app_commands.describe(
        user="The user to vouch for",
        message="Your vouch message (optional)"
    )
    async def vouch(self, interaction: discord.Interaction, user: discord.User, message: str = None):
        """Vouch for a user command"""
        
        # Check permissions and channel
        if not self.is_allowed_channel(interaction.channel.id):
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Wrong Channel",
                description=f"{config.EMOJIS['alert']} Vouch commands are only allowed in specific channels.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check cooldown for non-owners
        if not self.is_owner(interaction.user.id):
            cooldown_remaining = self.cooldown.is_on_cooldown(interaction.user.id, "vouch")
            if cooldown_remaining:
                embed = discord.Embed(
                    title=f"{config.EMOJIS['wrong']} Cooldown",
                    description=f"{config.EMOJIS['alert']} Please wait **{cooldown_remaining} seconds** before using this command again.",
                    color=0xFF0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        await interaction.response.defer()
        
        # Validate input
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Self-Vouch Denied",
                description=f"{config.EMOJIS['alert']} You cannot vouch for yourself.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        vouch_message = message or "No comment"
        if len(vouch_message) > 500:
            vouch_message = vouch_message[:500]
        
        # Check for attachments (proof)
        if not interaction.message.attachments and not self.is_owner(interaction.user.id):
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Missing Proof",
                description=f"{config.EMOJIS['alert']} Please attach a screenshot or proof to verify the vouch.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Check cooldown for specific user
        if not self.is_owner(interaction.user.id):
            recent_vouch = await self.bot.vouch_manager.get_recent_vouch(user.id, interaction.user.id)
            if recent_vouch:
                time_since_last = (interaction.created_at - recent_vouch["timestamp"]).total_seconds()
                if time_since_last < config.VOUCH_COOLDOWN_SECONDS:
                    remaining = config.VOUCH_COOLDOWN_SECONDS - int(time_since_last)
                    minutes = remaining // 60
                    seconds = remaining % 60
                    embed = discord.Embed(
                        title=f"{config.EMOJIS['wrong']} Cooldown",
                        description=f"{config.EMOJIS['alert']} Wait **{minutes}m {seconds}s** before vouching for this user again.",
                        color=0xFF0000
                    )
                    await interaction.followup.send(embed=embed)
                    return
        
        # Create vouch
        try:
            vouch_data = await self.bot.vouch_manager.create_vouch(user.id, interaction.user.id, vouch_message)
            vouch_count = await self.bot.vouch_manager.get_vouch_count(user.id)
            
            embed = discord.Embed(
                title=f"{config.EMOJIS['correct']} Vouch Recorded",
                description=f"{config.EMOJIS['dot']} Successfully vouched for **{user.display_name}**",
                color=0x00FF00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['pin']} From",
                value=interaction.user.mention,
                inline=True
            )
            embed.add_field(
                name=f"{config.EMOJIS['pin']} To", 
                value=user.mention,
                inline=True
            )
            embed.add_field(
                name=f"{config.EMOJIS['dot']} Vouch Count",
                value="+1",
                inline=True
            )
            embed.add_field(
                name=f"{config.EMOJIS['alert']} Comment",
                value=vouch_message[:100] + "..." if len(vouch_message) > 100 else vouch_message,
                inline=False
            )
            embed.add_field(
                name=f"{config.EMOJIS['dot']} Vouch ID",
                value=f"`{vouch_data['vouchId']}`",
                inline=True
            )
            embed.add_field(
                name=f"{config.EMOJIS['dot']} When",
                value=f"<t:{int(datetime.utcnow().timestamp())}:R>",
                inline=True
            )
            embed.set_footer(text=f"Thank you for vouching! | Vouch ID: {vouch_data['vouchId']}")
            
            await interaction.followup.send(embed=embed)
            
            # Log to log channel
            log_channel = self.bot.get_channel(config.VOUCH_LOG_CHANNEL)
            if log_channel:
                log_embed = discord.Embed(
                    title=f"{config.EMOJIS['pin']} Vouch Success",
                    description=f"{config.EMOJIS['dot']} Vouch for {user.display_name} by {interaction.user.display_name}",
                    color=0x00FF00
                )
                log_embed.add_field(name="Comment", value=vouch_message)
                log_embed.add_field(name="Vouch ID", value=f"`{vouch_data['vouchId']}`")
                
                # Add attachment if exists
                if interaction.message.attachments:
                    log_embed.set_image(url=interaction.message.attachments[0].url)
                
                await log_channel.send(embed=log_embed)
                
        except Exception as e:
            print(f"Vouch creation error: {e}")
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Save Failed",
                description=f"{config.EMOJIS['alert']} Failed to save vouch. Contact the bot owner.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
    
    # === Vouches Command ===
    
    @app_commands.command(name="vouches", description="Check vouch count for a user")
    @app_commands.describe(user="The user to check vouches for (optional)")
    async def vouches(self, interaction: discord.Interaction, user: discord.User = None):
        """Check vouch count command"""
        
        if not user:
            user = interaction.user
        
        await interaction.response.defer()
        
        try:
            vouches = await self.bot.vouch_manager.get_user_vouches(user.id)
            vouch_count = len(vouches)
            
            if vouch_count == 0:
                embed = discord.Embed(
                    title=f"{config.EMOJIS['wrong']} No Vouches",
                    description=f"{config.EMOJIS['alert']} {user.display_name} has no vouches yet. Be the first to vouch!",
                    color=0xFF5252
                )
                embed.set_thumbnail(url=user.display_avatar.url)
                embed.set_footer(text=f"User ID: {user.id}")
                await interaction.followup.send(embed=embed)
                return
            
            latest_vouch = vouches[0]
            
            embed = discord.Embed(
                title=f"{config.EMOJIS['pin']} 📊 Vouch Summary",
                description=f"{config.EMOJIS['dot']} Vouch stats for **{user.display_name}**",
                color=0x2B7FBD
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            
            embed.add_field(
                name=f"{config.EMOJIS['dot']} Total Vouches",
                value=f"**{vouch_count}**",
                inline=True
            )
            embed.add_field(
                name=f"{config.EMOJIS['alert']} Account", 
                value=user.display_name,
                inline=True
            )
            embed.add_field(
                name=f"{config.EMOJIS['pin']} User ID",
                value=f"`{user.id}`",
                inline=True
            )
            embed.add_field(
                name=f"{config.EMOJIS['correct']} Last Vouched",
                value=f"<t:{int(latest_vouch['timestamp'].timestamp())}:R>",
                inline=True
            )
            embed.add_field(
                name=f"{config.EMOJIS['dot']} Last Comment",
                value=f"`{latest_vouch['message'][:80]}{'...' if len(latest_vouch['message']) > 80 else ''}`",
                inline=False
            )
            
            embed.set_footer(text=f"Use /vouchhistory @{user.name} for full history")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"Vouches fetch error: {e}")
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Fetch Failed",
                description=f"{config.EMOJIS['alert']} Could not retrieve vouches. Try again later.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
    
    # === Vouch Leaderboard Command ===
    
    @app_commands.command(name="vouchleaderboard", description="View vouch leaderboard")
    @app_commands.describe(page="Page number (optional)")
    async def vouchleaderboard(self, interaction: discord.Interaction, page: int = 1):
        """Vouch leaderboard command"""
        
        await interaction.response.defer()
        
        try:
            leaderboard = await self.bot.vouch_manager.get_leaderboard(limit=50)
            
            if not leaderboard:
                embed = discord.Embed(
                    title=f"{config.EMOJIS['wrong']} Empty",
                    description=f"{config.EMOJIS['alert']} No vouches found.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed)
                return
            
            items_per_page = 10
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            embed = discord.Embed(
                title=f"{config.EMOJIS['pin']} 🏆 Vouch Leaderboard",
                description=f"{config.EMOJIS['dot']} Top **{len(leaderboard)}** most vouched users\nPage {page}/{(len(leaderboard) + items_per_page - 1) // items_per_page}",
                color=0xF1C40F
            )
            
            for i in range(start_idx, min(end_idx, len(leaderboard))):
                item = leaderboard[i]
                user_obj = await self.bot.fetch_user(int(item["_id"]))
                username = user_obj.display_name if user_obj else "Unknown"
                
                embed.add_field(
                    name=f"#{i + 1}",
                    value=f"**{username}** — {item['count']} vouches",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"Leaderboard error: {e}")
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Error",
                description=f"{config.EMOJIS['alert']} Could not load leaderboard.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
    
    # === Vouch Stats Command ===
    
    @app_commands.command(name="vouchstats", description="View vouch statistics")
    async def vouchstats(self, interaction: discord.Interaction):
        """Vouch statistics command"""
        
        await interaction.response.defer()
        
        try:
            stats = await self.bot.vouch_manager.get_stats()
            
            embed = discord.Embed(
                title=f"{config.EMOJIS['pin']} 📊 System Statistics",
                description=f"{config.EMOJIS['dot']} Global vouch statistics",
                color=0x9B59B6
            )
            
            embed.add_field(
                name=f"{config.EMOJIS['dot']} Total Vouches",
                value=f"**{stats['total']}**",
                inline=True
            )
            
            # Top giver
            top_giver_text = "None"
            if stats['top_giver']:
                giver_user = await self.bot.fetch_user(int(stats['top_giver']['_id']))
                if giver_user:
                    top_giver_text = f"{giver_user.mention} with **{stats['top_giver']['count']}**"
            
            embed.add_field(
                name=f"{config.EMOJIS['alert']} Top Giver",
                value=top_giver_text,
                inline=True
            )
            
            # Top receiver
            top_receiver_text = "None"
            if stats['top_receiver']:
                receiver_user = await self.bot.fetch_user(int(stats['top_receiver']['_id']))
                if receiver_user:
                    top_receiver_text = f"{receiver_user.mention} with **{stats['top_receiver']['count']}**"
            
            embed.add_field(
                name=f"{config.EMOJIS['pin']} Top Receiver", 
                value=top_receiver_text,
                inline=True
            )
            
            embed.set_footer(text="Stats as of now")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"Stats error: {e}")
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Error",
                description=f"{config.EMOJIS['alert']} Could not fetch stats.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
    
    # === Admin Commands ===
    
    # Vouch Give (Admin)
    @app_commands.command(name="vouchgive", description="[ADMIN] Give vouches to a user")
    @app_commands.describe(
        user="The user to give vouches to",
        count="Number of vouches to give",
        message="Vouch message (optional)"
    )
    async def vouchgive(self, interaction: discord.Interaction, user: discord.User, count: int, message: str = "Bulk vouch"):
        """Admin vouch give command"""
        
        if not self.is_owner(interaction.user.id):
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Permission Denied",
                description=f"{config.EMOJIS['alert']} Only bot owners can use this command.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Validate count
        if count < 1 or count > 1000:
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Invalid Count",
                description=f"{config.EMOJIS['alert']} Vouch count must be 1–1000.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
            return
        
        try:
            created_count = await self.bot.vouch_manager.bulk_create_vouches(user.id, interaction.user.id, count, message)
            total_count = await self.bot.vouch_manager.get_vouch_count(user.id)
            
            embed = discord.Embed(
                title=f"{config.EMOJIS['correct']} Vouches Added",
                description=f"{config.EMOJIS['dot']} Added **{created_count}** vouches to {user.display_name}",
                color=0x43B581
            )
            embed.add_field(
                name=f"{config.EMOJIS['pin']} Total Now",
                value=f"**{total_count}**",
                inline=True
            )
            embed.add_field(
                name=f"{config.EMOJIS['alert']} Comment", 
                value=message,
                inline=False
            )
            embed.set_footer(text=f"Action by: {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"Vouch give error: {e}")
            embed = discord.Embed(
                title=f"{config.EMOJIS['wrong']} Failed",
                description=f"{config.EMOJIS['alert']} Could not add vouches.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)