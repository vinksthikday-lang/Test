import asyncio
import logging
import sys
import traceback
from datetime import datetime

import discord
from discord.ext import commands

from utils.config import config
from utils.security import security
from models.database import MongoDB, VouchManager, TicketManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{config.LOG_PATH}/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class AdvancedBot(commands.Bot):
    """Advanced Discord bot with extended functionality"""
    
    def __init__(self):
        intents = discord.Intents.all()
        intents.typing = False
        intents.delayed = False
        
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            max_messages=10000
        )
        
        self.start_time = datetime.utcnow()
        self.db = MongoDB(config.MONGO_URI, config.MONGO_DB)
        self.vouch_manager = VouchManager(self.db)
        self.ticket_manager = TicketManager(self.db)
        self.extensions_loaded = False
        
        # Statistics
        self.commands_used = 0
        self.messages_processed = 0
        
    async def get_prefix(self, message: discord.Message) -> str:
        """Get prefix for guild or default"""
        if not message.guild:
            return config.BOT_PREFIX
        return config.BOT_PREFIX
    
    async def setup_hook(self):
        """Called when bot is starting"""
        logger.info("Starting bot setup...")
        
        # Initialize database
        await self.db.initialize()
        logger.info("Database initialized")
        
        # Load extensions
        await self.load_extensions()
        
        # Start background tasks
        self.update_status.start()
        
        logger.info("Bot setup completed")
    
    async def load_extensions(self):
        """Load all bot extensions"""
        extensions = [
            'extensions.admin',
            'extensions.moderation',
            'extensions.security',
            'extensions.music',
            'extensions.economy',
            'extensions.utilities',
            'extensions.tickets',
            'extensions.vouch'
        ]
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
                traceback.print_exc()
        
        self.extensions_loaded = True
    
    @commands.dm_only()
    async def on_message(self, message):
        """Handle DMs"""
        if message.author.bot:
            return
            
        # Log DM for debugging
        logger.info(f"DM from {message.author}: {message.content}")
        
        # Process commands in DMs
        await self.process_commands(message)
    
    @tasks.loop(minutes=5)
    async def update_status(self):
        """Update bot status periodically"""
        activities = [
            discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers"),
            discord.Activity(type=discord.ActivityType.listening, name="/help"),
            discord.Activity(type=discord.ActivityType.playing, name="with security")
        ]
        
        if hasattr(self, 'status_index'):
            self.status_index = (self.status_index + 1) % len(activities)
        else:
            self.status_index = 0
            
        activity = activities[self.status_index]
        await self.change_presence(activity=activity)
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} is now online!')
        logger.info(f'Connected to {len(self.guilds)} guilds')
        logger.info(f'Bot ID: {self.user.id}')
    
    async def on_command(self, ctx):
        """Called when a command is executed"""
        self.commands_used += 1
        logger.info(f"Command used: {ctx.command} by {ctx.author} in {ctx.guild}")
    
    async def on_error(self, event_method: str, *args, **kwargs):
        """Global error handler"""
        logger.error(f"Error in {event_method}: {args} {kwargs}")
        traceback.print_exc()

async def main():
    """Main entry point"""
    if not config.validate():
        logger.error("Configuration validation failed. Exiting.")
        return
    
    bot = AdvancedBot()
    
    try:
        await bot.start(config.DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        traceback.print_exc()
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(main())