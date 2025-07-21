import { createOllama, OllamaProviderSettings } from "ollama-ai-provider";
import { frontendTools } from "@assistant-ui/react-ai-sdk";
import { streamText } from "ai";
import { Experimental_StdioMCPTransport } from 'ai/mcp-stdio';
import { experimental_createMCPClient as createMCPClient, ToolSet } from "ai";
import path from "path";

export const runtime = "nodejs";


export async function POST(req: Request) {
  const { attachment } = await req.json();
  if (!attachment || !attachment.file) {
    return new Response("Invalid attachment", { status: 400 });
  }
  // curl -i -X POST -H "Authorization: Bearer key" -F "file=@report.pdf" -F "schema=@schema.json" "https://shipshape.companionintelligence.org/reader_api/process/home"
  // This will return a task ID that can be used to retrieve the results like so,
  // task id goes into the path.
  // curl -i -X GET -H "Authorization: Bearer key" "https://shipshape.companionintelligence.org/reader_api/tasks/18ab2458-47cd-4c4d-8dfc-ce8265e84f9a"'
  // {  
  //     "properties": {
  //         "address": {                                                                                                    
  //             "type": "string"
  //         },
  //         "square_footage": {
  //             "type": "integer"                                                                                           
  //         },
  //         "year_built": {                                                                                                 
  //             "type": "integer"                                                                                           
  //         }                                                                            
  //     },
  //     "required": ["address", "type"],                                                                                    
  //     "title": "Home",
  //     "type": "object"                                                                                                    
  // }
  const key = process.env.READER_API_KEY;
  if (!key) {
    throw new Error("READER_API_KEY environment variable is not set");
  }
  const formData = new FormData();
  formData.append("file", attachment.file);
  // use a basic schema for now, this can be extended later
  const schema = {
    properties: {
      success: {
        type: "boolean",
      },
      summary: {
        type: "string",
      },
      content: {
        type: "string",
      },
    },
    required: ["success", "summary", "content"],
    title: "File Analysis Result",
    type: "object",
  };
  formData.append("schema", new Blob([JSON.stringify(schema)], { type: "application/json" }));
  const response = await fetch("https://shipshape.companionintelligence.org/reader_api/process/file", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
    },
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Failed to queue File processing: ${response.status} ${response.statusText}`);
  }
  const res = await response.json()
  console.log("File processing response:", res);
  const taskId = res.task_id;

  while (true) {
    const taskResponse = await fetch(`https://shipshape.companionintelligence.org/reader_api/tasks/${taskId}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${key}`,
      },
    });
    if (!taskResponse.ok) {
      throw new Error(`Failed to retrieve task status: ${taskResponse.status} ${taskResponse.statusText}`);
    }
    const result = await taskResponse.json();
    console.log("Task status:", result);

    // Wait before polling again
    await new Promise(resolve => setTimeout(resolve, 2000));

    if (result.status === "completed") {


      return {
        id: attachment.id,
        type: "document",
        contentType: attachment.contentType,
        name: attachment.name,
        file: attachment.file,
        status: { type: "complete" },
        content: [
          {
            type: "text",
            text: result.summary || "No summary available",
          },
          {
            type: "text",
            text: result.content || "No content available",
          },
        ],
      };

    } else if (result.status === "failed") {
      throw new Error(`File processing failed: ${result.error || "Unknown error"}`);
    }
  }
}
