"""
SBDB: Set-Based Database Framework

A framework for generalised set-based structural design data generation
and verification.
"""

from .sets import DesignParameterSet, ObjectSet, VerifiedObjectLibrary
from .tracking import DatasetTracker

__version__ = "0.1.3"
__all__ = ["DesignParameterSet", "ObjectSet", "VerifiedObjectLibrary", "DatasetTracker"]
