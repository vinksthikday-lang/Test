import motor.motor_asyncio
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional

class MongoDB:
    """MongoDB database handler"""
    
    def __init__(self, connection_uri: str, db_name: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_uri)
        self.db = self.client[db_name]
        self.vouches = self.db.vouches
        self.tickets = self.db.tickets
        self.guilds = self.db.guilds
        self.users = self.db.users
        
    async def initialize(self):
        """Initialize database indexes"""
        # Vouches indexes
        await self.vouches.create_index("userId")
        await self.vouches.create_index("vouchedBy")
        await self.vouches.create_index("timestamp")
        await self.vouches.create_index("vouchId", unique=True)
        
        # Tickets indexes
        await self.tickets.create_index("ticketId", unique=True)
        await self.tickets.create_index("userId")
        await self.tickets.create_index("channelId")
        await self.tickets.create_index("status")
        
        # Guilds indexes
        await self.guilds.create_index("guildId", unique=True)
        
        # Users indexes
        await self.users.create_index("userId", unique=True)
    
    def generate_id(self) -> str:
        """Generate unique ID"""
        return str(uuid.uuid4())

class VouchManager:
    """Vouch system database operations"""
    
    def __init__(self, db: MongoDB):
        self.db = db
    
    async def create_vouch(self, user_id: int, vouched_by: int, message: str, points: int = 1) -> Dict[str, Any]:
        """Create a new vouch"""
        vouch_data = {
            "userId": str(user_id),
            "vouchedBy": str(vouched_by),
            "points": points,
            "message": message,
            "timestamp": datetime.utcnow(),
            "deleted": False,
            "vouchId": self.db.generate_id()
        }
        result = await self.db.vouches.insert_one(vouch_data)
        return vouch_data
    
    async def get_user_vouches(self, user_id: int, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """Get all vouches for a user"""
        query = {"userId": str(user_id)}
        if not include_deleted:
            query["deleted"] = False
            
        cursor = self.db.vouches.find(query).sort("timestamp", -1)
        return await cursor.to_list(length=None)
    
    async def get_vouch_count(self, user_id: int) -> int:
        """Get count of vouches for a user"""
        return await self.db.vouches.count_documents({
            "userId": str(user_id),
            "deleted": False
        })
    
    async def get_recent_vouch(self, user_id: int, vouched_by: int) -> Optional[Dict[str, Any]]:
        """Get most recent vouch from specific user"""
        return await self.db.vouches.find_one({
            "userId": str(user_id),
            "vouchedBy": str(vouched_by),
            "deleted": False
        }, sort=[("timestamp", -1)])
    
    async def delete_vouches(self, user_id: int, count: int = None) -> int:
        """Delete vouches for a user"""
        query = {"userId": str(user_id), "deleted": False}
        
        if count:
            vouches = await self.db.vouches.find(query).sort("timestamp", -1).limit(count).to_list(length=None)
            vouch_ids = [vouch["_id"] for vouch in vouches]
            result = await self.db.vouches.update_many(
                {"_id": {"$in": vouch_ids}},
                {"$set": {"deleted": True}}
            )
            return result.modified_count
        else:
            result = await self.db.vouches.update_many(
                query,
                {"$set": {"deleted": True}}
            )
            return result.modified_count
    
    async def transfer_vouches(self, from_user_id: int, to_user_id: int) -> int:
        """Transfer vouches from one user to another"""
        result = await self.db.vouches.update_many(
            {"userId": str(from_user_id), "deleted": False},
            {"$set": {"userId": str(to_user_id)}}
        )
        return result.modified_count
    
    async def search_vouches(self, keyword: str, user_id: int = None) -> List[Dict[str, Any]]:
        """Search vouches by keyword"""
        query = {
            "message": {"$regex": keyword, "$options": "i"},
            "deleted": False
        }
        
        if user_id:
            query["userId"] = str(user_id)
            
        cursor = self.db.vouches.find(query).sort("timestamp", -1)
        return await cursor.to_list(length=None)
    
    async def get_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get vouch leaderboard"""
        pipeline = [
            {"$match": {"deleted": False}},
            {"$group": {"_id": "$userId", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        return await self.db.vouches.aggregate(pipeline).to_list(length=None)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vouch statistics"""
        total_vouches = await self.db.vouches.count_documents({"deleted": False})
        
        pipeline_giver = [
            {"$match": {"deleted": False}},
            {"$group": {"_id": "$vouchedBy", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        top_giver = await self.db.vouches.aggregate(pipeline_giver).to_list(length=1)
        
        pipeline_receiver = [
            {"$match": {"deleted": False}},
            {"$group": {"_id": "$userId", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        top_receiver = await self.db.vouches.aggregate(pipeline_receiver).to_list(length=1)
        
        return {
            "total": total_vouches,
            "top_giver": top_giver[0] if top_giver else None,
            "top_receiver": top_receiver[0] if top_receiver else None
        }
    
    async def bulk_create_vouches(self, user_id: int, vouched_by: int, count: int, message: str) -> int:
        """Create multiple vouches at once"""
        vouches = []
        for _ in range(count):
            vouch_data = {
                "userId": str(user_id),
                "vouchedBy": str(vouched_by),
                "points": 1,
                "message": message,
                "timestamp": datetime.utcnow(),
                "deleted": False,
                "vouchId": self.db.generate_id()
            }
            vouches.append(vouch_data)
        
        if vouches:
            await self.db.vouches.insert_many(vouches)
        return len(vouches)

class TicketManager:
    """Ticket system database operations"""
    
    def __init__(self, db: MongoDB):
        self.db = db
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ticket"""
        ticket_data["ticketId"] = self.db.generate_id()
        ticket_data["createdAt"] = datetime.utcnow()
        ticket_data["status"] = "Pending"
        
        await self.db.tickets.insert_one(ticket_data)
        return ticket_data
    
    async def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        return await self.db.tickets.find_one({"ticketId": ticket_id})
    
    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket by channel ID"""
        return await self.db.tickets.find_one({"channelId": channel_id})
    
    async def update_ticket(self, ticket_id: str, update_data: Dict[str, Any]) -> bool:
        """Update ticket data"""
        result = await self.db.tickets.update_one(
            {"ticketId": ticket_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket"""
        result = await self.db.tickets.delete_one({"ticketId": ticket_id})
        return result.deleted_count > 0
    
    async def get_user_tickets(self, user_id: int, ticket_type: str = None) -> List[Dict[str, Any]]:
        """Get all tickets for a user"""
        query = {"userId": str(user_id)}
        if ticket_type:
            query["type"] = ticket_type
            
        cursor = self.db.tickets.find(query).sort("createdAt", -1)
        return await cursor.to_list(length=None)