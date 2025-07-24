import { SpecialFile, SpecialPendingAttachment, SpecialCompleteAttachment } from "@/components/special_file";
import {
    AttachmentAdapter
} from "@assistant-ui/react";

class FileAttachmentAdapter implements AttachmentAdapter {
    accept = "*/*"    

    async add({ file }: { file: SpecialFile }): Promise<SpecialPendingAttachment> {
        // Validate file size
        const maxSize = 10 * 1024 * 1024; // 10MB limit
        if (file.size > maxSize) {
            throw new Error("File size exceeds 10MB limit");
        }

        console.log(`Adding attachment: ${file.name}, size: ${file.size} bytes`);
        
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
        const formData = new FormData();
        formData.append("file", attachment.file);
        formData.append("id", attachment.id);
        formData.append("name", attachment.name);
    
        let res: Response;
            
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
            throw new Error("Unsupported process type");
        }

        if (!res) {
            throw new Error("Failed to send attachment");
        }
    
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

    async remove(attachment: SpecialPendingAttachment): Promise<void> {
        // Cleanup if needed
        console.log(`trying Removing attachment: ${attachment.id}`);
    }
}

export { FileAttachmentAdapter };