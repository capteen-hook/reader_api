"use server";

async function getOllamaStatus() {
    const res = await fetch(process.env.OLLAMA_URL || "http://localhost:11434/")
    if (!res.ok) {
        return false;
    }
    return res.ok
}

async function getReaderStatus() {
    const res = await fetch(process.env.READER_API || "http://localhost:8080/")
    if (!res.ok) {
        return false;
    }
    return res.ok
}

async function getMCPStatus() {
    const res = await fetch("https://dev.dashboard.shipshape.ai/sse")
    if (!res.ok) {
        return false;
    }
    return res.ok
}

function StatusIndicator(status: boolean, name: string) {
    return (
        <div style={{ color: status ? "green" : "red" }}>
            {name} is {status ? "Online" : "Offline"}
        </div>
    );
}

export default async function StatusMonitor() {
    
    const ollamaStatus = await getOllamaStatus();
    const readerStatus = await getReaderStatus();
    const mcpStatus = await getMCPStatus();

    return (
        <div className="status-monitor">
            <h2>Status Monitor</h2>
            {StatusIndicator(ollamaStatus, "Ollama")}
            {StatusIndicator(readerStatus, "Reader API")}
            {StatusIndicator(mcpStatus, "MCP Server")}
        </div>
    );
}