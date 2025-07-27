// import { useAssistantRuntime } from "@assistant-ui/react";
// // import { useThreadRuntime } from "@assistant-ui/react";
// // import { useComposerRuntime } from "@assistant-ui/react";

// import type { Attachment } from "@assistant-ui/react";

// import { useEffect, useState } from "react";

// export default function AttachmentMonitor() {
    
//     const [inProgressAttachments, setInProgressAttachments] = useState<Attachment[]>([]);

//     const assistantRuntime = useAssistantRuntime();

//     console.log("do we have attachments?", assistantRuntime.thread.getState());
    
//     useEffect(() => {
//         setInProgressAttachments([...assistantRuntime.thread.composer.getState().attachments]);
//         console.log("Updated inProgressAttachments:", assistantRuntime.thread.composer.getState().attachments);
//     }, [assistantRuntime.thread.composer.getState().attachments]);


//     return (
//         <ul className="attachment-monitor">
//             {inProgressAttachments.map((attachment) => (
//                 <li key={attachment.id} className="attachment-item">
//                     <div className="attachment-info">
//                         <span className="attachment-name">{attachment.name}</span>
//                         <span className="attachment-status">
//                             {attachment.status.type}
//                         </span>
//                     </div>
//                 </li>                
//             ))}
//         </ul>
//     );
// }