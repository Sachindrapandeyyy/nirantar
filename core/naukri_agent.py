import sys
from pathlib import Path

# Add root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from naukri.agent import AutonomousNaukriAgent, SEARCH_VECTORS
from naukri.filters import is_valid_software_role

__all__ = ["AutonomousNaukriAgent", "SEARCH_VECTORS", "is_valid_software_role"]

if __name__ == "__main__":
    import asyncio
    agent = AutonomousNaukriAgent()
    asyncio.run(agent.run_continuous_engine())
