"use client";
import React from "react";

function StatusIndicator({ status, name }: { status: boolean; name: string }) {
    return (
        <span
            style={{
                display: "inline-block",
                margin: "0 5px",
                width: "10px",
                height: "10px",
                backgroundColor: status ? "green" : "red",
                borderRadius: "50%",
                cursor: "pointer",
            }}
            title={`${name} is ${status ? "Online" : "Offline"}`}
        ></span>
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
                    cache: 'no-store', // Ensure fresh data
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

    return (
        <div className="m-2" style={{ display: "flex", justifyContent: "right"}}>
            <StatusIndicator status={ollamaStatus} name="Ollama" />
            <StatusIndicator status={readerStatus} name="Reader API" />
            <StatusIndicator status={mcpStatus} name="MCP Server" />
        </div>
    );
}