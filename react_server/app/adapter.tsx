import { SpecialFile, SpecialPendingAttachment, SpecialCompleteAttachment } from "@/components/special_file";
import {
    AttachmentAdapter
} from "@assistant-ui/react";

import { useAttachmentContext } from "@/components/attachment-monitor";
import type { Attachment } from "@/components/attachment-monitor";

class FileAttachmentAdapter implements AttachmentAdapter {
    accept = "*/*"    

    constructor(private attachmentContext: ReturnType<typeof useAttachmentContext>) {}

    async add({ file }: { file: SpecialFile }): Promise<SpecialPendingAttachment> {
        // Validate file size
        const maxSize = 10 * 1024 * 1024; // 10MB limit
        if (file.size > maxSize) {
            throw new Error("File size exceeds 10MB limit");
        }
        
        return {
            id: crypto.randomUUID(),
            type: "document",
            contentType: file.type,
            name: file.name,
            file,
            status: { type: "running", reason: "uploading", progress: 0 },
        };
    }

    async send(attachment: SpecialPendingAttachment): Promise<SpecialCompleteAttachment> {
        const { addAttachment, updateAttachment } = this.attachmentContext;

        // Update context to show progress
        const attachmentMoniter: Attachment = {
            id: attachment.id,
            name: attachment.name,
            status: 'running'
        };
        addAttachment(attachmentMoniter);

        const formData = new FormData();
        formData.append("file", attachment.file);
        formData.append("id", attachment.id);
        formData.append("name", attachment.name);
    
        let res: Response;
        console.log(`Sending attachment: ${attachment.id}, processType: ${attachment.file.processType}`);
        try {
            if (attachment.file.processType === "file") {
                res = await fetch("/api/file", {
                    method: "POST",
                    body: formData, 
                });
            } else if (attachment.file.processType === "report") {
                res = await fetch("/api/report", {
                    method: "POST",
                    body: formData,
                });
            } else if (attachment.file.processType === "appliance") {
                res = await fetch("/api/appliance", {
                    method: "POST",
                    body: formData,
                });
            } else {
                updateAttachment(attachment.id, {
                    status: "error",
                    response: "Unsupported process type"
                });
                throw new Error("Unsupported process type");
            }
        } catch (error) {
            updateAttachment(attachment.id, {
                status: "error",
                response: error instanceof Error ? error.message : "Unknown error"
            });
            throw new Error(`Failed to send attachment: ${error}`);
        }

        if (!res) {
            updateAttachment(attachment.id, {
                status: "error",
                response: "No response from server"
            });
            throw new Error("Failed to send attachment");
        }
    
        const data = await res.json();
        if (!data || !data.content) {
            updateAttachment(attachment.id, {
                status: "error",
                response: "No content returned from server"
            });
            throw new Error("Failed to process attachment");
        }

        const completeAttachment: Attachment = {
            ...attachment,
            status: res.ok ? "complete" : "error",
            response: JSON.stringify(data.content),
        };
        updateAttachment(attachment.id, completeAttachment);

    
        return {
            ...attachment,
            status: { type: "complete" },
            content: data.content,
        };
    }

    async remove(attachment: SpecialPendingAttachment): Promise<void> {
        // Cleanup if needed
        const { removeAttachment } = this.attachmentContext;

        removeAttachment(attachment.id);
        
        console.log(`trying Removing attachment: ${attachment.id}`);
    }
}

export { FileAttachmentAdapter };