import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _call_mcp_tool(
    subject: str,
    difficulty: str,
    question_count: int,
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
                "validate_exam_requirement",
                arguments={
                    "subject": subject,
                    "difficulty": difficulty,
                    "question_count": question_count,
                },
            )

            return result


def mcp_node(state) -> dict:
    """
    LangGraph node that invokes an MCP tool.
    """

    requirements = state.get("requirements", {})

    subject = requirements.get(
        "subject",
        "Computer Networks",
    )

    difficulty = requirements.get(
        "difficulty",
        "L1",
    )

    question_count = requirements.get(
        "question_count",
        5,
    )

    result = asyncio.run(
        _call_mcp_tool(
            subject=subject,
            difficulty=difficulty,
            question_count=question_count,
        )
    )

    trace = state.get("trace", [])

    return {
        "observation": {
            **state.get("observation", {}),
            "mcp": {
                "available": True,
                "tool": "validate_exam_requirement",
                "result": str(result),
            },
        },
        "trace": trace
        + [
            {
                "agent": "mcp_runtime",
                "action": "validate_exam_requirement",
                "status": "success",
            }
        ],
    }