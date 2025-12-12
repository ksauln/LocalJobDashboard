import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:  # make src imports work when modules import app.*
    sys.path.insert(0, str(PROJECT_ROOT))
