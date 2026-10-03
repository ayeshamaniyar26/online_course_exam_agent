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