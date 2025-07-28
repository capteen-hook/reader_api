"use client";

import {
  AssistantRuntimeProvider,
  // CompositeAttachmentAdapter,
  // SimpleImageAttachmentAdapter,
  // SimpleTextAttachmentAdapter
} from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { Thread } from "@/components/assistant-ui/thread";
// import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
// import { AppSidebar } from "@/components/app-sidebar";
// import { Separator } from "@/components/ui/separator";
// import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";

import { useAttachmentContext } from "@/components/attachment-monitor";
import { FileAttachmentAdapter } from "./adapter";
import AttachmentMonitor from "@/components/attachment-monitor";

export const runtime = "nodejs";

export const Assistant = () => {

  const attachmentContext = useAttachmentContext();
  const runtime = useChatRuntime({
    api: "/api/chat",
    adapters: {
      attachments: new FileAttachmentAdapter(attachmentContext),
    },
    unstable_humanToolNames: [],
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {/* <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
            <SidebarTrigger />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem className="hidden md:block">
                  <BreadcrumbLink href="#">
                    Build Your Own ChatGPT UX
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator className="hidden md:block" />
                <BreadcrumbItem>
                  <BreadcrumbPage>
                    Starter Template
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </header>
        </SidebarInset>
      </SidebarProvider> */}
      <Thread />
      <AttachmentMonitor />
    </AssistantRuntimeProvider>
  );
};
