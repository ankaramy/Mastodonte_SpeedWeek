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
# Helper functions
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

            a = math.dist(v0, v1)
            b = math.dist(v1, v2)
            c = math.dist(v2, v0)

            s = (a + b + c) / 2.0
            area += math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0.0))

        return float(area)
    except Exception:
        return 0.0


def get_space_label(space):
    """Get descriptive name if available, fallback to GlobalId."""
    return str(
        getattr(space, "LongName", None)
        or getattr(space, "Name", None)
        or f"Space #{space.id()}"
    )


def area_to_occupancy(area_m2):
    """
    Regulation mapping:
        <5 m²   -> invalid bedroom
        ≥5 m²   -> 1 person
        ≥8 m²   -> 2 people
        ≥12 m²  -> 3 people
    """
    if area_m2 < 5.0:
        return 0
    elif area_m2 < 8.0:
        return 1
    elif area_m2 < 12.0:
        return 2
    else:
        return 3


def get_spaces_by_keywords(model, keywords):
    """Filter spaces matching any keyword in their name."""
    spaces = model.by_type("IfcSpace")
    matched = []
    for s in spaces:
        label_lower = get_space_label(s).lower()
        if any(k in label_lower for k in keywords):
            matched.append(s)
    return matched


# --------------------------
# Main check function
# --------------------------
def check_bedroom_occupancy(model):
    """
    Check if all bedrooms meet minimum area requirement and calculate occupancy.
    
    Regulation:
      - Bedroom min area 5 m² for 1 occupant
      - 8 m² for 2 occupants
      - 12 m² for 3 occupants
      - Studio (no bedrooms): limited to max 2 occupants
    
    Args:
        model: ifcopenshell.file object (pre-loaded IFC model)
    
    Returns:
        list[dict]: One dict per bedroom/living space, following IFCore schema
    """
    results = []
    
    bedroom_keywords = ["bedroom", "habitacion", "habitación", "dormitorio"]
    living_keywords = ["living", "salon", "salón", "studio", "estudio", "common"]
    
    bedrooms = get_spaces_by_keywords(model, bedroom_keywords)
    living_spaces = get_spaces_by_keywords(model, living_keywords)
    
    # --------------------------
    # Studio case (no bedrooms)
    # --------------------------
    if len(bedrooms) == 0:
        if living_spaces:
            space = living_spaces[0]
            label = get_space_label(space)
            area = calculate_space_area(space)
            space_id = getattr(space, "GlobalId", str(space.id()))
            occupancy = min(area_to_occupancy(area), 2)
            passed = occupancy > 0
            
            results.append({
                "element_id": space_id,
                "element_type": "IfcSpace",
                "element_name": label,
                "element_name_long": f"{label} (studio dwelling)",
                "check_status": "pass" if passed else "fail",
                "actual_value": f"{area:.2f} m² → {occupancy} occupant(s) max",
                "required_value": "Studio max 2 occupants",
                "comment": "Studio dwelling limited to maximum 2 occupants" if passed else f"Area {area:.2f} m² too small for studio",
                "log": None,
            })
        return results
    
    # --------------------------
    # Bedroom-based case
    # --------------------------
    for space in bedrooms:
        label = get_space_label(space)
        area = calculate_space_area(space)
        space_id = getattr(space, "GlobalId", str(space.id()))
        occupancy = area_to_occupancy(area)
        
        passed = occupancy > 0
        comment = None
        if not passed:
            comment = f"Area {area:.2f} m² below minimum 5 m² for bedroom"
        
        results.append({
            "element_id": space_id,
            "element_type": "IfcSpace",
            "element_name": label,
            "element_name_long": f"{label} (bedroom occupancy)",
            "check_status": "pass" if passed else "fail",
            "actual_value": f"{area:.2f} m² → {occupancy} occupant(s)",
            "required_value": "≥5 m² (min 1 occupant)",
            "comment": comment,
            "log": None,
        })
    
    return results


# --------------------------
# Local testing (optional)
# --------------------------
if __name__ == "__main__":
    import ifcopenshell
    ifc_path = "C:/Users/OWNER/Desktop/IAAC/T05/AI_SpeedRun/AI-Speed-Run-Week/ifc_models/arc.ifc"
    model = ifcopenshell.open(ifc_path)
    results = check_bedroom_occupancy(model)
    
    print("Bedroom Occupancy Check Results:")
    for r in results:
        print(f"[{r['check_status'].upper()}] {r['element_name']}: {r['actual_value']}")
        if r['comment']:
            print(f"  → {r['comment']}")
