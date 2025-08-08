from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Connect via stdio to a local script
    server_params = StdioServerParameters(command="python", args=["server.py"])
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            result = await session.call_tool("scientific_calculator", {"expression": "2 + 3 * 4"})
            print(f"Calculator result: {result.content[0].text}")
            
            result = await session.call_tool("web_search", {"query": "What is the capital of France?"})
            print(f"Search result: {result.content[0].text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())