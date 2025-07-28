'use client';
import { Assistant } from "./assistant";

import { AttachmentProvider } from "@/components/attachment-monitor";

export default function Home() {
  return (
    <AttachmentProvider>
      <Assistant />
    </AttachmentProvider>
  );
}
