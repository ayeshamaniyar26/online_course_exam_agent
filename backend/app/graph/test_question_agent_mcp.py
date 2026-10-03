from backend.app.agents.question_agent.question_agent import QuestionAgent
from backend.app.graph.mcp_node import mcp_node


print("QUESTION AGENT -> MCP INTEGRATION TEST")
print("======================================")

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

# Step 1: Question Agent prepares the retrieval request
question_agent = QuestionAgent()
agent_result = question_agent.run(state)

print("QUESTION AGENT ACTION:")
print(agent_result["action"])

# Put Question Agent's action into the state
state["action"] = agent_result["action"]

# Step 2: MCP retrieves the questions
mcp_result = mcp_node(state)

print()
print("MCP AVAILABLE:", mcp_result["observation"]["mcp"]["available"])
print("MCP TOOL:", mcp_result["observation"]["mcp"]["tool"])
print("QUESTIONS RETRIEVED:", len(mcp_result["questions"]))

if mcp_result["questions"]:
    print("FIRST QUESTION:")
    print(mcp_result["questions"][0]["question"])

print()
print("QUESTION AGENT -> MCP INTEGRATION PASSED")