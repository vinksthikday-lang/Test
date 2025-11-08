from datetime import datetime
from typing import Optional, Dict, Any

class Ticket:
    """Ticket data model"""
    
    def __init__(
        self,
        ticket_id: str,
        user_id: int,
        channel_id: int,
        ticket_type: str,  # 'shop' or 'mm'
        status: str = "Pending",
        category: str = None,
        order: str = None,
        quantity: int = 1,
        notes: str = None,
        staff_name: str = None,
        amount: float = None,
        transact_partner: int = None,
        close_message_id: int = None
    ):
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.channel_id = channel_id
        self.type = ticket_type
        self.status = status
        self.category = category
        self.order = order
        self.quantity = quantity
        self.notes = notes
        self.staff_name = staff_name
        self.amount = amount
        self.transact_partner = transact_partner
        self.close_message_id = close_message_id
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "ticketId": self.ticket_id,
            "userId": str(self.user_id),
            "channelId": self.channel_id,
            "type": self.type,
            "status": self.status,
            "category": self.category,
            "order": self.order,
            "quantity": self.quantity,
            "notes": self.notes,
            "staffName": self.staff_name,
            "amount": self.amount,
            "transactPartner": str(self.transact_partner) if self.transact_partner else None,
            "closeMessageId": self.close_message_id,
            "createdAt": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ticket':
        """Create Ticket instance from dictionary"""
        return cls(
            ticket_id=data.get('ticketId'),
            user_id=int(data.get('userId')),
            channel_id=data.get('channelId'),
            ticket_type=data.get('type'),
            status=data.get('status', 'Pending'),
            category=data.get('category'),
            order=data.get('order'),
            quantity=data.get('quantity', 1),
            notes=data.get('notes'),
            staff_name=data.get('staffName'),
            amount=data.get('amount'),
            transact_partner=int(data.get('transactPartner')) if data.get('transactPartner') else None,
            close_message_id=data.get('closeMessageId')
        )