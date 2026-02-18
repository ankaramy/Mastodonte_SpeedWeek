from tools import toola, toolb, toolc, toold

TOOLS = {
    # toola.py (contains dwelling area tool)
    "dwelling_area": toola.dwelling_area_check_tool,

    # toolb.py
    "living_area_height": toolb.living_area_height_check_tool,

    # toolc.py
    "living_room_compliance": toolc.living_room_compliance_tool,

    # toold.py
    "service_space_height": toold.service_spaces_min_height_check_tool,
}

SCHEMAS = {
    "dwelling_area": toola.DWELLING_AREA_CHECK_SCHEMA,
    "living_area_height": toolb.LIVING_AREA_HEIGHT_CHECK_SCHEMA,
    "living_room_compliance": toolc.LIVING_ROOM_COMPLIANCE_SCHEMA,
    "service_space_height": toold.SERVICE_SPACES_MIN_HEIGHT_SCHEMA,
}


def list_tools():
    return SCHEMAS


def run_tool(tool_name: str, **kwargs):
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}. Available: {list(TOOLS)}")
    return TOOLS[tool_name](**kwargs)


if __name__ == "__main__":
    print("Available tools:", ", ".join(TOOLS.keys()))

    ifc_path = "C:/Users/OWNER/Desktop/IAAC/T05/AI_SpeedRun/AI-Speed-Run-Week/ifc_models/arc.ifc"

    result = run_tool("dwelling_area", ifc_model_path=ifc_path, min_area=36.0)
    print(result)
