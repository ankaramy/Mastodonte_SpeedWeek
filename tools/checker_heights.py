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
def check_living_area_height(model, min_height=2.50):
    """
    Check if all main living areas meet the minimum height requirement.
    
    Args:
        model: ifcopenshell.file object (pre-loaded IFC model)
        min_height: minimum height in meters (default 2.50)
    
    Returns:
        list[dict]: One dict per living/bedroom/hall space, following IFCore schema
    """
    spaces = get_main_living_areas(model)
    results = []

    for space in spaces:
        height = get_space_height(space)
        space_name = space.Name or f"Space #{space.id()}"
        space_id = getattr(space, "GlobalId", str(space.id()))
        
        status = "pass" if height >= min_height else "fail"
        comment = None if height >= min_height else f"Height {height:.2f}m below required {min_height:.2f}m"
        
        results.append({
            "element_id": space_id,
            "element_type": "IfcSpace",
            "element_name": space_name,
            "element_name_long": f"{space_name} (living area)",
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
    results = check_living_area_height(model, min_height=2.50)
    
    print("Living Area Height Check Results:")
    for r in results:
        print(f"[{r['check_status'].upper()}] {r['element_name']}: {r['actual_value']}")
        if r['comment']:
            print(f"  → {r['comment']}")
