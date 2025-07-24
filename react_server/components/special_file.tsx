import type {
    CompleteAttachment,
    PendingAttachment,
} from "@assistant-ui/react";

export interface SpecialFile extends File {
    processType: "file" | "report" | "appliance";
}

export function makeSpecial(file: File, processType: "file" | "report" | "appliance"): SpecialFile {
    return Object.assign(file, { processType }) as SpecialFile;
}
export type SpecialPendingAttachment = PendingAttachment & {
    file: SpecialFile;
}

export type SpecialCompleteAttachment = CompleteAttachment & {
    file: SpecialFile;
}