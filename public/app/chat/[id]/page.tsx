import ChatPageShell from "../chat-page-shell";
import { getChatSession } from "@/lib/chat-instructions";

type ChatByIdPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function ChatByIdPage({ params }: ChatByIdPageProps) {
  const { id } = await params;
  const session = await getChatSession(id);

  return (
    <ChatPageShell
      chatId={id}
      defaultInstructions={session.instructions ?? null}
      tasks={session.tasks ?? []}
      tip={session.tip ?? ""}
    />
  );
}
