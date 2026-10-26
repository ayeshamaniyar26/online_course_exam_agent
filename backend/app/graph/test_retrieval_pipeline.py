from backend.app.graph.exam_graph import (
    exam_graph,
    create_exam_state,
    exam_session_node,
)
from backend.app.schemas.exam_request import ExamRequest
from backend.app.schemas.student import Student


# --------------------------------------------------
# 1. CREATE TEST EXAM REQUEST
# --------------------------------------------------

student = Student(
    roll_number=2,
    usn="01FE23BCI002",
    name="Retrieval Test Student",
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


# --------------------------------------------------
# 2. TEST QUESTION RETRIEVAL
# --------------------------------------------------

print("RETRIEVAL PIPELINE TEST")
print("=" * 40)

result = exam_graph.invoke(initial_state)

questions = result.get("questions", [])

# Verify that every retrieved question has a unique ID.
question_ids = [q.get("question_id") for q in questions]

assert all(question_ids), "A retrieved question is missing question_id."
assert len(question_ids) == len(set(question_ids)), (
    "Duplicate question IDs were found."
)

print("PASS: All retrieved questions have unique question IDs.")

validation_results = result.get("validation_results", [])

print("\nTOTAL QUESTIONS:")
print(len(questions))

print("\nFIRST QUESTION STRUCTURE:")
print(questions[0] if questions else "No questions found")

print("\nQUESTION TYPES:")
for question in questions:
    print(question.get("question_type"))

print("\nVALIDATION RESULTS:")
for validation in validation_results:
    print(validation)

print("\nERRORS:")
print(result.get("errors", []))


# --------------------------------------------------
# 3. TEST EXAM SESSION CREATION INDEPENDENTLY
# --------------------------------------------------

print("\n" + "=" * 40)
print("TESTING EXAM SESSION CREATION")
print("=" * 40)

if not questions:
    raise AssertionError("No questions were retrieved.")

# Add test IDs because the current JSON question bank
# does not contain question_id fields.
session_questions = questions

session_state = {
    **initial_state,
    "questions": session_questions,
    "student": student.model_dump(),
    "exam_session": None,
    "errors": [],
    "trace": [],
}

session_result = exam_session_node(session_state)
exam_session = session_result.get("exam_session", {})

assert session_result.get("current_stage") == "exam_session", (
    f"Session creation failed: {session_result.get('errors', [])}"
)

assert exam_session, "No exam session was returned."

assert exam_session.get("student_id") == student.usn, (
    f"Expected student_id {student.usn}, "
    f"got {exam_session.get('student_id')}"
)

assert exam_session.get("session_id"), (
    "The exam session is missing its session_id."
)

print("PASS: Questions were retrieved.")
print("PASS: Exam session created successfully.")
print("PASS: Session student_id matches the student's USN.")
print("PASS: Session has a session_id.")