from backend.app.graph.mcp_node import mcp_node


state = {
    "requirements": {
        "subject": "Computer Networks",
        "difficulty": "L1",
        "question_count": 5,
    },
    "observation": {},
    "trace": [],
}


print("MCP LANGGRAPH NODE TEST")
print("=======================")

result = mcp_node(state)

print("MCP AVAILABLE:", result["observation"]["mcp"]["available"])
print("MCP TOOL:", result["observation"]["mcp"]["tool"])
print("MCP NODE EXECUTION PASSED")