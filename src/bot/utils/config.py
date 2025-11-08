import os
import logging
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management with validation"""
    
    # Discord
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
    BOT_STATUS = os.getenv('BOT_STATUS', 'online')
    BOT_ACTIVITY = os.getenv('BOT_ACTIVITY', 'Monitoring your server')
    
    # Database
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB = os.getenv('MONGO_DB', 'discord_bot')
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    
    # Web
    WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
    WEB_PORT = int(os.getenv('WEB_PORT', '5000'))
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Security
    ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    RATE_LIMIT = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
    
    # Ticket System
    TICKET_CATEGORY = int(os.getenv('TICKET_CATEGORY', '0'))
    SUPPORT_ROLE = int(os.getenv('SUPPORT_ROLE', '0'))
    MM_SUPPORT_ROLE = int(os.getenv('MM_SUPPORT_ROLE', '0'))
    CLIENT_ROLE = int(os.getenv('CLIENT_ROLE', '0'))
    ORDERLIST_CHANNEL = int(os.getenv('ORDERLIST_CHANNEL', '0'))
    ORDERLOGS_CHANNEL = int(os.getenv('ORDERLOGS_CHANNEL', '0'))
    
    # Vouch System
    ALLOWED_CHANNEL_IDS = [int(x.strip()) for x in os.getenv('ALLOWED_CHANNEL_IDS', '').split(',') if x.strip()]
    VOUCH_COOLDOWN_SECONDS = int(os.getenv('VOUCH_COOLDOWN_SECONDS', '600'))
    VOUCH_LOG_CHANNEL = int(os.getenv('VOUCH_LOG_CHANNEL', '0'))
    
    # APIs
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Emojis
    EMOJIS = {
        "loading": os.getenv('EMOJI_LOADING', '⏳'),
        "typing": os.getenv('EMOJI_TYPING', '⌨️'),
        "verify": os.getenv('EMOJI_VERIFY', '✅'),
        "alert": os.getenv('EMOJI_ALERT', '⚠️'),
        "dot": os.getenv('EMOJI_DOT', '•'),
        "wrong": os.getenv('EMOJI_WRONG', '❌'),
        "warning": os.getenv('EMOJI_WARNING', '⚠️'),
        "cart": os.getenv('EMOJI_CART', '🛒'),
        "correct": os.getenv('EMOJI_CORRECT', '✅'),
        "pin": os.getenv('EMOJI_PIN', '📌')
    }
    
    # Staff Payments
    STAFF_PAYMENTS = json.loads(os.getenv('STAFF_PAYMENTS', '{}'))
    
    # Paths
    DATA_PATH = os.path.join(os.path.dirname(__file__), '../../data')
    LOG_PATH = os.path.join(os.path.dirname(__file__), '../../logs')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = ['DISCORD_TOKEN', 'SECRET_KEY']
        missing = [var for var in required if not getattr(cls, var)]
        
        if missing:
            logging.error(f"Missing required environment variables: {missing}")
            return False
        
        # Create directories
        os.makedirs(cls.DATA_PATH, exist_ok=True)
        os.makedirs(cls.LOG_PATH, exist_ok=True)
        
        return True

# Global config instance
config = Config()