import { ollama } from "ollama-ai-provider";
import { frontendTools } from "@assistant-ui/react-ai-sdk";
import { streamText } from "ai";
import { Experimental_StdioMCPTransport } from 'ai/mcp-stdio';
import { experimental_createMCPClient as createMCPClient } from "ai";

export const runtime = "nodejs";

const transport = new Experimental_StdioMCPTransport({
  command: "npx",
  args: [
    "-y",
    "@h1deya/mcp-server-weather"
  ]
});

const mcpClient = await createMCPClient({
  transport,
});

const mcpTools = await mcpClient.tools();

export async function POST(req: Request) {
  const { messages, system, tools } = await req.json();

  const result = streamText({
    model: ollama("llama3.1:latest"),
    messages,
    // forward system prompt and tools from the frontend
    toolCallStreaming: true,
    system,
    tools: {
      ...frontendTools(tools),
      ...mcpTools,
    },
    onError: console.log,
  });

  return result.toDataStreamResponse();
}
