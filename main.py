from tools import toola, toolb, toolc, toold

TOOLS = {
    "living_area_height": toola.living_area_height_check_tool,
    "service_space_height": toolb.service_spaces_min_height_check_tool,
    "dwelling_area": toolc.dwelling_area_check_tool,
    "living_room_compliance": toold.living_room_compliance_tool,
}

SCHEMAS = {
    "living_area_height": toola.LIVING_AREA_HEIGHT_CHECK_SCHEMA,
    "service_space_height": toolb.SERVICE_SPACES_MIN_HEIGHT_SCHEMA,
    "dwelling_area": toolc.DWELLING_AREA_CHECK_SCHEMA,
    "living_room_compliance": toold.LIVING_ROOM_COMPLIANCE_SCHEMA,
}


def list_tools():
    return SCHEMAS


def run_tool(tool_name: str, **kwargs):
    if tool_name not in TOOLS:
        raise ValueError(
            f"Unknown tool: {tool_name}. Available: {list(TOOLS)}"
        )
    return TOOLS[tool_name](**kwargs)


# --------------------------
# Example run
# --------------------------
if __name__ == "__main__":
    ifc_path = "/content/ifc-bench/projects/duplex/arc.ifc"

    print("Available tools:")
    for t in list_tools():
        print(" -", t)

    print("\nRunning dwelling area check:\n")
    result = run_tool(
        "dwelling_area",
        ifc_model_path=ifc_path,
        min_area=36.0
    )

    print(result)
