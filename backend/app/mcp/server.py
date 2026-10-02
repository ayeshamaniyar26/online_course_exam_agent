from mcp.server import MCPServer

from backend.app.mcp.tools.exam_tools import (
    get_question_bank,
    validate_question,
    save_question,
    get_exam_requirements,
    get_subject_topics,
)


server = MCPServer(
    name="online-course-examination-system"
)


# ============================================================
# REGISTER MCP TOOLS
# ============================================================

server.add_tool(
    get_question_bank,
    name="get_question_bank",
    description="Retrieve questions from the examination question bank.",
)

server.add_tool(
    validate_question,
    name="validate_question",
    description="Validate the structure and correctness of an examination question.",
)

server.add_tool(
    save_question,
    name="save_question",
    description="Validate and save an examination question.",
)

server.add_tool(
    get_exam_requirements,
    name="get_exam_requirements",
    description="Get normalized examination requirements.",
)

server.add_tool(
    get_subject_topics,
    name="get_subject_topics",
    description="Get available topics for a subject.",
)
if __name__ == "__main__":
    import asyncio

    asyncio.run(
        server.run_stdio_async()
    )