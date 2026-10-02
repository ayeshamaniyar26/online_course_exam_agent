from backend.app.graph.exam_graph import exam_graph


initial_state = {
    "run_id": "openclaw-full-route-test",
    "student": {},
    "exam_id": "test",
    "goal": "Test complete agentic OpenClaw route",
    "requirements": {
        "task": "execute_openclaw"
    },
    "current_stage": "question_generation",
    "current_agent": "coordinator",
    "questions": [],
    "answers": [],
    "validation_results": [],
    "evaluation_results": [],
    "final_result": None,
    "retry_count": 0,
    "errors": [],
    "max_retries": 0,
    "last_error": None,
    "trace": [],
    "perception": {},
    "plan": {},
    "action": {},
    "observation": {},
    "revision": {
        "status": "continue"
    },
    "iteration_count": 0,
}


print("FULL AGENTIC OPENCLAW ROUTE TEST")
print("=================================")

result = exam_graph.invoke(initial_state)

print()
print("FINAL STAGE:", result.get("current_stage"))
print("CURRENT AGENT:", result.get("current_agent"))
print("TRACE:")

for item in result.get("trace", []):
    print(item)

print()
print("OBSERVATION:")
print(result.get("observation", {}))