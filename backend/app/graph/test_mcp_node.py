from backend.app.graph.mcp_node import mcp_node


state = {
    "requirements": {
        "subject": "DBMS",
        "topic": "Introduction to DBMS",
        "difficulty": "L1",
        "count": 3,
    },
    "questions": [],
    "observation": {},
    "trace": [],
}


print("MCP LANGGRAPH NODE TEST")
print("=======================")

result = mcp_node(state)

print("MCP AVAILABLE:", result["observation"]["mcp"]["available"])
print("MCP TOOL:", result["observation"]["mcp"]["tool"])
print("QUESTIONS RETRIEVED:", len(result["questions"]))

if result["questions"]:
    print("FIRST QUESTION:")
    print(result["questions"][0]["question"])

print("MCP NODE EXECUTION PASSED")