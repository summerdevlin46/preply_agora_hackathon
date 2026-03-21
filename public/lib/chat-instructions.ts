const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export const DEFAULT_CHAT_INSTRUCTIONS = `You are the live speaking tutor for the Mirror demo.
Keep answers concise, spoken, and natural.
Guide the learner through English practice with specific feedback and clear next steps.
Avoid markdown, bullet points, or long monologues unless explicitly requested.`;

type ChatInstructionsResponse = {
  instructions?: string | null;
};

function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;
}

export async function getDefaultChatInstructions() {
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/api/chat/get-user-chat-instructions`,
      {
        cache: "no-store",
      },
    );

    if (!response.ok) {
      return DEFAULT_CHAT_INSTRUCTIONS;
    }

    const data = (await response.json()) as ChatInstructionsResponse;
    if (data.instructions === null) {
      return null;
    }

    return data.instructions?.trim() || DEFAULT_CHAT_INSTRUCTIONS;
  } catch {
    return DEFAULT_CHAT_INSTRUCTIONS;
  }
}

export async function getChatInstructions(chatId: string) {
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/api/chat/${encodeURIComponent(chatId)}/instructions`,
      {
        cache: "no-store",
      },
    );

    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as ChatInstructionsResponse;
    if (data.instructions === null) {
      return null;
    }

    return data.instructions?.trim() || DEFAULT_CHAT_INSTRUCTIONS;
  } catch {
    return null;
  }
}
