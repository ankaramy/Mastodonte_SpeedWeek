"""
IFCore Compliance Checker Tools

All check_* functions exported from this package follow the IFCore contract:
- Signature: check_*(model, **kwargs)
- Returns: list[dict] with IFCore schema (element_id, element_type, check_status, etc.)
- Platform auto-discovers check functions by name prefix "check_"
"""

from .checker_dwelling import check_dwelling_area
from .checker_heights import check_living_area_height
from .checker_living_rooms import check_living_room_compliance
from .checker_service_spaces import check_service_spaces_min_height

__all__ = [
    "check_dwelling_area",
    "check_living_area_height",
    "check_living_room_compliance",
    "check_service_spaces_min_height",
]
