import { createOllama, OllamaProviderSettings } from "ollama-ai-provider";
import { frontendTools } from "@assistant-ui/react-ai-sdk";
import { streamText } from "ai";
import { Experimental_StdioMCPTransport } from 'ai/mcp-stdio';
import { experimental_createMCPClient as createMCPClient, ToolSet } from "ai";
import path from "path";

export const runtime = "nodejs";

const ollamaSettings: OllamaProviderSettings = {
  baseURL: (process.env.OLLAMA_URL || "http://localhost:11434/") + "api",
}

const ollama = createOllama(ollamaSettings);

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

async function searchTool() {
  const mcpServerPath = path.resolve(
    "node_modules/.bin/tavily-mcp"
  );

  const transport = new Experimental_StdioMCPTransport({
    command: mcpServerPath,
    env: {
      TAVILY_API_KEY: process.env.TAVILY_API_KEY || "dummy_key",
    },
  });

  const mcpClient = await createMCPClient({ transport });

  return await mcpClient.tools();
}

async function shipshapeTool() {
  // npx mcp-remote@latest https://dev.dashboard.shipshape.ai/sse --transport=sse-only --header X-API-KEY:dummy_key

  const mcpServerPath = path.resolve(
    "node_modules/.bin/mcp-remote"
  );

  const transport = new Experimental_StdioMCPTransport({
    command: mcpServerPath,
    args: [
      "https://dev.dashboard.shipshape.ai/sse",
      "--transport=sse-only",
      "--header",
      "X-API-KEY:" + process.env.MCP_API_KEY,
    ],
  });
  const mcpClient = await createMCPClient({ transport });
  return await mcpClient.tools();
}

async function createMCPTools(): Promise<ToolSet> {


  const weather = await weatherTool();
  const search = await searchTool();

  try {
    const shipshape = await shipshapeTool();

    const mcpTools: ToolSet = {
      ...weather,
      ...search,
      ...shipshape,
    };

    return mcpTools;
  } catch (error) {
    console.error("ShipShape tool failed to load:", error)

    const mcpTools: ToolSet = {
      ...weather,
      ...search,
    };

    return mcpTools;
  }
}

let mcpTools: null | ToolSet = null;

async function getMcpTools() {
  if (!mcpTools) {
    mcpTools = await createMCPTools();
  }
  return mcpTools;
}

export async function POST(req: Request) {
  try {
    const res = await req.json();
    console.log("Received req:", res);
    const { messages, system, tools } = res
    console.log("Received request with messages:", messages);
    console.log("System prompt:", system);
    console.log("Tools:", tools);
    if (!tools) {
      const result = streamText({
        model: ollama(process.env.MODEL_NAME || "qwen3:8b"),
        messages,
        // forward system prompt from the frontend
        system,
        toolCallStreaming: false,
        onError: console.log,
      });

      return result.toDataStreamResponse();

    } else {
      const this_mcpTools = await getMcpTools();

      // console.log("Received messages:");
      // for (const message of messages) {
      //   console.log(`- ${message.role}: ${Object.keys(message.content)}`);
      // }

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
  } catch (error) {
    console.error("Error in POST /chat:", error);
    return new Response(`Error processing file: ${error}`, { status: 500 });
  }
}
