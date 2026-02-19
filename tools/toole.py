# --------------------------
# Requirements
# --------------------------
import math
import json
import ifcopenshell
import ifcopenshell.geom

# --------------------------
# Geometry settings (same pattern as other tools)
# --------------------------
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)

# --------------------------
# IFC Geometry Helper
# --------------------------
def _calculate_space_area(space):
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

            a = math.dist(v0, v1)
            b = math.dist(v1, v2)
            c = math.dist(v2, v0)

            s = (a + b) / 2.0 + c / 2.0
            area += math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0.0))

        return float(area)

    except Exception:
        return 0.0


# --------------------------
# Semantic helpers
# --------------------------
def _space_label(space):
    return str(
        getattr(space, "LongName", None)
        or getattr(space, "Name", None)
        or "Unnamed"
    )


def _matches_any_keyword(text, keywords):
    t = (text or "").lower()
    return any(k in t for k in keywords)


def _get_spaces_by_keywords(model, keywords):
    spaces = model.by_type("IfcSpace")
    return [s for s in spaces if _matches_any_keyword(_space_label(s), keywords)]


# --------------------------
# Regulation Logic
# --------------------------
def _area_to_occupancy(area):
    """
    Regulation mapping:
        <5 m²   -> invalid bedroom
        ≥5 m²   -> 1 person
        ≥8 m²   -> 2 people
        ≥12 m²  -> 3 people
    """
    if area < 5.0:
        return 0
    elif area < 8.0:
        return 1
    elif area < 12.0:
        return 2
    else:
        return 3


def bedroom_occupancy_check(ifc_model_path):
    """
    Determines allowed occupancy from bedroom areas.

    Special rule:
    - If NO bedrooms exist (studio dwelling), occupancy is limited to max 2 people.
    """

    model = ifcopenshell.open(ifc_model_path)

    bedroom_keywords = ["bedroom", "habitacion", "habitación", "dormitorio"]
    living_keywords  = ["living", "salon", "salón", "studio", "estudio", "common"]

    bedrooms = _get_spaces_by_keywords(model, bedroom_keywords)
    living_spaces = _get_spaces_by_keywords(model, living_keywords)

    room_areas = {}
    occupancy = {}
    total_people = 0

    # --------------------------
    # Studio Case
    # --------------------------
    if len(bedrooms) == 0:

        if not living_spaces:
            return {
                "result": "fail",
                "reason": "No habitable space identified",
                "room_areas": {},
                "occupancy": {},
                "total_allowed_people": 0,
            }

        main_space = living_spaces[0]
        label = _space_label(main_space)
        area = _calculate_space_area(main_space)

        allowed = min(_area_to_occupancy(area), 2)

        room_areas[label] = float(area)
        occupancy[label] = int(allowed)

        return {
            "result": "pass",
            "reason": "Studio dwelling limited to maximum 2 occupants",
            "room_areas": room_areas,
            "occupancy": occupancy,
            "total_allowed_people": int(allowed),
        }

    # --------------------------
    # Bedroom-based Case
    # --------------------------
    for space in bedrooms:
        label = _space_label(space)
        area = _calculate_space_area(space)
        allowed = _area_to_occupancy(area)

        if allowed == 0:
            return {
                "result": "fail",
                "reason": f"{label} area {area:.2f} m² is below minimum 5 m²",
                "room_areas": room_areas,
                "occupancy": occupancy,
                "total_allowed_people": int(total_people),
            }

        room_areas[label] = float(area)
        occupancy[label] = int(allowed)
        total_people += allowed

    return {
        "result": "pass",
        "reason": "Bedroom areas satisfy occupancy requirements",
        "room_areas": room_areas,
        "occupancy": occupancy,
        "total_allowed_people": int(total_people),
    }


# --------------------------
# Tool Entrypoint (LLM-callable)
# --------------------------
def bedroom_occupancy_check_tool(ifc_model_path: str):
    return bedroom_occupancy_check(ifc_model_path)


# --------------------------
# Schema (matches your other tool style)
# --------------------------
BEDROOM_OCCUPANCY_CHECK_SCHEMA = {
    "name": "bedroom_occupancy_check_tool",
    "description": "Evaluates bedroom areas in an IFC model to determine the allowed number of occupants.",
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_model_path": {
                "type": "string",
                "description": "Filesystem path to the IFC model."
            }
        },
        "required": ["ifc_model_path"]
    }
}


# --------------------------
# Local Sanity Test (same pattern as Tool 1)
# --------------------------
if __name__ == "__main__":
    print("Schema OK:")
    print(json.dumps(BEDROOM_OCCUPANCY_CHECK_SCHEMA, indent=2))

    ifc_path = "/content/ifc-bench/projects/duplex/arc.ifc"

    result = bedroom_occupancy_check_tool(ifc_path)

    print(result["result"])
    print(result["reason"])