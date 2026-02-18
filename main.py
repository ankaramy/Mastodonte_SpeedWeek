"""
IFCore Compliance Checker - Integration Test

This script tests all check_* functions against an IFC model.
Each check_* function returns list[dict] following the IFCore schema.
"""
import ifcopenshell
from tools.checker_dwelling import check_dwelling_area
from tools.checker_heights import check_living_area_height
from tools.checker_living_rooms import check_living_room_compliance
from tools.checker_service_spaces import check_service_spaces_min_height


# Map of check names to functions and their parameters
CHECKS = {
    "dwelling_area": {
        "func": check_dwelling_area,
        "kwargs": {"min_area": 36.0},
    },
    "living_area_height": {
        "func": check_living_area_height,
        "kwargs": {"min_height": 2.50},
    },
    "living_room_compliance": {
        "func": check_living_room_compliance,
        "kwargs": {},
    },
    "service_spaces_min_height": {
        "func": check_service_spaces_min_height,
        "kwargs": {"min_height": 2.20},
    },
}


def run_all_checks(ifc_model_path):
    """
    Load IFC model once and run all checks.
    
    Returns:
        dict: { check_name: [results], ... }
    """
    print(f"Loading IFC model: {ifc_model_path}")
    model = ifcopenshell.open(ifc_model_path)
    
    all_results = {}
    
    for check_name, check_info in CHECKS.items():
        print(f"\nRunning {check_name}...")
        func = check_info["func"]
        kwargs = check_info["kwargs"]
        
        try:
            results = func(model, **kwargs)
            all_results[check_name] = results
            
            # Print summary
            if results:
                passed = sum(1 for r in results if r["check_status"] == "pass")
                failed = sum(1 for r in results if r["check_status"] == "fail")
                print(f"  ✓ {check_name}: {passed} passed, {failed} failed")
                
                for r in results:
                    status_symbol = "✓" if r["check_status"] == "pass" else "✗"
                    print(f"    {status_symbol} {r['element_name']}: {r['actual_value']} (req: {r['required_value']})")
                    if r['comment']:
                        print(f"      → {r['comment']}")
            else:
                print(f"  ⓘ {check_name}: No elements checked")
        
        except Exception as e:
            print(f"  ✗ {check_name} FAILED: {str(e)}")
            all_results[check_name] = []
    
    return all_results


if __name__ == "__main__":
    ifc_path = r"C:\Users\OWNER\Desktop\IAAC\T05\AI_SpeedRun\AI-Speed-Run-Week\ifc_models\arc.ifc"
    
    print("=" * 70)
    print("IFCore Compliance Checker - Integration Test")
    print("=" * 70)
    
    results = run_all_checks(ifc_path)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for check_name, check_results in results.items():
        if check_results:
            passed = sum(1 for r in check_results if r["check_status"] == "pass")
            failed = sum(1 for r in check_results if r["check_status"] == "fail")
            print(f"{check_name}: {passed} ✓ / {failed} ✗")
        else:
            print(f"{check_name}: (no results)")

