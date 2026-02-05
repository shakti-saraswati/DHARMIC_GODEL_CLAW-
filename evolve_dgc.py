
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("dgc_evolution")

# Set YOLO Mode and LLM capability
os.environ["DGC_SWARM_USE_LLM"] = "1"
os.environ["DGC_YOLO_MODE"] = "1"
os.environ["DGC_GOD_MODE"] = "1" # Maximum permissions
os.environ["DGC_MOCK_LLM"] = "1" # Use mock LLM for demonstration
os.environ["DGC_ALLOW_LIVE"] = "1" # ALLOW WRITING TO FILES

# Import Orchestrator
try:
    from swarm.orchestrator import SwarmOrchestrator
except ImportError as e:
    logger.error(f"Failed to import SwarmOrchestrator: {e}")
    sys.exit(1)

async def main():
    logger.info("🚀 STARTING DGC EVOLUTION SEQUENCE (YOLO MODE)")
    logger.info("Goal: Stronger, more effective, self-evolving system.")
    
    orchestrator = SwarmOrchestrator()
    
    # Run continuous improvement
    # We target 'swarm' initially to improve the agents themselves
    results = await orchestrator.continuous_improvement(
        max_iterations=3,
        improvement_threshold=0.01 # Keep going even for small gains
    )
    
    logger.info("Evolution sequence complete.")
    for idx, res in enumerate(results):
        status = "✅" if res.state.name == "COMPLETED" else "❌"
        logger.info(f"Cycle {idx+1}: {status} Files: {res.files_changed}")

if __name__ == "__main__":
    asyncio.run(main())
