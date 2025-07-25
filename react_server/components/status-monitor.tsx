"use client";
import React from "react";

function StatusIndicator(status: boolean, name: string) {
    return (
        <div style={{ color: status ? "green" : "red" }}>
            {name} is {status ? "Online" : "Offline"}
        </div>
    );
}

export default function StatusMonitor() {

    const [ollamaStatus, setOllamaStatus] = React.useState<boolean>(false);
    const [readerStatus, setReaderStatus] = React.useState<boolean>(false);
    const [mcpStatus, setMcpStatus] = React.useState<boolean>(false);

    React.useEffect(() => {
        async function fetchStatus() {
            try {
                const res = await fetch('/api/status', {
                    method: 'GET',
                    cache: 'no-store' // Ensure fresh data
                });

                if (!res.ok) {
                    throw new Error('Failed to fetch status');
                }

                const [ollama, reader, mcp] = await res.json();
                setOllamaStatus(ollama);
                setReaderStatus(reader);
                setMcpStatus(mcp);
            } catch (error) {
                console.error("Error fetching status:", error);
            }
        }

        fetchStatus();
    }, []);

    console.log("Ollama Status:", ollamaStatus);
    console.log("Reader API Status:", readerStatus);
    console.log("MCP Server Status:", mcpStatus);

    return (
        <div className="status-monitor">
            <h2>Status Monitor</h2>
            {StatusIndicator(ollamaStatus, "Ollama")}
            {StatusIndicator(readerStatus, "Reader API")}
            {StatusIndicator(mcpStatus, "MCP Server")}
        </div>
    );
}