from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    run_id: str

    # Student identity
    student: Dict[str, Any]

    # Examination information
    exam_id: str
    exam_session: Dict[str, Any]

    # Overall requirement/goal
    goal: str
    requirements: Dict[str, Any]

    # Current orchestration status
    current_stage: str
    current_agent: str

    # Question-related data
    # Original validated questions are kept here.
    # These may contain answer keys for downstream evaluation.
    questions: List[Dict[str, Any]]

    # Student-facing questions.
    # Sensitive fields such as correct_answer,
    # expected_answer, explanation, source and metadata
    # are removed before storing here.
    student_questions: List[Dict[str, Any]]

    # Student answers already stored in the exam session.
    answers: List[Dict[str, Any]]

    # Answers waiting to be submitted by the student.
    pending_answers: List[Dict[str, Any]]

    # Request to submit/lock the current exam session.
    submit_exam: bool

    # Validation information
    validation_results: List[Dict[str, Any]]

    # Evaluation information
    evaluation_results: List[Dict[str, Any]]

    # Final system output
    final_result: Optional[Dict[str, Any]]

    # Error and retry information
    retry_count: int
    errors: List[str]

    # Execution trace
    trace: List[Dict[str, Any]]

    # Agentic reasoning cycle
    perception: Dict[str, Any]
    plan: Dict[str, Any]
    action: Dict[str, Any]
    observation: Dict[str, Any]
    revision: Dict[str, Any]

    # Number of agentic iterations
    iteration_count: int