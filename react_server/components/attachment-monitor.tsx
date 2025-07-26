import React, { createContext, useContext, useState, ReactNode } from "react";

export type Attachment = {
  id: string;
  name: string;
  status: string; 
  response?: string;
};

type AttachmentContextType = {
  attachments: Attachment[];
  addAttachment: (attachment: Attachment) => void;
  updateAttachment: (id: string, updatedAttachment: Partial<Attachment>) => void;
  clearAttachments: () => void;
  removeAttachment: (id: string) => void;
};

const AttachmentContext = createContext<AttachmentContextType | undefined>(undefined);

export const AttachmentProvider = ({ children }: { children: ReactNode }) => {
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  const addAttachment = (attachment: Attachment) => {
    setAttachments((prev) => [...prev, attachment]);
  };

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((attachment) => attachment.id !== id));
  };

  const updateAttachment = (id: string, updatedAttachment: Partial<Attachment>) => {
    setAttachments((prev) =>
      prev.map((attachment) =>
        attachment.id === id ? { ...attachment, ...updatedAttachment } : attachment
      )
    );
  }

  const clearAttachments = () => {
    setAttachments([]);
  };

  return (
    <AttachmentContext.Provider value={{ attachments, addAttachment, updateAttachment, clearAttachments, removeAttachment }}>
      {children}
    </AttachmentContext.Provider>
  );
};

export const useAttachmentContext = () => {
  const context = useContext(AttachmentContext);
  if (!context) {
    throw new Error("useAttachmentContext must be used within an AttachmentProvider");
  }
  return context;
};

export default function AttachmentMonitor() {
  const { attachments } = useAttachmentContext();

  return (
    <ul className="m-2">
      {attachments.slice().reverse().slice(0, 4).map((attachment) => (
        <li key={attachment.id} className="flex items-center gap-2 p-2 border-b">
          <span className="m-1 text-sm font-semibold">{attachment.name}</span>
          <span className="text-xs text-gray-500">{attachment.status}</span>
          {attachment.response && (
            <span className="text-xs text-gray-700">{attachment.response}</span>
          )}
        </li>
      ))}
    </ul>
  );
}