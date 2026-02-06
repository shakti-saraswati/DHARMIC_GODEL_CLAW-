"""Message type definitions and validation for the swarm communication system."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json


class MessageType(Enum):
    """Enumeration of message types in the swarm."""
    
    PROPOSAL = "proposal"
    APPROVAL = "approval"
    REJECTION = "rejection"
    IMPLEMENTATION = "implementation"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"


class Priority(Enum):
    """Message priority levels."""
    
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Message:
    """Base message structure for swarm communication."""
    
    id: str
    type: MessageType
    sender: str
    recipient: Optional[str]
    content: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    timestamp: Optional[datetime] = None
    parent_id: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            'id': self.id,
            'type': self.type.value,
            'sender': self.sender,
            'recipient': self.recipient,
            'content': self.content,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'parent_id': self.parent_id
        }
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        return cls(
            id=data['id'],
            type=MessageType(data['type']),
            sender=data['sender'],
            recipient=data.get('recipient'),
            content=data['content'],
            priority=Priority(data.get('priority', Priority.NORMAL.value)),
            timestamp=timestamp,
            parent_id=data.get('parent_id')
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create message from JSON string."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise MessageValidationError(f"Invalid message JSON: {e}")


@dataclass
class ProposalMessage:
    """Specialized message for proposals."""
    
    title: str
    description: str
    changes: List[str]
    rationale: str
    risk_level: str = "low"
    estimated_effort: str = "small"
    
    def to_message(self, sender: str, message_id: str) -> Message:
        """Convert to base Message."""
        return Message(
            id=message_id,
            type=MessageType.PROPOSAL,
            sender=sender,
            recipient=None,
            content={
                'title': self.title,
                'description': self.description,
                'changes': self.changes,
                'rationale': self.rationale,
                'risk_level': self.risk_level,
                'estimated_effort': self.estimated_effort
            },
            priority=Priority.NORMAL
        )


@dataclass
class ApprovalMessage:
    """Specialized message for approvals."""
    
    proposal_id: str
    approved: bool
    feedback: str = ""
    conditions: List[str] = None
    
    def __post_init__(self) -> None:
        """Initialize conditions if None."""
        if self.conditions is None:
            self.conditions = []
    
    def to_message(self, sender: str, message_id: str) -> Message:
        """Convert to base Message."""
        msg_type = MessageType.APPROVAL if self.approved else MessageType.REJECTION
        return Message(
            id=message_id,
            type=msg_type,
            sender=sender,
            recipient=None,
            content={
                'proposal_id': self.proposal_id,
                'approved': self.approved,
                'feedback': self.feedback,
                'conditions': self.conditions
            },
            parent_id=self.proposal_id,
            priority=Priority.HIGH
        )


@dataclass
class StatusMessage:
    """Specialized message for status updates."""
    
    status: str
    details: Dict[str, Any]
    health: str = "healthy"
    
    def to_message(self, sender: str, message_id: str) -> Message:
        """Convert to base Message."""
        return Message(
            id=message_id,
            type=MessageType.STATUS_UPDATE,
            sender=sender,
            recipient=None,
            content={
                'status': self.status,
                'details': self.details,
                'health': self.health
            },
            priority=Priority.LOW
        )


class MessageValidationError(Exception):
    """Exception raised for message validation errors."""
    pass


def validate_message(message: Message) -> bool:
    """Validate message structure and content.
    
    Args:
        message: Message to validate
        
    Returns:
        True if valid
        
    Raises:
        MessageValidationError: If message is invalid
    """
    if not message.id:
        raise MessageValidationError("Message ID is required")
    
    if not message.sender:
        raise MessageValidationError("Sender is required")
    
    if not isinstance(message.type, MessageType):
        raise MessageValidationError("Invalid message type")
    
    if not isinstance(message.priority, Priority):
        raise MessageValidationError("Invalid priority")
    
    if not isinstance(message.content, dict):
        raise MessageValidationError("Content must be a dictionary")
    
    # Type-specific validation
    if message.type == MessageType.PROPOSAL:
        required_fields = ['title', 'description', 'changes', 'rationale']
        for field in required_fields:
            if field not in message.content:
                raise MessageValidationError(f"Proposal missing required field: {field}")
    
    elif message.type in [MessageType.APPROVAL, MessageType.REJECTION]:
        if 'proposal_id' not in message.content:
            raise MessageValidationError("Approval/rejection missing proposal_id")
        if 'approved' not in message.content:
            raise MessageValidationError("Approval/rejection missing approved field")
    
    return True


def create_heartbeat(sender: str, message_id: str) -> Message:
    """Create a heartbeat message.
    
    Args:
        sender: Agent sending heartbeat
        message_id: Unique message identifier
        
    Returns:
        Heartbeat message
    """
    return Message(
        id=message_id,
        type=MessageType.HEARTBEAT,
        sender=sender,
        recipient=None,
        content={'timestamp': datetime.utcnow().isoformat()},
        priority=Priority.LOW
    )


def create_error_message(sender: str, message_id: str, error: str, 
                        context: Optional[Dict[str, Any]] = None) -> Message:
    """Create an error message.
    
    Args:
        sender: Agent reporting error
        message_id: Unique message identifier
        error: Error description
        context: Additional error context
        
    Returns:
        Error message
    """
    content = {'error': error}
    if context:
        content['context'] = context
    
    return Message(
        id=message_id,
        type=MessageType.ERROR,
        sender=sender,
        recipient=None,
        content=content,
        priority=Priority.HIGH
    )