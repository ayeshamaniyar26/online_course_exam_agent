from backend.app.agents.validation_agent.validation_agent import ValidationAgent


agent = ValidationAgent()

questions = [
    {
        "question": "What is normalization in DBMS?",
        "question_type": "normal_mcq",
        "options": {
            "A": "Reducing redundancy",
            "B": "Increasing redundancy",
            "C": "Deleting databases",
            "D": "Creating indexes",
        },
        "correct_answer": "A",
        "explanation": "Normalization reduces redundancy.",
        "subject": "DBMS",
        "topic": "SQL",
        "difficulty": "L2",
    },
    {
        "question": "What is normalization in DBMS?",
        "question_type": "normal_mcq",
        "options": {
            "A": "Reducing redundancy",
            "B": "Increasing redundancy",
            "C": "Deleting databases",
            "D": "Creating indexes",
        },
        "correct_answer": "A",
        "explanation": "Normalization reduces redundancy.",
        "subject": "DBMS",
        "topic": "SQL",
        "difficulty": "L2",
    },
]

state = {
    "questions": questions,
    "requirements": {
        "subject": "DBMS",
        "topic": "SQL",
        "difficulty": "L2",
        "question_mix": {
            "normal_mcq": 2,
            "scenario_mcq": 0,
            "coding": 0,
        },
    },
}

result = agent.run(state)

print("DUPLICATE VALIDATION TEST")
print("=" * 35)

for item in result["validation_results"]:
    print(item)

print("\nSTATUS:")
print(result["action"]["status"])