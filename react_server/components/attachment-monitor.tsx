// import { useAssistantRuntime } from "@assistant-ui/react";
// import { useThreadRuntime } from "@assistant-ui/react";
// import { useComposerRuntime } from "@assistant-ui/react";
import { useAttachment } from "@assistant-ui/react";

import type { Attachment } from "@assistant-ui/react";

import { useEffect, useState } from "react";

export default function AttachmentMonitor() {
    
    const [inProgressAttachments, setInProgressAttachments] = useState<Attachment[]>([]);

    // const assistantRuntime = useAssistantRuntime();
    // const canRemove = useAttachment((a) => a.source !== "message");
    const attachment = useAttachment();

    console.log("do we have attachments?", attachment);
    
    useEffect(() => {
        console.log("Attachments changed:", attachment);
    }, [attachment]);

    return (
        <ul className="attachment-monitor">
            {inProgressAttachments.map((attachment) => (
                <li key={attachment.id} className="attachment-item">
                    <div className="attachment-info">
                        <span className="attachment-name">{attachment.name}</span>
                        <span className="attachment-status">
                            {attachment.status.type}
                        </span>
                    </div>
                </li>                
            ))}
        </ul>
    );
}