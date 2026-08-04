import inspect
from langchain_core.tools import StructuredTool
from mcp_server import mcp

def get_mcp_tools():
    """Extract FastMCP registered tools directly into executable LangChain StructuredTools."""
    mcp_tools = []
    
    tools_dict = getattr(mcp, "_tools", {})
    if not tools_dict and hasattr(mcp, "_tool_manager"):
        tools_dict = getattr(mcp._tool_manager, "_tools", {})

    for tool_name, tool_obj in tools_dict.items():
        fn = getattr(tool_obj, "fn", tool_obj)
        description = getattr(tool_obj, "description", None) or f"MCP tool {tool_name}"
        
        is_coro = inspect.iscoroutinefunction(fn)
        structured_tool = StructuredTool.from_function(
            coroutine=fn if is_coro else None,
            func=fn if not is_coro else None,
            name=tool_name,
            description=description
        )
        mcp_tools.append(structured_tool)
    return mcp_tools

async def build_agent():
    """Returns pure FastMCP tools for direct execution without an external LLM dependency."""
    mcp_tools = get_mcp_tools()
    print("⚡ Direct MCP Execution Engine Ready")
    return None, mcp_tools