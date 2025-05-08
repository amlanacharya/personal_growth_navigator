"""
Personal Growth Navigator package.
"""

# Add the parent directory to sys.path to allow imports from src
import os
import sys

# Get the absolute path of the src directory's parent
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the parent directory to sys.path if it's not already there
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
