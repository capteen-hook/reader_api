import { ollama } from "ollama-ai-provider";
import { frontendTools } from "@assistant-ui/react-ai-sdk";
import { streamText } from "ai";
import { Experimental_StdioMCPTransport } from 'ai/mcp-stdio';
import { experimental_createMCPClient as createMCPClient, ToolSet } from "ai";
import path from "path";

export const runtime = "nodejs";

// const transport = new Experimental_StdioMCPTransport({
//   command: "npx",
//   args: [
//     "-y",
//     "@h1deya/mcp-server-weather"
//   ]
// });

async function createMCPTools() {
  const mcpServerPath = path.resolve(
    "node_modules/.bin/mcp-server-weather" 
  );

  const transport = new Experimental_StdioMCPTransport({
    command: mcpServerPath,
  });

  const mcpClient = await createMCPClient({ transport });

  return await mcpClient.tools();
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
    model: ollama("llama3.1:latest"),
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
