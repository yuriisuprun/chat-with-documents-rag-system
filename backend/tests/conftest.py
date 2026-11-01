"""
Pytest configuration and shared fixtures.

Provides common setup and fixtures for tests.
"""

import os
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set testing environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["TEST_MODE"] = "true"
