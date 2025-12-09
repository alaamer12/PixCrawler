import sys
import os
from pathlib import Path

# Add repo root to sys.path to allow importing 'builder', 'validator' etc.
# This assumes we are running from sdk/tests or root
# Current file is sdk/tests/conftest.py
# Root is ../../
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))

print(f"Added {repo_root} to sys.path")
