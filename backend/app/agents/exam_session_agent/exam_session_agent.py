from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from uuid import uuid4

from backend.app.schemas.exam_session import (
    ExamSession,
    ExamSessionStatus,
    StudentAnswer,
)


class ExamSessionAgent:
    """
    Friend 3: Practice / Exam Session Agent.

    Responsibilities:
    - create session
    - start session
    - deliver student-safe questions
    - submit/store student answers
    - track progress
    - submit exam
    - expire exam
    - preserve answers after expiry/submission

    Evaluation/scoring is handled by Friend 4.
    """

    # ============================================================
    # SESSION CREATION
    # ============================================================

    def create_session(
        self,
        exam_id: str,
        student_id: str,
        questions: List[Dict[str, Any]],
        duration_minutes: int = 30,
    ) -> ExamSession:
        """Create a new exam/practice session."""

        if not exam_id:
            raise ValueError("exam_id is required.")

        if not student_id:
            raise ValueError("student_id is required.")

        if duration_minutes <= 0:
            raise ValueError(
                "duration_minutes must be greater than zero."
            )

        now = datetime.now(timezone.utc)

        return ExamSession(
            session_id=str(uuid4()),
            exam_id=exam_id,
            student_id=student_id,
            status=ExamSessionStatus.NOT_STARTED,
            started_at=None,
            ends_at=now + timedelta(minutes=duration_minutes),
            submitted_at=None,
            current_question_index=0,
            answers={},
            total_questions=len(questions),
            answered_questions=0,
        )

    # ============================================================
    # START SESSION
    # ============================================================

    def start_session(
        self,
        session: ExamSession,
    ) -> ExamSession:
        """Start a NOT_STARTED session."""

        if session.status != ExamSessionStatus.NOT_STARTED:
            raise ValueError(
                f"Session cannot be started from status: "
                f"{session.status.value}"
            )

        now = datetime.now(timezone.utc)

        if session.ends_at is None:
            raise ValueError(
                "Session deadline is not configured."
            )

        remaining_seconds = (
            session.ends_at - now
        ).total_seconds()

        if remaining_seconds <= 0:
            session.status = ExamSessionStatus.EXPIRED

            raise ValueError(
                "Session duration has already expired."
            )

        session.status = ExamSessionStatus.IN_PROGRESS
        session.started_at = now

        # Keep the original remaining duration.
        session.ends_at = now + timedelta(
            seconds=remaining_seconds
        )

        return session

    # ============================================================
    # QUESTION DELIVERY
    # ============================================================

    def get_questions(
        self,
        session: ExamSession,
        questions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Return student-safe questions.

        NEVER expose:
        - correct_answer
        - expected_answer
        - explanation
        - source
        - metadata
        """

        self._ensure_active(session)

        safe_questions: List[Dict[str, Any]] = []

        for question in questions:

            question_id = question.get("question_id")

            if not question_id:
                raise ValueError(
                    "Every question must have a question_id."
                )

            safe_question = {
                "question_id": question_id,
                "subject": question.get("subject"),
                "topic": question.get("topic"),
                "difficulty": question.get("difficulty"),
                "question_type": question.get(
                    "question_type",
                    "normal_mcq",
                ),
                "question": question.get("question"),
                "options": question.get("options", {}),
            }

            safe_questions.append(safe_question)

        return safe_questions

    # ============================================================
    # SINGLE ANSWER
    # ============================================================

    def submit_answer(
        self,
        session: ExamSession,
        question_id: str,
        answer: str,
    ) -> ExamSession:
        """
        Store one student's answer.

        This method DOES NOT evaluate correctness.
        Friend 4 handles evaluation.
        """

        self._ensure_active(session)

        if not question_id:
            raise ValueError(
                "question_id is required."
            )

        if not isinstance(answer, str):
            raise ValueError(
                "answer must be a string."
            )

        now = datetime.now(timezone.utc)

        is_new_answer = (
            question_id not in session.answers
        )

        session.answers[question_id] = StudentAnswer(
            question_id=question_id,
            answer=answer,
            answered_at=now,
        )

        if is_new_answer:
            session.answered_questions += 1

        return session

    # ============================================================
    # MULTIPLE ANSWERS
    # ============================================================

    def submit_answers(
        self,
        session: ExamSession,
        answers: List[Dict[str, Any]],
    ) -> ExamSession:
        """
        Store multiple student answers.

        Expected format:

        [
            {
                "question_id": "q1",
                "answer": "A"
            },
            {
                "question_id": "q2",
                "answer": "SELECT ..."
            }
        ]

        Existing answers can be updated without increasing
        answered_questions again.
        """

        self._ensure_active(session)

        for item in answers:

            if not isinstance(item, dict):
                raise ValueError(
                    "Each answer must be a dictionary."
                )

            question_id = item.get("question_id")
            answer = item.get("answer")

            if not question_id:
                raise ValueError(
                    "Each answer requires question_id."
                )

            if answer is None:
                raise ValueError(
                    f"Answer missing for question: {question_id}"
                )

            self.submit_answer(
                session=session,
                question_id=question_id,
                answer=str(answer),
            )

        return session

    # ============================================================
    # PROGRESS
    # ============================================================

    def get_progress(
        self,
        session: ExamSession,
    ) -> Dict[str, Any]:
        """
        Return current exam progress.
        """

        if session.status == ExamSessionStatus.IN_PROGRESS:

            now = datetime.now(timezone.utc)

            if session.ends_at is not None and now >= session.ends_at:
                self.expire_session(session)

        remaining_questions = max(
            session.total_questions
            - session.answered_questions,
            0,
        )

        current_question_number = (
            session.current_question_index + 1
        )

        return {
            "session_id": session.session_id,
            "exam_id": session.exam_id,
            "student_id": session.student_id,
            "status": session.status.value,
            "current_question_index": (
                session.current_question_index
            ),
            "current_question_number": (
                current_question_number
            ),
            "total_questions": (
                session.total_questions
            ),
            "answered_questions": (
                session.answered_questions
            ),
            "remaining_questions": (
                remaining_questions
            ),
            "started_at": session.started_at,
            "ends_at": session.ends_at,
            "submitted_at": session.submitted_at,
        }

    # ============================================================
    # MOVE TO NEXT QUESTION
    # ============================================================

    # 
    
    # ============================================================
    # NEXT QUESTION
    # ============================================================

    def next_question(
        self,
        session: ExamSession,
        questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Move to the next question and return the
        student-safe question.

        Sensitive fields such as:
        - correct_answer
        - expected_answer
        - explanation
        - source
        - metadata

        are never returned.
        """

        self._ensure_active(session)

        if not questions:
            raise ValueError(
                "No questions available."
            )

        next_index = session.current_question_index + 1

        if next_index >= len(questions):
            raise ValueError(
                "Already at the last question."
            )

        session.current_question_index = next_index

        return self.get_current_question(
            session,
            questions,
        )

    # ============================================================
    # SUBMIT EXAM
    # ============================================================

    def submit_session(
        self,
        session: ExamSession,
    ) -> ExamSession:
        """
        Submit and lock the exam session.

        No evaluation happens here.
        """

        if session.status != ExamSessionStatus.IN_PROGRESS:
            raise ValueError(
                "Only an active session can be submitted."
            )

        now = datetime.now(timezone.utc)

        if session.ends_at is None:
            raise ValueError(
                "Session deadline is not configured."
            )

        if now >= session.ends_at:
            return self.expire_session(session)

        session.status = ExamSessionStatus.SUBMITTED
        session.submitted_at = now

        return session

    # ============================================================
    # EXPIRE SESSION
    # ============================================================

    def expire_session(
        self,
        session: ExamSession,
    ) -> ExamSession:
        """
        Expire an exam session.

        Existing student answers are preserved.
        """

        if session.status == ExamSessionStatus.SUBMITTED:
            raise ValueError(
                "Submitted sessions cannot be expired."
            )

        if session.status == ExamSessionStatus.EXPIRED:
            return session

        session.status = ExamSessionStatus.EXPIRED

        if session.submitted_at is None:
            session.submitted_at = datetime.now(
                timezone.utc
            )

        return session

    # ============================================================
    # INTERNAL ACTIVE-SESSION CHECK
    # ============================================================

    def _ensure_active(
        self,
        session: ExamSession,
    ) -> None:
        """
        Central safety check for all student actions.
        """

        if session.status != ExamSessionStatus.IN_PROGRESS:
            raise ValueError(
                "Session must be active."
            )

        now = datetime.now(timezone.utc)

        if session.ends_at is None:
            raise ValueError(
                "Session deadline is not configured."
            )

        if now >= session.ends_at:
            self.expire_session(session)

            raise ValueError(
                "The examination session has expired."
            )
    # ============================================================
    # CURRENT QUESTION
    # ============================================================

    def get_current_question(
        self,
        session: ExamSession,
        questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Return the current student-safe question.

        Uses the session's current_question_index.
        Sensitive answer/evaluation fields are never exposed.
        """

        self._ensure_active(session)

        if not questions:
            raise ValueError(
                "No questions available."
            )

        index = session.current_question_index

        if index < 0 or index >= len(questions):
            raise ValueError(
                "Current question index is out of range."
            )

        question = questions[index]

        question_id = question.get("question_id")

        if not question_id:
            raise ValueError(
                "Every question must have a question_id."
            )

        return {
            "question_id": question_id,
            "subject": question.get("subject"),
            "topic": question.get("topic"),
            "difficulty": question.get("difficulty"),
            "question_type": question.get(
                "question_type",
                "normal_mcq",
            ),
            "question": question.get("question"),
            "options": question.get("options", {}),
        }
