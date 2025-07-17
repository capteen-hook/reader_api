import asyncio
import os

from dotenv import load_dotenv, find_dotenv
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

load_dotenv(find_dotenv())

# llm_temperature = float(os.getenv('LLM_TEMPERATURE'))
# ollama_model = os.getenv('OLLAMA_MODEL')
# ollama_base_url = os.getenv('OLLAMA_BASE_URL')

llm_temperature = 0.7
ollama_model = "llama3.1:latest" 
ollama_base_url = "http://localhost:11434"

ollama_chat_llm = ChatOllama(base_url=ollama_base_url, model=ollama_model, temperature=llm_temperature)

# {
#   "mcpServers": {
#     "mcp-core-server-dev": {
#       "command": "npx",
#       "args": [
#         "mcp-remote@latest",
#         "https://dev.dashboard.shipshape.ai/sse",
#         "--transport=sse-only",
#         "--header",
#         "X-API-KEY:" + os.getenv('MCP_API_KEY', 'dummy_key'),
#       ]
#     }
#   }
# }

# npx mcp-remote@latest https://dev.dashboard.shipshape.ai/sse --transport=sse-only --header X-API-KEY:dummy_key

# server_params = StdioServerParameters(
#     command="npx",
#     args=[
#         "mcp-remote@latest",
#         "https://dev.dashboard.shipshape.ai/sse",
#         "--transport=sse-only",
#         "--header",
#         "X-API-KEY:" + os.getenv('MCP_API_KEY', 'dummy_key'),
#     ]
# )

# {
#   "mcpServers": {
#     "weather": {
#       "command": "npx",
#         "args": [
#             "-y",
#             "@h1deya/mcp-server-weather"
#         ],
#     }
#   }
# }

# npx -y @h1deya/mcp-server-weather

server_params = StdioServerParameters(
    command="npx",
    args=[
        "-y",
        "@h1deya/mcp-server-weather"
    ]
)

def serialize(obj):
    """Custom serializer for non-serializable objects."""
    if hasattr(obj, "__dict__"):
        return obj.__dict__  # Convert objects to dictionaries
    elif isinstance(obj, list):
        return [serialize(item) for item in obj]  # Recursively handle lists
    elif isinstance(obj, dict):
        return {key: serialize(value) for key, value in obj.items()}  # Recursively handle dicts
    else:
        return str(obj)  # Fallback to string representation
      
async def main():
  
  async with stdio_client(server_params) as (read, write):
      async with ClientSession(read, write) as session:
          await session.initialize()
          tools = await load_mcp_tools(session) 
          # Initialize a ReACT agent
          agent = create_react_agent(ollama_chat_llm, tools)

  agent_response = await agent.ainvoke(
    {'messages': 'what tools are available to you ?'})

  print("Response:")
  # Pretty-print the JSON response
  print(json.dumps(serialize(agent_response), indent=4))

if __name__ == '__main__':
  asyncio.run(main())