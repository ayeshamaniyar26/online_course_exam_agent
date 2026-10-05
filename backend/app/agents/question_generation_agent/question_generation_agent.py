import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai

load_dotenv()

from backend.app.schemas.agent_state import AgentState


class QuestionGenerationAgent:
    """
    Generate questions using Gemini according to the teacher's
    requested question mix.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    def run(self, state: AgentState) -> Dict[str, Any]:
        requirements = state.get("requirements", {})

        subject = requirements.get("subject")
        topic = requirements.get("topic")
        difficulty = requirements.get("difficulty", "L1")

        question_mix = requirements.get("question_mix")

        # Backward compatibility with the old format.
        if not question_mix:
            count = requirements.get(
                "count",
                requirements.get("number_of_questions", 5),
            )

            question_mix = {
                "normal_mcq": count,
                "scenario_mcq": 0,
                "coding": 0,
            }

        question_mix = {
            "normal_mcq": int(question_mix.get("normal_mcq", 0)),
            "scenario_mcq": int(question_mix.get("scenario_mcq", 0)),
            "coding": int(question_mix.get("coding", 0)),
        }

        total_required = sum(question_mix.values())

        existing_questions = state.get("questions", [])

        missing_count = max(
            total_required - len(existing_questions),
            0,
        )

        if missing_count == 0:
            return {
                "current_agent": "question_generation_agent",
                "action": {
                    "type": "generation_not_required",
                    "status": "complete",
                },
                "trace_entry": {
                    "agent": "question_generation_agent",
                    "action": "generation_not_required",
                },
            }

        prompt = self._build_prompt(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            question_mix=question_mix,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        questions = self._parse_response(response.text)

        return {
            "current_agent": "question_generation_agent",
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
            "questions": existing_questions + questions,
            "trace_entry": {
                "agent": "question_generation_agent",
                "action": "generate_questions",
                "generated_count": len(questions),
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
        Build a Gemini prompt directly from teacher requirements.
        """

        topic_text = topic or "any suitable topic"

        normal_mcq_count = question_mix["normal_mcq"]
        scenario_mcq_count = question_mix["scenario_mcq"]
        coding_count = question_mix["coding"]

        coding_instruction = ""

        if coding_count > 0:
            if subject.upper() == "DBMS":
                coding_instruction = """
For coding questions:
- Create scenario-based SQL problems.
- Give the database scenario and relevant tables.
- Ask the student to write the SQL query themselves.
- Do NOT give SQL code in the question.
- Include the expected SQL answer separately for later evaluation.
- These are NOT MCQs.
"""
            elif subject.upper() == "OOPS":
                coding_instruction = """
For coding questions:
- Create scenario-based OOPS programming problems.
- Describe the required functionality clearly.
- Ask the student to write the program/code themselves.
- Do NOT provide the complete solution in the question.
- Include an expected solution separately for later evaluation.
- These are NOT MCQs.
"""
            else:
                coding_instruction = """
For coding questions:
- Create a scenario-based programming problem.
- Ask the student to write the solution themselves.
- Do NOT provide the solution in the question.
- Include an expected solution separately for later evaluation.
- These are NOT MCQs.
"""

        prompt = f"""
You are an examination Question Generation Agent.

The teacher has selected the following requirements:

Subject: {subject}
Topic: {topic_text}
Difficulty: {difficulty}

Question distribution requested by the teacher:
- Normal MCQ: {normal_mcq_count}
- Scenario-based MCQ: {scenario_mcq_count}
- Coding/Scenario questions: {coding_count}

IMPORTANT:
Generate EXACTLY the requested number of each type.
Do not change the distribution.

Normal MCQ:
- Standard conceptual or application-based MCQ.
- Four options: A, B, C, D.
- Exactly one correct answer.

Scenario-based MCQ:
- Give a realistic scenario.
- Ask a question based on that scenario.
- Student answers by selecting A, B, C, or D.
- Four options are required.
- Exactly one correct answer.

{coding_instruction}

Return ONLY valid JSON.
Do not use Markdown.
Do not add any text outside the JSON.

Use this structure:

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

For scenario coding questions, use this structure instead:

{{
  "question": "Scenario and task given to the student",
  "question_type": "coding",
  "options": {{}},
  "correct_answer": null,
  "expected_answer": "Expected SQL/code solution",
  "explanation": "Explanation of the expected solution",
  "subject": "{subject}",
  "topic": "{topic_text}",
  "difficulty": "{difficulty}",
  "source": "gemini"
}}
"""

        return prompt

    def _parse_response(self, response_text: str) -> list[dict[str, Any]]:
        response_text = response_text.strip()

        # Gemini may wrap valid JSON inside Markdown code fences.
        if response_text.startswith("```"):
            lines = response_text.splitlines()

            # Remove opening ```json / ```
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            # Remove closing ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            response_text = "\n".join(lines).strip()

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as exc:
            print("========== GEMINI RAW RESPONSE ==========")
            print(response_text)
            print("=========================================")
            raise ValueError(
                "Gemini returned invalid JSON."
            ) from exc

        questions = data.get("questions")

        if not isinstance(questions, list):
            raise ValueError(
                "Gemini response does not contain a valid questions list."
            )

        return questions