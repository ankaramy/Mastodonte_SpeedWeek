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
    return ifcopenshell.open(ifc_model_path)

def get_space_name(space):
    """Get descriptive name if available, fallback to LongName/Name/GlobalId."""
    if getattr(space, "LongName", None):
        return str(space.LongName)
    if getattr(space, "Name", None):
        return str(space.Name)
    return str(getattr(space, "GlobalId", "Unnamed"))

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

def is_service_space(space_name_lower):
    """Bathrooms, kitchens, hallways by keywords."""
    service_keywords = [
        "bath", "bathroom", "baño", "bano", "wc", "toilet",
        "kitchen", "cocina",
        "hall", "hallway", "corridor", "pasillo"
    ]
    return any(k in space_name_lower for k in service_keywords)

# --------------------------
# Compliance check
# --------------------------
def service_spaces_min_height_check(ifc_model_path, min_height=2.20):
    """
    Regulation:
      - Minimum height in bathrooms, kitchens, and hallways is 2.20 m

    Returns:
      - result: 'pass' or 'fail'
      - reason
      - room_heights: dict label -> height
      - checked_spaces: list of labels that were evaluated
    """
    model = load_model(ifc_model_path)
    spaces = model.by_type("IfcSpace")

    room_heights = {}
    checked_spaces = []

    for space in spaces:
        label = get_space_name(space)
        label_l = label.lower()

        if not is_service_space(label_l):
            continue

        checked_spaces.append(label)
        h = get_space_height(space)
        room_heights[label] = h

        if h < float(min_height):
            return {
                "result": "fail",
                "reason": f"{label} height below {float(min_height):.2f}m",
                "room_heights": room_heights,
                "checked_spaces": checked_spaces
            }

    if not checked_spaces:
        return {
            "result": "fail",
            "reason": "No bathrooms/kitchens/hallways matched by keywords, nothing checked",
            "room_heights": room_heights,
            "checked_spaces": checked_spaces
        }

    return {
        "result": "pass",
        "reason": f"All checked bathrooms/kitchens/hallways meet minimum height {float(min_height):.2f}m",
        "room_heights": room_heights,
        "checked_spaces": checked_spaces
    }

# --------------------------
# Tool entrypoint (for an LLM router later)
# --------------------------
def service_spaces_min_height_check_tool(ifc_model_path: str, min_height: float = 2.20):
    return service_spaces_min_height_check(ifc_model_path, min_height)

# --------------------------
# Schema (no API key needed)
# --------------------------
SERVICE_SPACES_MIN_HEIGHT_SCHEMA = {
    "name": "service_spaces_min_height_check_tool",
    "description": "Checks bathrooms, kitchens, and hallways in an IFC for a minimum height requirement (default 2.20m).",
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_model_path": {
                "type": "string",
                "description": "Filesystem path to the IFC model."
            },
            "min_height": {
                "type": "number",
                "description": "Minimum height in meters. Default is 2.20."
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
    print(json.dumps(SERVICE_SPACES_MIN_HEIGHT_SCHEMA, indent=2))

    ifc_path = "/content/ifc-bench/projects/duplex/arc.ifc"  # change if needed
    check = service_spaces_min_height_check_tool(ifc_path, min_height=2.20)

    print("\nCheck result:")
    print(check["result"])
    print(check["reason"])
    print("Room heights:", check["room_heights"])
    print("Checked spaces:", check["checked_spaces"])