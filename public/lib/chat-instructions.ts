const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export const DEFAULT_CHAT_INSTRUCTIONS = `You are the live speaking tutor for the Mirror demo.
Keep answers concise, spoken, and natural.
Guide the learner through English practice with specific feedback and clear next steps.
Avoid markdown, bullet points, or long monologues unless explicitly requested.`;

type ChatInstructionsResponse = {
  instructions?: string | null;
};

export type ChatTask = {
  title: string;
  description: string;
};

export type ChatSessionResponse = {
  instructions?: string | null;
  tasks?: ChatTask[];
  tip?: string;
};

export type StudentAnalysis = {
  confidence_score: number;
  fluency_score: number;
  raw_turns: Record<string, unknown>[];
};

export type TeacherReportResponse = {
  chat_id: string;
  transcript: string;
  homework_analysis: string;
  student_analysis: StudentAnalysis;
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

export async function getChatSession(chatId: string) {
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/api/chat/${encodeURIComponent(chatId)}/session`,
      {
        cache: "no-store",
      },
    );

    if (!response.ok) {
      return { instructions: null, tasks: [], tip: "" } satisfies Required<ChatSessionResponse>;
    }

    const data = (await response.json()) as ChatSessionResponse;
    return {
      instructions:
        data.instructions === null
          ? null
          : data.instructions?.trim() || DEFAULT_CHAT_INSTRUCTIONS,
      tasks: Array.isArray(data.tasks) ? data.tasks : [],
      tip: data.tip?.trim() || "",
    };
  } catch {
    return { instructions: null, tasks: [], tip: "" } satisfies Required<ChatSessionResponse>;
  }
}

export async function getTeacherReport(chatId: string) {
  const response = await fetch(
    `${getApiBaseUrl()}/api/chat/get-report?chat_id=${encodeURIComponent(chatId)}`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    let message = "Unable to load report.";
    try {
      const data = await response.json();
      if (typeof data?.detail === "string" && data.detail.trim()) {
        message = data.detail.trim();
      }
    } catch {}
    throw new Error(message);
  }

  const data = (await response.json()) as TeacherReportResponse;

  return {
    chat_id: data.chat_id,
    transcript: data.transcript?.trim() || "",
    homework_analysis: data.homework_analysis?.trim() || "",
    student_analysis: {
      confidence_score: Number(data.student_analysis?.confidence_score ?? 0),
      fluency_score: Number(data.student_analysis?.fluency_score ?? 0),
      raw_turns: Array.isArray(data.student_analysis?.raw_turns)
        ? data.student_analysis.raw_turns
        : [],
    },
  } satisfies TeacherReportResponse;
}
