import json
import math
import ifcopenshell
import ifcopenshell.geom

# Optional: only needed if you truly have it available
# from ifcopenshell.util.element import get_psets as _get_psets

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

def calculate_space_area(space):
    """
    Approximate area from mesh triangles.
    Note: this is mesh surface area, not guaranteed to be floor area.
    """
    if hasattr(space, "NetFloorArea") and space.NetFloorArea:
        return float(space.NetFloorArea)

    try:
        shape = ifcopenshell.geom.create_shape(settings, space)
        verts = shape.geometry.verts
        faces = shape.geometry.faces
        area = 0.0

        for i in range(0, len(faces), 3):
            idx0, idx1, idx2 = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
            v0 = verts[idx0:idx0 + 3]
            v1 = verts[idx1:idx1 + 3]
            v2 = verts[idx2:idx2 + 3]

            a = math.sqrt((v1[0]-v0[0])**2 + (v1[1]-v0[1])**2 + (v1[2]-v0[2])**2)
            b = math.sqrt((v2[0]-v1[0])**2 + (v2[1]-v1[1])**2 + (v2[2]-v1[2])**2)
            c = math.sqrt((v0[0]-v2[0])**2 + (v0[1]-v2[1])**2 + (v0[2]-v2[2])**2)

            s = (a + b + c) / 2.0
            area += math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0.0))

        return float(area)
    except Exception:
        return 0.0

def get_space_name(space):
    """Get descriptive name if available, fallback to LongName/Name/GlobalId."""
    if getattr(space, "LongName", None):
        return str(space.LongName)
    if getattr(space, "Name", None):
        return str(space.Name)

    # If you have ifcopenshell.util.element available, you can enable this block:
    # try:
    #     psets = _get_psets(space)
    #     for props in (psets or {}).values():
    #         for k, v in (props or {}).items():
    #             if "name" in str(k).lower() and isinstance(v, str) and v.strip():
    #                 return v.strip()
    # except Exception:
    #     pass

    return str(getattr(space, "GlobalId", "Unnamed"))

def can_fit_square(area_m2, width=2.4, depth=2.4):
    """Approx check: area must allow a width x depth square."""
    return float(area_m2) >= float(width) * float(depth)

# --------------------------
# Living room compliance
# --------------------------
def check_living_room_compliance(model):
    """
    Check living room spaces for minimum area and clearance rules.
    
    Rule encoded:
      - Living room min area 10 m²
      - If living+kitchen combined: min area 14 m²
      - Must allow 2.40 x 2.40 m clearance (approx via area check)
    
    Args:
        model: ifcopenshell.file object (pre-loaded IFC model)
    
    Returns:
        list[dict]: One dict per living room space, following IFCore schema
    """
    spaces = model.by_type("IfcSpace")
    results = []

    for space in spaces:
        raw_name = get_space_name(space)
        name = raw_name.lower()
        area = calculate_space_area(space)
        space_id = getattr(space, "GlobalId", str(space.id()))
        
        if area <= 0:
            continue

        if "living" in name:
            has_kitchen = "kitchen" in name
            min_area = 14.0 if has_kitchen else 10.0

            clearance_ok = can_fit_square(area, 2.4, 2.4)
            passed = (area >= min_area) and clearance_ok

            reasons = []
            if area < min_area:
                reasons.append(f"Area {area:.2f} m² < required {min_area:.2f} m²")
            if not clearance_ok:
                reasons.append("Does not allow 2.40 m x 2.40 m square (approx)")

            results.append({
                "element_id": space_id,
                "element_type": "IfcSpace",
                "element_name": raw_name,
                "element_name_long": f"{raw_name} (living room zone)",
                "check_status": "pass" if passed else "fail",
                "actual_value": f"{area:.2f} m²",
                "required_value": f"{min_area:.2f} m²",
                "comment": "; ".join(reasons) if reasons else None,
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
    results = check_living_room_compliance(model)
    
    print("Living Room Compliance Check Results:")
    if not results:
        print("No living room spaces matched (keyword 'living') or no computable areas.")
    else:
        for r in results:
            print(f"[{r['check_status'].upper()}] {r['element_name']}: {r['actual_value']}")
            if r['comment']:
                print(f"  → {r['comment']}")