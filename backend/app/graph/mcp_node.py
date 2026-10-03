import asyncio
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _call_mcp_tool(
    subject: str,
    topic: str | None,
    difficulty: str,
    count: int,
):
    server_params = StdioServerParameters(
        command="python",
        args=[
            "-m",
            "backend.app.mcp.server",
        ],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            result = await session.call_tool(
                "get_question_bank",
                arguments={
                    "subject": subject,
                    "topic": topic,
                    "difficulty": difficulty,
                    "count": count,
                },
            )

            return result


def mcp_node(state) -> dict[str, Any]:
    """
    LangGraph node that retrieves examination questions
    through the MCP question-bank tool.
    """

    requirements = state.get("requirements", {})

    retrieval_request = state.get("action", {}).get(
        "retrieval_request",
        {},
    )

    subject = retrieval_request.get(
        "subject",
        requirements.get("subject"),
    )

    topic = retrieval_request.get(
        "topic",
        requirements.get("topic"),
    )

    difficulty = retrieval_request.get(
        "difficulty",
        requirements.get("difficulty", "L1"),
    )

    count = retrieval_request.get(
        "count",
        requirements.get(
            "count",
            requirements.get("number_of_questions", 5),
        ),
    )

    if not subject:
        return {
            "questions": [],
            "observation": {
                **state.get("observation", {}),
                "mcp": {
                    "available": False,
                    "tool": "get_question_bank",
                    "error": "Subject is required.",
                },
            },
            "errors": list(state.get("errors", []))
            + ["Subject is required for question retrieval."],
        }

    result = asyncio.run(
        _call_mcp_tool(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            count=count,
        )
    )

    structured_content = getattr(
        result,
        "structured_content",
        None,
    )

    if not structured_content:
        return {
            "questions": [],
            "observation": {
                **state.get("observation", {}),
                "mcp": {
                    "available": False,
                    "tool": "get_question_bank",
                    "error": "MCP returned no structured question data.",
                },
            },
            "errors": list(state.get("errors", []))
            + ["MCP returned no structured question data."],
        }

    questions = structured_content.get("questions", [])

    # Normalize retrieved question-bank questions.
    # Question-bank entries are MCQs by default.
    for question in questions:
        question.setdefault("question_type", "normal_mcq")

    trace = state.get("trace", [])

    return {
        "questions": questions,
        "observation": {
            **state.get("observation", {}),
            "mcp": {
                "available": True,
                "tool": "get_question_bank",
                "count": len(questions),
                "source": structured_content.get(
                    "source",
                    "question_bank",
                ),
            },
        },
        "trace": trace
        + [
            {
                "agent": "mcp_runtime",
                "action": "get_question_bank",
                "status": "success",
                "question_count": len(questions),
            }
        ],
    }