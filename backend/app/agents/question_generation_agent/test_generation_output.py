from backend.app.agents.question_generation_agent.question_generation_agent import (
    QuestionGenerationAgent,
)


agent = QuestionGenerationAgent()

state = {
    "requirements": {
        "subject": "DBMS",
        "topic": "SQL",
        "difficulty": "L2",
        "question_mix": {
            "normal_mcq": 2,
            "scenario_mcq": 1,
            "coding": 2,
        },
    }
}

result = agent.run(state)

questions = result.get("questions", [])

result = agent.run(state)

questions = result.get("questions", [])

# Verify that every generated question has a question_id.
assert all(q.get("question_id") for q in questions), \
    "Some generated questions are missing question_id."

# Verify that all question IDs are unique.
question_ids = [q["question_id"] for q in questions]

assert len(question_ids) == len(set(question_ids)), \
    "Duplicate question IDs found."

print("PASS: All generated questions have unique IDs.")

print("\nGENERATED QUESTIONS")
print("=" * 70)

print("\nGENERATED QUESTIONS")
print("=" * 70)

for index, question in enumerate(questions, start=1):

    print(f"\nQUESTION {index}")
    print("-" * 70)

    print("TYPE:", question.get("question_type"))
    print("SUBJECT:", question.get("subject"))
    print("TOPIC:", question.get("topic"))
    print("DIFFICULTY:", question.get("difficulty"))

    print("\nQUESTION:")
    print(question.get("question"))

    if question.get("options"):
        print("\nOPTIONS:")
        for key, value in question["options"].items():
            print(f"  {key}. {value}")

    print("\nCORRECT ANSWER:")
    print(question.get("correct_answer"))

    if question.get("expected_answer"):
        print("\nEXPECTED ANSWER:")
        print(question.get("expected_answer"))

    print("\nEXPLANATION:")
    print(question.get("explanation"))

print("\n" + "=" * 70)
print("TOTAL GENERATED:", len(questions))