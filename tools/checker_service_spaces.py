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
def check_service_spaces_min_height(model, min_height=2.20):
    """
    Check if bathrooms, kitchens, and hallways meet minimum height requirement.
    
    Regulation:
      - Minimum height in bathrooms, kitchens, and hallways is 2.20 m
    
    Args:
        model: ifcopenshell.file object (pre-loaded IFC model)
        min_height: minimum height in meters (default 2.20)
    
    Returns:
        list[dict]: One dict per service space, following IFCore schema
    """
    spaces = model.by_type("IfcSpace")
    results = []

    for space in spaces:
        label = get_space_name(space)
        label_l = label.lower()

        if not is_service_space(label_l):
            continue

        height = get_space_height(space)
        space_id = getattr(space, "GlobalId", str(space.id()))
        
        status = "pass" if height >= min_height else "fail"
        comment = None if height >= min_height else f"Height {height:.2f}m below required {min_height:.2f}m"
        
        results.append({
            "element_id": space_id,
            "element_type": "IfcSpace",
            "element_name": label,
            "element_name_long": f"{label} (service space)",
            "check_status": status,
            "actual_value": f"{height:.2f} m",
            "required_value": f"{min_height:.2f} m",
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
    results = check_service_spaces_min_height(model, min_height=2.20)
    
    print("Service Spaces Min Height Check Results:")
    for r in results:
        print(f"[{r['check_status'].upper()}] {r['element_name']}: {r['actual_value']}")
        if r['comment']:
            print(f"  → {r['comment']}")