from backend.app.graph.exam_graph import exam_graph, create_exam_state
from backend.app.schemas.exam_request import ExamRequest
from backend.app.schemas.student import Student


student = Student(
    student_id="TEST001",
    name="Test Student",
    email="test@example.com",
    roll_number="001",
    usn="4XX23AI001",
    division="A",
)

exam_request = ExamRequest(
    student=student,
    subject="DBMS",
    topic="SQL",
    difficulty="L2",
    number_of_questions=5,
    question_mix={
        "normal_mcq": 2,
        "scenario_mcq": 1,
        "coding": 2,
    },
)

initial_state = create_exam_state(exam_request)

print("FULL QUESTION PIPELINE TEST")
print("=" * 40)

print("\nTEACHER REQUIREMENTS:")
print(initial_state["requirements"])

result = exam_graph.invoke(initial_state)

print("\nTOTAL QUESTIONS:")
print(len(result.get("questions", [])))

print("\nQUESTION TYPES:")
for question in result.get("questions", []):
    print(question.get("question_type"))

print("\nVALIDATION RESULTS:")
for validation in result.get("validation_results", []):
    print(validation)

print("\nTRACE:")
for trace in result.get("trace", []):
    print(trace)

print("\nERRORS:")
print(result.get("errors", []))