import ChatPageShell from "../chat-page-shell";
import { getChatInstructions } from "@/lib/chat-instructions";

type ChatByIdPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function ChatByIdPage({ params }: ChatByIdPageProps) {
  const { id } = await params;
  const defaultInstructions = await getChatInstructions(id);

  return <ChatPageShell chatId={id} defaultInstructions={defaultInstructions} />;
}
