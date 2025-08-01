
async function getOllamaStatus() {
    try {
        console.log("Ollama URL:", process.env.OLLAMA_URL || "not provided");
        const res = await fetch(process.env.OLLAMA_URL || "http://localhost:11434/")
        console.log("Ollama response status:", res.status);
        if (!res.ok) {
            return false;
        }
        return res.ok
    } catch (error) {
        console.error("Error fetching Ollama status:", error);
        return false;
    }
}

async function getReaderStatus() {
    try {
        console.log("Reader API URL:", process.env.READER_API || "not provided");
        const res = await fetch(process.env.READER_API || "http://localhost:8000/")
        console.log("Reader API response status:", res.status);
        if (!res.ok) {
            return false;
        }
        return res.ok
    } catch (error) {
        console.error("Error fetching Reader API status:", error);
        return false;
    }
}

async function getMCPStatus(): Promise<boolean> {
    try {
        const key = process.env.MCP_API_KEY;

        const res = await fetch("https://dev.dashboard.shipshape.ai/sse", {
            method: "GET",
            headers: {
                "X-API-KEY": key || "",
            },
        });

        console.log("MCP Server response status:", res.status);

        const contentType = res.headers.get("content-type") || "";

        if (res.ok && contentType.includes("text/event-stream")) {
            return true;
        }

        return false;
    } catch (error) {
        console.error("Error fetching MCP Server status:", error);
        return false;
    }
}

export async function GET() {
    try {
        const ollamaStatus = await getOllamaStatus();
        const readerStatus = await getReaderStatus();
        const mcpStatus = await getMCPStatus();

        return new Response(JSON.stringify([ollamaStatus, readerStatus, mcpStatus]), {
            headers: {
                "Content-Type": "application/json",
            },
        });
    } catch (error) {
        console.error("Error in GET /api/status:", error);
        return new Response(JSON.stringify({ error: "Internal Server Error" }), {
            status: 500,
            headers: {
                "Content-Type": "application/json",
            },
        });
    }
}