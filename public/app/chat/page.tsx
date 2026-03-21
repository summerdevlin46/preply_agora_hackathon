import ChatPageShell from "./chat-page-shell";
import { getDefaultChatInstructions } from "@/lib/chat-instructions";

export default async function ChatPage() {
  const defaultInstructions = await getDefaultChatInstructions();

  return <ChatPageShell defaultInstructions={defaultInstructions} />;
}
