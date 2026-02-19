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

def check_dwelling_area(model, min_area=36.0):
    """
    Check if each space in the dwelling meets minimum area requirement.
    
    Args:
        model: ifcopenshell.file object (pre-loaded IFC model)
        min_area: minimum total area in m² (default 36.0)
    
    Returns:
        list[dict]: One dict per IfcSpace element, following IFCore schema
    """
    spaces = model.by_type("IfcSpace")
    results = []
    total_area = 0.0

    for space in spaces:
        area = calculate_space_area(space)
        space_name = getattr(space, "LongName", None) or getattr(space, "Name", None) or f"Space #{space.id()}"
        space_id = getattr(space, "GlobalId", str(space.id()))
        
        total_area += float(area)
        
        results.append({
            "element_id": space_id,
            "element_type": "IfcSpace",
            "element_name": space_name,
            "element_name_long": f"{space_name} (dwelling area check)",
            "check_status": "pass",  # Will be determined after loop for aggregate
            "actual_value": f"{area:.2f} m²",
            "required_value": f"{min_area:.2f} m²",
            "comment": None,
            "log": None,
        })

    # Update check_status based on total area
    if len(results) == 0:
        return results
    
    status = "pass" if total_area >= float(min_area) else "fail"
    for result in results:
        result["check_status"] = status
        if status == "fail":
            result["comment"] = f"Total dwelling area {total_area:.2f} m² is below required {min_area:.2f} m²"
    
    return results


# --------------------------
# Local testing (optional)
# --------------------------
if __name__ == "__main__":
    import ifcopenshell
    ifc_path = "C:/Users/OWNER/Desktop/IAAC/T05/AI_SpeedRun/AI-Speed-Run-Week/ifc_models/arc.ifc"
    model = ifcopenshell.open(ifc_path)
    results = check_dwelling_area(model, min_area=36.0)
    
    print("Dwelling Area Check Results:")
    for r in results:
        print(f"[{r['check_status'].upper()}] {r['element_name']}: {r['actual_value']}")
        if r['comment']:
            print(f"  → {r['comment']}")
