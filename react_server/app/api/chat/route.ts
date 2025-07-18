import { ollama } from "ollama-ai-provider";
import { frontendTools } from "@assistant-ui/react-ai-sdk";
import { streamText } from "ai";
import { Experimental_StdioMCPTransport } from 'ai/mcp-stdio';
import { experimental_createMCPClient as createMCPClient, ToolSet } from "ai";
import path from "path";

export const runtime = "nodejs";

async function weatherTool() {
  const mcpServerPath = path.resolve(
    "node_modules/.bin/mcp-server-weather" 
  );

  const transport = new Experimental_StdioMCPTransport({
    command: mcpServerPath,
  });

  const mcpClient = await createMCPClient({ transport });

  return await mcpClient.tools();
}

// async function searchTool() {
//   const mcpServerPath = path.resolve(
//     "node_modules/.bin/tavily-mcp"
//   );

//   const transport = new Experimental_StdioMCPTransport({
//     command: mcpServerPath,
//   });

//   const mcpClient = await createMCPClient({ transport });

//   return await mcpClient.tools();
// }

// async function shipshapeTool() {
//   // npx mcp-remote@latest https://dev.dashboard.shipshape.ai/sse --transport=sse-only --header X-API-KEY:dummy_key

//   const mcpServerPath = path.resolve(
//     "node_modules/.bin/mcp-remote"
//   );

//   const transport = new Experimental_StdioMCPTransport({
//     command: mcpServerPath,
//     args: [
//       "https://dev.dashboard.shipshape.ai/sse",
//       "--transport=sse-only",
//       "--header=X-API-KEY:" + process.env.MCP_API_KEY,
//     ],
//   });
//   const mcpClient = await createMCPClient({ transport });
//   return await mcpClient.tools();
// }

async function createMCPTools(): Promise<ToolSet> {
  const weather = await weatherTool();
  // const search = await searchTool();
  // const shipshape = await shipshapeTool();

  return weather

  // const mcpTools: ToolSet = {
  //   ...weather,
  //   ...search,
  // };

  // return mcpTools
}

let mcpTools: null | ToolSet = null;

async function getMcpTools() {
  if (!mcpTools) {
    mcpTools = await createMCPTools();
  }
  return mcpTools;
}

export async function POST(req: Request) {
  const { messages, system, tools } = await req.json();

  const this_mcpTools = await getMcpTools();

  const result = streamText({
    model: ollama(process.env.MODEL_NAME || "qwen3:8b"),
    messages,
    // forward system prompt and tools from the frontend
    toolCallStreaming: true,
    system,
    tools: {
      ...frontendTools(tools),
      ...this_mcpTools,
    },
    onError: console.log,
  });

  return result.toDataStreamResponse();
}
