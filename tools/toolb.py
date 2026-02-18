import json
import ifcopenshell
import ifcopenshell.geom

# --------------------------
# Geometry settings
# --------------------------
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)

# --------------------------
# Helper functions
# --------------------------
def load_model(ifc_model_path):
    """Load IFC model"""
    return ifcopenshell.open(ifc_model_path)

def get_main_living_areas(ifc_model):
    """
    Return spaces considered main living areas.
    Filtering by common keywords in space name.
    """
    spaces = ifc_model.by_type("IfcSpace")
    main_spaces = []
    for s in spaces:
        if s.Name and any(keyword in s.Name.lower() for keyword in ["living", "bedroom", "hall"]):
            main_spaces.append(s)
    return main_spaces

def get_space_height(space):
    """
    Approximate height of a space from geometry bounding box.
    Uses Z coordinates of all vertices.
    """
    try:
        shape = ifcopenshell.geom.create_shape(settings, space)
        verts = shape.geometry.verts
        if not verts:
            return 0.0
        zs = verts[2::3]
        return float(max(zs) - min(zs))
    except Exception:
        return 0.0

# --------------------------
# Main check function
# --------------------------
def living_area_height_check(ifc_model_path, min_height=2.50):
    """
    Check if all main living areas meet the minimum height requirement.

    Returns a dictionary with:
    - result: 'pass' or 'fail'
    - reason: explanation string
    - room_heights: dictionary of room_name -> calculated height
    """
    model = load_model(ifc_model_path)
    spaces = get_main_living_areas(model)

    room_heights = {}
    for s in spaces:
        height = get_space_height(s)
        room_name = s.Name or "Unnamed"
        room_heights[room_name] = height
        if height < min_height:
            return {
                "result": "fail",
                "reason": f"{room_name} height below {min_height}m",
                "room_heights": room_heights
            }

    return {
        "result": "pass",
        "reason": f"All main living areas meet minimum height {min_height}m",
        "room_heights": room_heights
    }

# --------------------------
# Tool entrypoint (for an LLM router later)
# --------------------------
def living_area_height_check_tool(ifc_model_path: str, min_height: float = 2.50):
    return living_area_height_check(ifc_model_path, min_height)

# --------------------------
# Schema (no API key needed)
# --------------------------
LIVING_AREA_HEIGHT_CHECK_SCHEMA = {
    "name": "living_area_height_check_tool",
    "description": "Checks whether main living areas in an IFC meet a minimum height requirement and returns a room-by-room height breakdown.",
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_model_path": {
                "type": "string",
                "description": "Filesystem path to the IFC model."
            },
            "min_height": {
                "type": "number",
                "description": "Minimum height in meters. Default is 2.50."
            }
        },
        "required": ["ifc_model_path"]
    }
}

# --------------------------
# Usage example (prints schema + pass/fail)
# --------------------------
if __name__ == "__main__":
    print("Schema OK:")
    print(json.dumps(LIVING_AREA_HEIGHT_CHECK_SCHEMA, indent=2))

    ifc_path = "/content/ifc-bench/projects/duplex/arc.ifc"  # change if needed
    check = living_area_height_check_tool(ifc_path, min_height=2.50)

    print("\nCheck result:")
    print(check["result"])
    print(check["reason"])
    print("Room heights:", check["room_heights"])
