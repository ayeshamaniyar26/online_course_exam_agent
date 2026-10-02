import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=[
            "-m",
            "backend.app.mcp.server",
        ],
    )

    print("MCP CLIENT TEST")
    print("================")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            tools = await session.list_tools()

            print("MCP CONNECTION PASSED")
            print("AVAILABLE TOOLS:")

            for tool in tools.tools:
                print("-", tool.name)

            result = await session.call_tool(
                "validate_exam_requirement",
                arguments={
                    "subject": "Computer Networks",
                    "difficulty": "L1",
                    "question_count": 5,
                },
            )

            print()
            print("TOOL EXECUTION RESULT:")
            print(result)

            print()
            print("MCP TOOL EXECUTION PASSED")


if __name__ == "__main__":
    asyncio.run(main())