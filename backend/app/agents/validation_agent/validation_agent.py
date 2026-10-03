from typing import Any, Dict

from backend.app.schemas.agent_state import AgentState


class ValidationAgent:
    """
    Validate retrieved or Gemini-generated examination questions.

    Validation is structural and requirement-based. It checks that
    questions are complete and suitable to enter the examination flow.
    """

    def run(self, state: AgentState) -> Dict[str, Any]:
        questions = state.get("questions", [])
        requirements = state.get("requirements", {})

        validation_results = []
        valid_questions = []

        duplicate_indexes = self._find_duplicate_questions(questions)

        # --------------------------------------------------------
        # 1. Validate each question individually
        # --------------------------------------------------------

        for index, question in enumerate(questions, start=1):
            errors = self._validate_question(question, requirements)

            zero_based_index = index - 1

            if zero_based_index in duplicate_indexes:
                errors.append("Duplicate question detected.")

            result = {
                "question_index": index,
                "valid": len(errors) == 0,
                "errors": errors,
            }

            validation_results.append(result)

            if not errors:
                valid_questions.append(question)

        # --------------------------------------------------------
        # 2. Validate the teacher-requested question distribution
        # --------------------------------------------------------

        question_mix = requirements.get("question_mix")

        mix_errors = []

        if question_mix:
            expected_mix = {
                "normal_mcq": int(question_mix.get("normal_mcq", 0)),
                "scenario_mcq": int(question_mix.get("scenario_mcq", 0)),
                "coding": int(question_mix.get("coding", 0)),
            }

            actual_mix = {
                "normal_mcq": 0,
                "scenario_mcq": 0,
                "coding": 0,
            }

            for question in questions:
                question_type = question.get("question_type")

                if question_type in actual_mix:
                    actual_mix[question_type] += 1

            for question_type, expected_count in expected_mix.items():
                actual_count = actual_mix[question_type]

                if actual_count != expected_count:
                    mix_errors.append(
                        f"{question_type}: expected {expected_count}, "
                        f"but received {actual_count}."
                    )

        # --------------------------------------------------------
        # 3. Overall validation status
        # --------------------------------------------------------

        all_questions_valid = (
            len(valid_questions) == len(questions)
        )

        mix_valid = len(mix_errors) == 0

        all_valid = all_questions_valid and mix_valid

        return {
            "current_agent": "validation_agent",
            "action": {
                "type": "validate_questions",
                "question_count": len(questions),
                "valid_count": len(valid_questions),
                "invalid_count": len(questions) - len(valid_questions),
                "status": "passed" if all_valid else "failed",
                "expected_mix": (
                    expected_mix if question_mix else None
                ),
                "actual_mix": (
                    actual_mix if question_mix else None
                ),
                "mix_errors": mix_errors,
            },
            "validation_results": validation_results,
            "questions": valid_questions,
            "trace_entry": {
                "agent": "validation_agent",
                "action": "validate_questions",
                "question_count": len(questions),
                "valid_count": len(valid_questions),
                "invalid_count": len(questions) - len(valid_questions),
                "mix_valid": mix_valid,
                "expected_mix": (
                    expected_mix if question_mix else None
                ),
                "actual_mix": (
                    actual_mix if question_mix else None
                ),
            },
        }


    def _find_duplicate_questions(
        self,
        questions: list[dict[str, Any]],
    ) -> set[int]:
        """Find duplicate questions using normalized question text."""

        seen = {}
        duplicates = set()

        for index, question in enumerate(questions):
            text = question.get("question", "").strip().lower()

            if not text:
                continue

            if text in seen:
                duplicates.add(index)
            else:
                seen[text] = index

        return duplicates

    def _validate_question(
        self,
        question: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> list[str]:

        errors = []

        # --------------------------------------------------
        # Common required fields
        # --------------------------------------------------

        if not question.get("question"):
            errors.append("Question text is missing.")

        if not question.get("subject"):
            errors.append("Subject is missing.")

        if not question.get("difficulty"):
            errors.append("Difficulty is missing.")

        question_type = question.get("question_type")

        if not question_type:
            errors.append("Question type is missing.")

        # --------------------------------------------------
        # Subject validation
        # --------------------------------------------------

        expected_subject = requirements.get("subject")

        if (
            expected_subject
            and question.get("subject", "").strip().lower()
            != expected_subject.strip().lower()
        ):
            errors.append("Question subject does not match the requested subject.")

        # --------------------------------------------------
        # Difficulty validation
        # --------------------------------------------------

        expected_difficulty = requirements.get("difficulty")

        if (
            expected_difficulty
            and question.get("difficulty", "").strip().upper()
            != expected_difficulty.strip().upper()
        ):
            errors.append(
                "Question difficulty does not match the requested difficulty."
            )

        # --------------------------------------------------
        # MCQ validation
        # --------------------------------------------------

        if question_type in {"normal_mcq", "scenario_mcq"}:

            options = question.get("options")

            if not isinstance(options, dict):
                errors.append("MCQ options must be a dictionary.")
            else:
                expected_options = {"A", "B", "C", "D"}

                if set(options.keys()) != expected_options:
                    errors.append(
                        "MCQ must contain exactly A, B, C and D options."
                    )

                for key in expected_options:
                    if not options.get(key):
                        errors.append(
                            f"MCQ option {key} is empty."
                        )

            correct_answer = question.get("correct_answer")

            if correct_answer not in {"A", "B", "C", "D"}:
                errors.append(
                    "MCQ correct_answer must be A, B, C or D."
                )

            if not question.get("explanation"):
                errors.append("MCQ explanation is missing.")

        # --------------------------------------------------
        # Coding question validation
        # --------------------------------------------------

        elif question_type == "coding":

            expected_answer = question.get("expected_answer")

            if not expected_answer:
                errors.append(
                    "Coding question expected_answer is missing."
                )

            # Coding questions should not require MCQ options.
            options = question.get("options", {})

            if options not in ({}, None):
                errors.append(
                    "Coding questions should not contain MCQ options."
                )

        else:
            errors.append(
                f"Unsupported question type: {question_type}"
            )

        return errors