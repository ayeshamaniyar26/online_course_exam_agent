import asyncio

from backend.app.mcp.server import server


async def main():
    print("MCP TOOL EXECUTION TEST")
    print("=======================")

    result = await server.call_tool(
        "get_exam_requirements",
        {
            "subject": "CN",
            "difficulty": "L1",
            "count": 5,
        },
    )

    print("RESULT:")
    print(result)

    print()
    print("MCP TOOL EXECUTION PASSED")


if __name__ == "__main__":
    asyncio.run(main())