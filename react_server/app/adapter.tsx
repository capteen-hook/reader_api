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
        const formData = new FormData();
        formData.append("file", attachment.file);  // The actual file
        formData.append("id", attachment.id);      // Optional metadata
        formData.append("name", attachment.name);
    
        const res = await fetch("/api/read", {
            method: "POST",
            body: formData, // No Content-Type header! Browser sets it automatically.
        });
    
        const data = await res.json();
        if (!data || !data.content) {
            throw new Error("Failed to process attachment");
        }
    
        return {
            ...attachment,
            status: { type: "complete" },
            content: data.content,
        };
    }

    async remove(attachment: PendingAttachment): Promise<void> {
        // Cleanup if needed
        console.log(`trying Removing attachment: ${attachment.id}`);
    }
}

export { FileAttachmentAdapter };