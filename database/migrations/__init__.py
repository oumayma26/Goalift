"""
database/migrations/__init__.py
"""

# Import explicite pour que le runner charge les migrations
from database.migrations import generator
from database.migrations import schema_detector