import {
    AttachmentAdapter,
    PendingAttachment,
    CompleteAttachment,
} from "@assistant-ui/react";

class FileAttachmentAdapter implements AttachmentAdapter {
    accept = "*/*"    

    async add({ file }: { file: File }): Promise<PendingAttachment> {
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

    async send(attachment: PendingAttachment): Promise<CompleteAttachment> {
        const res = await fetch("/api/read", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                attachment: attachment,
            }),
        })

        return res.json().then((data: CompleteAttachment) => {
            if (!data || !data.content) {
                throw new Error("Failed to process attachment");
            }

            return {
                ...attachment,
                status: { type: "complete" },
                content: data.content,
            };
        });

    }

    async remove(attachment: PendingAttachment): Promise<void> {
        // Cleanup if needed
    }
}

export { FileAttachmentAdapter };