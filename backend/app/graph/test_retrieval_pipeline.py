from backend.app.graph.exam_graph import exam_graph, create_exam_state
from backend.app.schemas.exam_request import ExamRequest
from backend.app.schemas.student import Student


student = Student(
    student_id="TEST002",
    name="Retrieval Test Student",
    email="retrieval@test.com",
    roll_number="002",
    usn="4XX23AI002",
    division="A",
)

exam_request = ExamRequest(
    student=student,
    subject="DBMS",
    topic="Introduction to DBMS",
    difficulty="L1",
    number_of_questions=3,
    question_mix={
        "normal_mcq": 3,
        "scenario_mcq": 0,
        "coding": 0,
    },
)

initial_state = create_exam_state(exam_request)

print("RETRIEVAL PIPELINE TEST")
print("=" * 40)

result = exam_graph.invoke(initial_state)

questions = result.get("questions", [])
validation_results = result.get("validation_results", [])

print("\nTOTAL QUESTIONS:")
print(len(questions))

print("\nQUESTION TYPES:")
for question in questions:
    print(question.get("question_type"))

print("\nFIRST QUESTION:")
if questions:
    print(questions[0].get("question"))

print("\nVALIDATION RESULTS:")
for validation in validation_results:
    print(validation)

print("\nTRACE:")
for trace in result.get("trace", []):
    print(trace)

print("\nERRORS:")
print(result.get("errors", []))