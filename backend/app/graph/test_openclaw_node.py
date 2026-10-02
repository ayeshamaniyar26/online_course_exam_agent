from backend.app.graph.openclaw_node import openclaw_node


state = {
    "run_id": "openclaw-integration-test",
    "trace": [],
    "errors": [],
}

result = openclaw_node(state)

print("OPENCLAW LANGGRAPH NODE TEST")
print("============================")
print("STAGE:", result.get("current_stage"))
print("AGENT:", result.get("current_agent"))
print("OBSERVATION:", result.get("observation"))

if result.get("observation", {}).get("openclaw", {}).get("available"):
    print()
    print("OPENCLAW LANGGRAPH NODE TEST PASSED")
else:
    print()
    print("OPENCLAW GATEWAY NODE REPORTED UNAVAILABLE")
    print("ERROR:", result.get("last_error"))