# Ensures the repository root is on sys.path when pytest runs from any directory, so `import coinselect` works without installing the package.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))