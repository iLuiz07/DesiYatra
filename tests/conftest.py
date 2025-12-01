import sys
import os
from pathlib import Path

# Add the project root directory to sys.path
# This assumes conftest.py is in /tests/ and project root is one level up
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
