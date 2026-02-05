# DGC Context Manager — Clawdbot Memory Integration
"""
Context manager that uses Unified Memory for Clawdbot recall.
Bridges my working memory with long-term unified storage.
"""

import sys
sys.path.insert(0, '/Users/dhyana/DHARMIC_GODEL_CLAW/src/core')

from unified_memory import MemoryManager, MemoryConfig, MemoryType

class DGCContextManager:
    """
    Manages Clawdbot context using Unified Memory.
    
    - Captures key interactions
    - Retrieves relevant context for tasks  
    - Maintains conversation coherence
    """
    
    def __init__(self):
        self.memory = MemoryManager(MemoryConfig(
            db_path='~/.dgc_context/clawdbot_memory.db'
        ))
        self.recent_ids = []
    
    def capture_interaction(self, role: str, content: str, tags=None):
        """Capture a conversation turn."""
        mem_id = self.memory.capture(
            content=f"[{role}] {content[:500]}",
            memory_type=MemoryType.INTERACTION,
            tags=tags or ['conversation'],
            importance=7 if role == 'user' else 5
        )
        self.recent_ids.append(mem_id)
        self.recent_ids = self.recent_ids[-20:]  # Keep last 20
        return mem_id
    
    def get_context_for_query(self, query: str, max_memories=5):
        """Get relevant memories for current query."""
        return self.memory.get_context_for_task(
            query, 
            self.recent_ids,
            max_memories
        )
    
    def recall(self, query: str, limit=5):
        """Search memory for relevant information."""
        return self.memory.search(query, limit=limit)

# Global instance
_context_manager = None

def get_context_manager():
    global _context_manager
    if _context_manager is None:
        _context_manager = DGCContextManager()
    return _context_manager

if __name__ == "__main__":
    cm = get_context_manager()
    print("✅ DGC Context Manager initialized")
    print(f"Stats: {cm.memory.get_stats()}")
