"""Alembic migration environment — delegates to root alembic/env.py."""

import os
import sys

# Ensure backend/app is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from alembic import context
from app.db.schema import Base

config = context.config
target_metadata = Base.metadata