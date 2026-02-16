"""
Shared types and type aliases for the application.
"""

from typing import Any, Dict, List, Optional

# Generic JSON-serializable structure
JSONDict = Dict[str, Any]
JSONList = List[Dict[str, Any]]

__all__ = ["JSONDict", "JSONList"]
