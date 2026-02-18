# Requirements
import math
import json
import ifcopenshell
import ifcopenshell.geom

# --------------------------
# Geometry settings
# --------------------------
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)

# --------------------------
# IFC helpers
# --------------------------
def calculate_space_area(space):
    """Approximate area by summing triangle areas from the space mesh."""
    try:
        shape = ifcopenshell.geom.create_shape(settings, space)
        verts = shape.geometry.verts
        faces = shape.geometry.faces
        area = 0.0

        for i in range(0, len(faces), 3):
            i0, i1, i2 = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
            v0 = verts[i0:i0 + 3]
            v1 = verts[i1:i1 + 3]
            v2 = verts[i2:i2 + 3]

            a = math.sqrt((v1[0]-v0[0])**2 + (v1[1]-v0[1])**2 + (v1[2]-v0[2])**2)
            b = math.sqrt((v2[0]-v1[0])**2 + (v2[1]-v1[1])**2 + (v2[2]-v1[2])**2)
            c = math.sqrt((v0[0]-v2[0])**2 + (v0[1]-v2[1])**2 + (v0[2]-v2[2])**2)

            s = (a + b + c) / 2.0
            area += math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0.0))

        return float(area)
    except Exception:
        return 0.0

def dwelling_area_check(ifc_model_path, min_area=36.0):
    """Check if total dwelling useful area >= min_area."""
    model = ifcopenshell.open(ifc_model_path)
    spaces = model.by_type("IfcSpace")

    total_area = 0.0
    room_areas = {}

    for space in spaces:
        area = calculate_space_area(space)
        room_name = getattr(space, "LongName", None) or getattr(space, "Name", None) or "Unnamed"
        room_areas[str(room_name)] = float(area)
        total_area += float(area)

    if total_area >= float(min_area):
        return {
            "result": "pass",
            "reason": f"Total useful area {total_area:.2f} m² >= {float(min_area):.2f} m²",
            "total_area": float(total_area),
            "room_areas": room_areas,
        }

    return {
        "result": "fail",
        "reason": f"Total useful area {total_area:.2f} m² < {float(min_area):.2f} m²",
        "total_area": float(total_area),
        "room_areas": room_areas,
    }

# --------------------------
# Tool entrypoint (what your LLM router will call later)
# --------------------------
def dwelling_area_check_tool(ifc_model_path: str, min_area: float = 36.0):
    return dwelling_area_check(ifc_model_path, min_area)

# --------------------------
# Schema (API key not needed)
# Plain JSON-schema-like dict, easy to serialize + pass to any LLM framework
# --------------------------
DWELLING_AREA_CHECK_SCHEMA = {
    "name": "dwelling_area_check_tool",
    "description": "Checks whether an IFC dwelling meets a minimum total useful area requirement and returns a room-by-room breakdown.",
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_model_path": {
                "type": "string",
                "description": "Filesystem path to the IFC model."
            },
            "min_area": {
                "type": "number",
                "description": "Minimum total area in m². Default is 36."
            }
        },
        "required": ["ifc_model_path"]
    }
}

# --------------------------
# Optional: local sanity test (no API usage)
# --------------------------
if __name__ == "__main__":
    print("Schema OK:")
    print(json.dumps(DWELLING_AREA_CHECK_SCHEMA, indent=2))

    ifc_path = "/content/ifc-bench/projects/duplex/arc.ifc"
    result = dwelling_area_check_tool(ifc_path, min_area=36.0)
    print(result["result"])
    print(result["reason"])
