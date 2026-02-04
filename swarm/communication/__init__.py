"""
Communication module for the DHARMIC GODEL CLAW agent swarm.

This module handles inter-agent communication, message routing, and event broadcasting
within the swarm architecture.
"""

from typing import Dict, Any, List, Optional, Protocol, runtime_checkable
import logging

from .message_bus import MessageBus, Message, MessageType
from .event_system import EventSystem, Event, EventHandler
from .protocol import CommunicationProtocol, AgentMessage

__version__ = "0.1.0"
__all__ = [
    "MessageBus",
    "Message", 
    "MessageType",
    "EventSystem",
    "Event",
    "EventHandler",
    "CommunicationProtocol",
    "AgentMessage",
    "get_message_bus",
    "get_event_system",
]

# Module-level instances
_message_bus: Optional[MessageBus] = None
_event_system: Optional[EventSystem] = None

logger = logging.getLogger(__name__)


def get_message_bus() -> MessageBus:
    """
    Get the singleton MessageBus instance.
    
    Returns:
        MessageBus: The global message bus instance
        
    Raises:
        RuntimeError: If message bus is not initialized
    """
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
        logger.info("Initialized global message bus")
    return _message_bus


def get_event_system() -> EventSystem:
    """
    Get the singleton EventSystem instance.
    
    Returns:
        EventSystem: The global event system instance
        
    Raises:
        RuntimeError: If event system is not initialized
    """
    global _event_system
    if _event_system is None:
        _event_system = EventSystem()
        logger.info("Initialized global event system")
    return _event_system


def initialize_communication(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize the communication subsystem with optional configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        global _message_bus, _event_system
        
        if config is None:
            config = {}
            
        # Initialize message bus
        _message_bus = MessageBus(config.get("message_bus", {}))
        
        # Initialize event system  
        _event_system = EventSystem(config.get("event_system", {}))
        
        logger.info("Communication subsystem initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize communication subsystem: {e}")
        raise


def shutdown_communication() -> None:
    """
    Shutdown the communication subsystem and cleanup resources.
    """
    global _message_bus, _event_system
    
    try:
        if _message_bus is not None:
            _message_bus.shutdown()
            _message_bus = None
            
        if _event_system is not None:
            _event_system.shutdown()
            _event_system = None
            
        logger.info("Communication subsystem shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during communication shutdown: {e}")
        raise