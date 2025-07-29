"""Amazon Marketing Cloud Manager - Main Package"""

__version__ = "0.1.0"
__author__ = "AMC Manager Team"

from .config import settings
from .core.logger import get_logger

logger = get_logger(__name__)