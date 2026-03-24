import sys
from pathlib import Path

# Add backend directory to path so "from models.xxx" and "from dmx.xxx" resolve
backend_root = Path(__file__).parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
