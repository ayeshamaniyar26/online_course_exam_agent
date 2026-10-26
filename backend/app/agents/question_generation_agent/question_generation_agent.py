# import json
# import os
# from typing import Any, Dict

# from dotenv import load_dotenv
# from google import genai

# load_dotenv()

# from backend.app.schemas.agent_state import AgentState


# class QuestionGenerationAgent:
#     """
#     Generate questions using Gemini according to the teacher's
#     requested question mix.
#     """

#     def __init__(self):
#         api_key = os.getenv("GEMINI_API_KEY")

#         if not api_key:
#             raise RuntimeError(
#                 "GEMINI_API_KEY environment variable is not set."
#             )

#         self.client = genai.Client(api_key=api_key)
#         self.model = "gemini-3.8-flash"

#     def run(self, state: AgentState) -> Dict[str, Any]:
#         requirements = state.get("requirements", {})

#         subject = requirements.get("subject")
#         topic = requirements.get("topic")
#         difficulty = requirements.get("difficulty", "L1")

#         question_mix = requirements.get("question_mix")

#         # Backward compatibility with the old format.
#         if not question_mix:
#             count = requirements.get(
#                 "count",
#                 requirements.get("number_of_questions", 5),
#             )

#             question_mix = {
#                 "normal_mcq": count,
#                 "scenario_mcq": 0,
#                 "coding": 0,
#             }

#         question_mix = {
#             "normal_mcq": int(question_mix.get("normal_mcq", 0)),
#             "scenario_mcq": int(question_mix.get("scenario_mcq", 0)),
#             "coding": int(question_mix.get("coding", 0)),
#         }

#         total_required = sum(question_mix.values())

#         existing_questions = state.get("questions", [])

#         missing_count = max(
#             total_required - len(existing_questions),
#             0,
#         )

#         if missing_count == 0:
#             return {
#                 "current_agent": "question_generation_agent",
#                 "action": {
#                     "type": "generation_not_required",
#                     "status": "complete",
#                 },
#                 "trace_entry": {
#                     "agent": "question_generation_agent",
#                     "action": "generation_not_required",
#                 },
#             }

#         prompt = self._build_prompt(
#             subject=subject,
#             topic=topic,
#             difficulty=difficulty,
#             question_mix=question_mix,
#         )

#         response = self.client.models.generate_content(
#             model=self.model,
#             contents=prompt,
#         )

#         questions = self._parse_response(response.text)

#         return {
#             "current_agent": "question_generation_agent",
#             "action": {
#                 "type": "generate_questions",
#                 "requirements": {
#                     "subject": subject,
#                     "topic": topic,
#                     "difficulty": difficulty,
#                     "question_mix": question_mix,
#                     "count": total_required,
#                 },
#                 "questions": questions,
#             },
#             "questions": existing_questions + questions,
#             "trace_entry": {
#                 "agent": "question_generation_agent",
#                 "action": "generate_questions",
#                 "generated_count": len(questions),
#                 "question_mix": question_mix,
#             },
#         }

#     def _build_prompt(
#         self,
#         subject: str,
#         topic: str | None,
#         difficulty: str,
#         question_mix: Dict[str, int],
#     ) -> str:
#         """
#         Build a Gemini prompt directly from teacher requirements.
#         """

#         topic_text = topic or "any suitable topic"

#         normal_mcq_count = question_mix["normal_mcq"]
#         scenario_mcq_count = question_mix["scenario_mcq"]
#         coding_count = question_mix["coding"]

#         coding_instruction = ""

#         if coding_count > 0:
#             if subject.upper() == "DBMS":
#                 coding_instruction = """
# For coding questions:
# - Create scenario-based SQL problems.
# - Give the database scenario and relevant tables.
# - Ask the student to write the SQL query themselves.
# - Do NOT give SQL code in the question.
# - Include the expected SQL answer separately for later evaluation.
# - These are NOT MCQs.
# """
#             elif subject.upper() == "OOPS":
#                 coding_instruction = """
# For coding questions:
# - Create scenario-based OOPS programming problems.
# - Describe the required functionality clearly.
# - Ask the student to write the program/code themselves.
# - Do NOT provide the complete solution in the question.
# - Include an expected solution separately for later evaluation.
# - These are NOT MCQs.
# """
#             else:
#                 coding_instruction = """
# For coding questions:
# - Create a scenario-based programming problem.
# - Ask the student to write the solution themselves.
# - Do NOT provide the solution in the question.
# - Include an expected solution separately for later evaluation.
# - These are NOT MCQs.
# """

#         prompt = f"""
# You are an examination Question Generation Agent.

# The teacher has selected the following requirements:

# Subject: {subject}
# Topic: {topic_text}
# Difficulty: {difficulty}

# Question distribution requested by the teacher:
# - Normal MCQ: {normal_mcq_count}
# - Scenario-based MCQ: {scenario_mcq_count}
# - Coding/Scenario questions: {coding_count}

# IMPORTANT:
# Generate EXACTLY the requested number of each type.
# Do not change the distribution.

# Normal MCQ:
# - Standard conceptual or application-based MCQ.
# - Four options: A, B, C, D.
# - Exactly one correct answer.

# Scenario-based MCQ:
# - Give a realistic scenario.
# - Ask a question based on that scenario.
# - Student answers by selecting A, B, C, or D.
# - Four options are required.
# - Exactly one correct answer.

# {coding_instruction}

# Return ONLY valid JSON.
# Do not use Markdown.
# Do not add any text outside the JSON.

# Use this structure:

# {{
#   "questions": [
#     {{
#       "question": "Question text",
#       "question_type": "normal_mcq",
#       "options": {{
#         "A": "Option A",
#         "B": "Option B",
#         "C": "Option C",
#         "D": "Option D"
#       }},
#       "correct_answer": "A",
#       "explanation": "Explanation",
#       "subject": "{subject}",
#       "topic": "{topic_text}",
#       "difficulty": "{difficulty}",
#       "source": "gemini"
#     }}
#   ]
# }}

# For scenario coding questions, use this structure instead:

# {{
#   "question": "Scenario and task given to the student",
#   "question_type": "coding",
#   "options": {{}},
#   "correct_answer": null,
#   "expected_answer": "Expected SQL/code solution",
#   "explanation": "Explanation of the expected solution",
#   "subject": "{subject}",
#   "topic": "{topic_text}",
#   "difficulty": "{difficulty}",
#   "source": "gemini"
# }}
# """

#         return prompt

#     def _parse_response(self, response_text: str) -> list[dict[str, Any]]:
#         response_text = response_text.strip()

#         # Gemini may wrap valid JSON inside Markdown code fences.
#         if response_text.startswith("```"):
#             lines = response_text.splitlines()

#             # Remove opening ```json / ```
#             if lines and lines[0].strip().startswith("```"):
#                 lines = lines[1:]

#             # Remove closing ```
#             if lines and lines[-1].strip() == "```":
#                 lines = lines[:-1]

#             response_text = "\n".join(lines).strip()

#         try:
#             data = json.loads(response_text)
#         except json.JSONDecodeError as exc:
#             print("========== GEMINI RAW RESPONSE ==========")
#             print(response_text)
#             print("=========================================")
#             raise ValueError(
#                 "Gemini returned invalid JSON."
#             ) from exc

#         questions = data.get("questions")

#         if not isinstance(questions, list):
#             raise ValueError(
#                 "Gemini response does not contain a valid questions list."
#             )

#         return questions


import json
import os
from typing import Any, Dict
from uuid import uuid4

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.app.schemas.agent_state import AgentState


load_dotenv()


class QuestionGenerationAgent:
    """
    Generate examination questions using Gemini.

    Flow:
        Teacher requirements
            -> Gemini generation
            -> JSON parsing
            -> LangGraph state
            -> Validation Agent
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite",
        )

    def run(self, state: AgentState) -> Dict[str, Any]:
        requirements = state.get("requirements", {})

        subject = requirements.get("subject")
        topic = requirements.get("topic")
        difficulty = requirements.get(
            "difficulty",
            "L1",
        )

        question_mix = requirements.get(
            "question_mix"
        )

        # --------------------------------------------------
        # Backward compatibility
        # --------------------------------------------------
        if not question_mix:
            count = requirements.get(
                "count",
                requirements.get(
                    "number_of_questions",
                    5,
                ),
            )

            question_mix = {
                "normal_mcq": count,
                "scenario_mcq": 0,
                "coding": 0,
            }

        question_mix = {
            "normal_mcq": int(
                question_mix.get(
                    "normal_mcq",
                    0,
                )
            ),
            "scenario_mcq": int(
                question_mix.get(
                    "scenario_mcq",
                    0,
                )
            ),
            "coding": int(
                question_mix.get(
                    "coding",
                    0,
                )
            ),
        }

        total_required = sum(
            question_mix.values()
        )

        existing_questions = state.get(
            "questions",
            [],
        )

        # --------------------------------------------------
        # Check whether generation is required
        # --------------------------------------------------
        missing_count = max(
            total_required
            - len(existing_questions),
            0,
        )

        if missing_count == 0:
            return {
                "current_agent": (
                    "question_generation_agent"
                ),
                "action": {
                    "type": (
                        "generation_not_required"
                    ),
                    "status": "complete",
                },
                "trace_entry": {
                    "agent": (
                        "question_generation_agent"
                    ),
                    "action": (
                        "generation_not_required"
                    ),
                },
            }

        # --------------------------------------------------
        # Build prompt
        # --------------------------------------------------
        prompt = self._build_prompt(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            question_mix=question_mix,
        )

        print(
            "[QuestionGenerationAgent] "
            f"Generating {missing_count} question(s) "
            f"using {self.model}"
        )

        # --------------------------------------------------
        # Gemini generation
        # --------------------------------------------------
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        if response is None:
            raise RuntimeError(
                "Gemini returned no response."
            )

        response_text = getattr(
            response,
            "text",
            None,
        )

        if not response_text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        # --------------------------------------------------
        # Parse generated JSON
        # --------------------------------------------------
        questions = self._parse_response(
            response_text
        )

        # --------------------------------------------------
        # Return updated LangGraph state
        # --------------------------------------------------
        return {
            "current_agent": (
                "question_generation_agent"
            ),
            "action": {
                "type": "generate_questions",
                "requirements": {
                    "subject": subject,
                    "topic": topic,
                    "difficulty": difficulty,
                    "question_mix": question_mix,
                    "count": total_required,
                },
                "questions": questions,
            },
            "questions": (
                existing_questions
                + questions
            ),
            "trace_entry": {
                "agent": (
                    "question_generation_agent"
                ),
                "action": "generate_questions",
                "generated_count": len(
                    questions
                ),
                "question_mix": question_mix,
            },
        }

    def _build_prompt(
        self,
        subject: str,
        topic: str | None,
        difficulty: str,
        question_mix: Dict[str, int],
    ) -> str:
        """
        Build the Gemini generation prompt.
        """

        topic_text = (
            topic
            or "any suitable topic"
        )

        normal_mcq_count = (
            question_mix["normal_mcq"]
        )

        scenario_mcq_count = (
            question_mix["scenario_mcq"]
        )

        coding_count = (
            question_mix["coding"]
        )

        coding_instruction = ""

        if coding_count > 0:

            if subject.upper() == "DBMS":

                coding_instruction = """
For coding questions:

- Create scenario-based SQL problems.
- Provide the database scenario.
- Provide relevant table definitions.
- Ask the student to write the SQL query.
- Do NOT provide SQL code in the question.
- Include the expected SQL solution separately.
- These are NOT MCQs.
"""

            elif subject.upper() == "OOPS":

                coding_instruction = """
For coding questions:

- Create scenario-based OOPS programming problems.
- Clearly describe the required functionality.
- Ask the student to write the program.
- Do NOT provide the complete solution.
- Include the expected solution separately.
- These are NOT MCQs.
"""

            else:

                coding_instruction = """
For coding questions:

- Create a programming scenario.
- Ask the student to write the solution.
- Do NOT provide the solution in the question.
- Include the expected solution separately.
- These are NOT MCQs.
"""

        prompt = f"""
You are an examination Question Generation Agent.

Generate examination questions according to
the teacher's requirements.

Subject:
{subject}

Topic:
{topic_text}

Difficulty:
{difficulty}

Required question distribution:

Normal MCQ:
{normal_mcq_count}

Scenario-based MCQ:
{scenario_mcq_count}

Coding:
{coding_count}

IMPORTANT RULES:

1. Generate EXACTLY the requested number.
2. Do NOT change the requested distribution.
3. Do NOT generate fewer questions.
4. Do NOT generate additional questions.
5. Every normal MCQ must contain exactly four options.
6. Every scenario MCQ must contain exactly four options.
7. MCQs must have exactly one correct answer.
8. Coding questions must not reveal the solution.
9. Coding questions must contain an expected_answer.
10. Return ONLY JSON.

{coding_instruction}

Return this exact JSON structure:

{{
    "questions": [
        {{
            "question": "Question text",
            "question_type": "normal_mcq",
            "options": {{
                "A": "Option A",
                "B": "Option B",
                "C": "Option C",
                "D": "Option D"
            }},
            "correct_answer": "A",
            "explanation": "Explanation",
            "subject": "{subject}",
            "topic": "{topic_text}",
            "difficulty": "{difficulty}",
            "source": "gemini"
        }}
    ]
}}

For coding questions use:

{{
    "question": "Scenario and task",
    "question_type": "coding",
    "options": {{}},
    "correct_answer": null,
    "expected_answer": "Expected SQL or code solution",
    "explanation": "Explanation",
    "subject": "{subject}",
    "topic": "{topic_text}",
    "difficulty": "{difficulty}",
    "source": "gemini"
}}
"""

        return prompt

    def _parse_response(
        self,
        response_text: str,
    ) -> list[dict[str, Any]]:
        """
        Parse Gemini JSON response.
        """

        response_text = (
            response_text.strip()
        )

        # Safety fallback in case Gemini still
        # returns markdown fences.
        if response_text.startswith("```"):

            lines = (
                response_text.splitlines()
            )

            if (
                lines
                and lines[0]
                .strip()
                .startswith("```")
            ):
                lines = lines[1:]

            if (
                lines
                and lines[-1]
                .strip()
                == "```"
            ):
                lines = lines[:-1]

            response_text = (
                "\n".join(lines)
                .strip()
            )

        try:

            data = json.loads(
                response_text
            )

        except json.JSONDecodeError as exc:

            print(
                "\n========== GEMINI RAW RESPONSE =========="
            )

            print(response_text)

            print(
                "==========================================\n"
            )

            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc

        questions = data.get(
            "questions"
        )

        if not isinstance(
            questions,
            list,
        ):
            raise ValueError(
                "Gemini response does not contain "
                "a valid questions list."
            )

        # Assign unique IDs to generated questions.
        for question in questions:
            question.setdefault(
                "question_id",
                f"GENERATED_{uuid4().hex}",
            )

        return questions