"""
Common types and data structures for the framework.
"""

from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class OperationResult:
    """Result of a hardware operation"""
    success: bool
    error: Optional[str] = None
    data: Optional[Any] = None
    log: str = ""

    def __bool__(self):
        return self.success