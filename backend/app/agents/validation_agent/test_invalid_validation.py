from backend.app.agents.validation_agent.validation_agent import ValidationAgent


agent = ValidationAgent()

questions = [
    {
        # Missing options and correct_answer
        "question": "What is SQL?",
        "question_type": "normal_mcq",
        "subject": "DBMS",
        "topic": "SQL",
        "difficulty": "L2",
        "options": {},
        "correct_answer": None,
        "explanation": "",
    }
]

state = {
    "questions": questions,
    "requirements": {
        "subject": "DBMS",
        "topic": "SQL",
        "difficulty": "L2",
        "question_mix": {
            "normal_mcq": 1,
            "scenario_mcq": 0,
            "coding": 0,
        },
    },
}

result = agent.run(state)

print("INVALID QUESTION VALIDATION TEST")
print("=" * 40)

for item in result["validation_results"]:
    print(item)

print("\nSTATUS:")
print(result["action"]["status"])