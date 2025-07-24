export const runtime = "nodejs";


export async function POST(req: Request) {
  const formData = await req.formData();
  const file = formData.get("file") as File;

  if (!file) {
    return new Response("No file part in request", { status: 400 });
  }
  // curl -i -X POST -H "Authorization: Bearer key" -F "file=@report.pdf" -F "schema=@schema.json" "https://shipshape.companionintelligence.org/reader_api/process/home"
  // This will return a task ID that can be used to retrieve the results like so,
  // task id goes into the path.
  // curl -i -X GET -H "Authorization: Bearer key" "https://shipshape.companionintelligence.org/reader_api/tasks/18ab2458-47cd-4c4d-8dfc-ce8265e84f9a"'
  // {
  //     "$defs": {
  //         "Status": {
  //             "enum": [
  //                 "success",
  //                 "failure"
  //             ],
  //             "title": "Status",
  //             "type": "string"
  //         }
  //     },
  //     "properties": {
  //         "status": {
  //             "$ref": "#/$defs/Status"
  //         },
  //         "response": {
  //             "type": "string"
  //         }
  //     },
  //     "required": [
  //         "status",
  //         "response"
  //     ],
  //     "title": "Structured Response",
  //     "type": "object"
  // }
  const key = process.env.READER_API_KEY;
  if (!key) {
    throw new Error("READER_API_KEY environment variable is not set");
  }
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

  const uploadData = new FormData();
  uploadData.append("file", file);
  uploadData.append("schema", new Blob([JSON.stringify(schema)], { type: "application/json" }));

  console.log("Uploading to", process.env.READER_API + "/process/home");

  const response = await fetch(process.env.READER_API + "/process/home", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}` },
    body: uploadData,
  });

  if (!response.ok) {
    throw new Error(`Failed to queue File processing: ${response.status} ${response.statusText}`);
  }

  const res = await response.json();
  console.log("File processing response:", res);
  const taskId = res.task_id;

  // Polling loop
  while (true) {
    console.log("Polling", process.env.READER_API + '/tasks/' + taskId);
    const taskResponse = await fetch(process.env.READER_API + '/tasks/' + taskId, {
      method: "GET",
      headers: { Authorization: `Bearer ${key}` },
    });
    if (!taskResponse.ok) {
      throw new Error(`Failed to retrieve task status: ${taskResponse.status} ${taskResponse.statusText}`);
    }
    const result = await taskResponse.json();
    console.log("Task status:", result);

    if (result.state === "SUCCESS") {
      return new Response(JSON.stringify({
        id: file.name,
        type: "document",
        contentType: file.type,
        name: file.name,
        status: { type: "complete" },
        content: [
          { type: "text", text: JSON.stringify(result, null, 2) },
        ],
      }), { status: 200 });
    } else if (result.state === "FAILURE") {
      throw new Error(`File processing failed: ${result.error || "Unknown error"}`);
    }

    // Wait before polling again
    await new Promise(resolve => setTimeout(resolve, 4000));
  }
}