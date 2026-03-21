"use client";

import dynamic from "next/dynamic";
import type { ChatTask } from "@/lib/chat-instructions";

type ChatPageShellProps = {
  chatId?: string | null;
  defaultInstructions: string | null;
  tasks?: ChatTask[];
  tip?: string;
};

const ChatPageClient = dynamic(() => import("./chat-page-client"), {
  ssr: false,
});

export default function ChatPageShell(props: ChatPageShellProps) {
  return <ChatPageClient {...props} />;
}
