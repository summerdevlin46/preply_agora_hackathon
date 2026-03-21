"use client";

import dynamic from "next/dynamic";

type ChatPageShellProps = {
  chatId?: string | null;
  defaultInstructions: string | null;
};

const ChatPageClient = dynamic(() => import("./chat-page-client"), {
  ssr: false,
});

export default function ChatPageShell(props: ChatPageShellProps) {
  return <ChatPageClient {...props} />;
}
