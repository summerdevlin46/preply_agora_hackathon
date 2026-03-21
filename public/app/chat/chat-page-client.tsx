"use client";

import { SyntheticEvent, useEffect, useRef, useState } from "react";
import {
  AnamEvent,
  AudioPermissionState,
  createClient,
  type AnamClient,
  type Message,
} from "@anam-ai/js-sdk";

const VIDEO_ELEMENT_ID = "anam-persona-video";

type SessionResponse = {
  sessionToken: string;
};

type ChatPageClientProps = {
  chatId?: string | null;
  defaultInstructions: string | null;
};

type ChatRole = "user" | "persona";
type InteractionMode = "speak" | "message";

type ChatMessage = {
  id: string;
  content: string;
  role: ChatRole;
  interrupted?: boolean;
};

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while setting up the Anam session.";
}

async function parseErrorResponse(response: Response) {
  const body = (await response.json().catch(() => null)) as
    | { detail?: string }
    | null;

  return body?.detail ?? `Request failed with status ${response.status}`;
}

function mapMessages(messages: Message[]): ChatMessage[] {
  return messages.map((message) => ({
    id: message.id,
    content: message.content,
    role: message.role,
    interrupted: message.interrupted,
  }));
}

export default function ChatPageClient({
  chatId,
  defaultInstructions,
}: ChatPageClientProps) {
  const clientRef = useRef<AnamClient | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);
  const chatSectionRef = useRef<HTMLElement | null>(null);
  const messagesRef = useRef<ChatMessage[]>([]);
  const isFinalizingRef = useRef(false);
  const hasFinalizedRef = useRef(false);
  const isExpired = defaultInstructions === null;

  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [interactionMode, setInteractionMode] =
    useState<InteractionMode>("speak");
  const [status, setStatus] = useState(
    isExpired
      ? "This session is unavailable."
      : "Press Start session to begin speaking.",
  );
  const [warning, setWarning] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isMicMuted, setIsMicMuted] = useState(false);
  const [micPermissionState, setMicPermissionState] =
    useState<AudioPermissionState>(AudioPermissionState.NOT_REQUESTED);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    return () => {
      const client = clientRef.current;
      cleanupRef.current?.();
      cleanupRef.current = null;
      clientRef.current = null;

      if (client) {
        void client.stopStreaming().catch(() => undefined);
      }
    };
  }, []);

  const finalizeHomework = async () => {
    if (!chatId || hasFinalizedRef.current || isFinalizingRef.current) {
      return;
    }

    const transcriptMessages = messagesRef.current
      .map((message) => ({
        role: message.role,
        content: message.content.trim(),
        interrupted: Boolean(message.interrupted),
      }))
      .filter((message) => message.content);

    if (!transcriptMessages.length) {
      return;
    }

    isFinalizingRef.current = true;
    setStatus("Wrapping up homework...");

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"}/api/chat/${encodeURIComponent(chatId)}/complete`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            messages: transcriptMessages,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
      }

      hasFinalizedRef.current = true;
      setStatus("Session stopped. Homework summary saved.");
    } catch (error) {
      setStatus(`Session stopped, but wrap-up failed: ${getErrorMessage(error)}`);
    } finally {
      isFinalizingRef.current = false;
    }
  };

  const handleDisconnect = async () => {
    const client = clientRef.current;
    cleanupRef.current?.();
    cleanupRef.current = null;
    clientRef.current = null;

    if (!client) {
      setIsConnected(false);
      setIsMicMuted(false);
      setMicPermissionState(AudioPermissionState.NOT_REQUESTED);
      setStatus("Session stopped.");
      return;
    }

    try {
      await client.stopStreaming();
    } catch (error) {
      setStatus(getErrorMessage(error));
    } finally {
      setIsConnected(false);
      setIsMicMuted(false);
      setMicPermissionState(AudioPermissionState.NOT_REQUESTED);
      await finalizeHomework();
    }
  };

  const handleConnect = async () => {
    if (isExpired) {
      setStatus("This session is unavailable.");
      return;
    }

    setIsConnecting(true);
    setWarning("");
    setStatus("Requesting an Anam session token...");

    try {
      const response = await fetch("/api/anam/session", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          instructions: defaultInstructions,
        }),
      });

      if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
      }

      const data = (await response.json()) as SessionResponse;
      const client = createClient(data.sessionToken, {
        metrics: {
          disableClientMetrics: true,
        },
      });

      const handleMessageHistoryUpdated = (nextMessages: Message[]) => {
        const mappedMessages = mapMessages(nextMessages);
        messagesRef.current = mappedMessages;
        setMessages(mappedMessages);
      };
      const handleConnectionEstablished = () => {
        setIsConnected(true);
        if (interactionMode === "message") {
          client.muteInputAudio();
        } else {
          client.unmuteInputAudio();
        }
        setIsMicMuted(client.getInputAudioState().isMuted);
        setStatus(
          interactionMode === "speak"
            ? "Speak to the tutor."
            : "Chat mode is active. Type your message.",
        );
      };
      const handleConnectionClosed = (_reason: unknown, details?: string) => {
        setIsConnected(false);
        setIsMicMuted(false);
        setMicPermissionState(AudioPermissionState.NOT_REQUESTED);
        setStatus(details ? `Connection closed: ${details}` : "Connection closed.");
        void finalizeHomework();
      };
      const handleServerWarning = (message: string) => {
        setWarning(message);
      };
      const handleMicPermissionPending = () => {
        setMicPermissionState(AudioPermissionState.PENDING);
        setStatus("Allow microphone access to speak.");
      };
      const handleMicPermissionGranted = () => {
        setMicPermissionState(AudioPermissionState.GRANTED);
        if (interactionMode === "speak") {
          setStatus("Microphone connected. Speak to the tutor.");
        }
      };
      const handleMicPermissionDenied = (error: string) => {
        setMicPermissionState(AudioPermissionState.DENIED);
        setStatus(
          error
            ? `Microphone access was denied: ${error}`
            : "Microphone access was denied. Switch to Chat to type instead.",
        );
      };
      const handleUserSpeechStarted = () => {
        setStatus("Listening...");
      };
      const handleUserSpeechEnded = () => {
        setStatus("Processing...");
      };

      client.addListener(
        AnamEvent.MESSAGE_HISTORY_UPDATED,
        handleMessageHistoryUpdated,
      );
      client.addListener(
        AnamEvent.CONNECTION_ESTABLISHED,
        handleConnectionEstablished,
      );
      client.addListener(AnamEvent.CONNECTION_CLOSED, handleConnectionClosed);
      client.addListener(AnamEvent.SERVER_WARNING, handleServerWarning);
      client.addListener(
        AnamEvent.MIC_PERMISSION_PENDING,
        handleMicPermissionPending,
      );
      client.addListener(
        AnamEvent.MIC_PERMISSION_GRANTED,
        handleMicPermissionGranted,
      );
      client.addListener(
        AnamEvent.MIC_PERMISSION_DENIED,
        handleMicPermissionDenied,
      );
      client.addListener(AnamEvent.USER_SPEECH_STARTED, handleUserSpeechStarted);
      client.addListener(AnamEvent.USER_SPEECH_ENDED, handleUserSpeechEnded);

      cleanupRef.current = () => {
        client.removeListener(
          AnamEvent.MESSAGE_HISTORY_UPDATED,
          handleMessageHistoryUpdated,
        );
        client.removeListener(
          AnamEvent.CONNECTION_ESTABLISHED,
          handleConnectionEstablished,
        );
        client.removeListener(AnamEvent.CONNECTION_CLOSED, handleConnectionClosed);
        client.removeListener(AnamEvent.SERVER_WARNING, handleServerWarning);
        client.removeListener(
          AnamEvent.MIC_PERMISSION_PENDING,
          handleMicPermissionPending,
        );
        client.removeListener(
          AnamEvent.MIC_PERMISSION_GRANTED,
          handleMicPermissionGranted,
        );
        client.removeListener(
          AnamEvent.MIC_PERMISSION_DENIED,
          handleMicPermissionDenied,
        );
        client.removeListener(
          AnamEvent.USER_SPEECH_STARTED,
          handleUserSpeechStarted,
        );
        client.removeListener(AnamEvent.USER_SPEECH_ENDED, handleUserSpeechEnded);
      };

      clientRef.current = client;
      hasFinalizedRef.current = false;
      isFinalizingRef.current = false;
      setMessages([]);
      messagesRef.current = [];
      setStatus("Starting session...");
      await client.streamToVideoElement(VIDEO_ELEMENT_ID);
    } catch (error) {
      cleanupRef.current?.();
      cleanupRef.current = null;
      clientRef.current = null;
      setIsConnected(false);
      setIsMicMuted(false);
      setMicPermissionState(AudioPermissionState.NOT_REQUESTED);
      setStatus(getErrorMessage(error));
    } finally {
      setIsConnecting(false);
    }
  };

  const scrollToChat = () => {
    chatSectionRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const handleInteractionModeChange = (nextMode: InteractionMode) => {
    setInteractionMode(nextMode);

    const client = clientRef.current;
    if (nextMode === "message") {
      scrollToChat();
    }

    if (!client || !isConnected) {
      return;
    }

    try {
      if (nextMode === "speak") {
        client.unmuteInputAudio();
        setIsMicMuted(false);
        setStatus("Speech mode is active. Speak to the tutor.");
      } else {
        client.muteInputAudio();
        setIsMicMuted(true);
        setStatus("Chat mode is active. Type your message.");
      }
    } catch (error) {
      setStatus(getErrorMessage(error));
    }
  };

  const handleSend = async (
    event: SyntheticEvent<HTMLFormElement, SubmitEvent>,
  ) => {
    event.preventDefault();

    const client = clientRef.current;
    const nextDraft = draft.trim();

    if (!client || !isConnected) {
      setStatus("Start the session before sending a message.");
      return;
    }

    if (!nextDraft) {
      setStatus("Write a message before sending it.");
      return;
    }

    setIsSending(true);
    setStatus("Sending message...");

    try {
      client.sendUserMessage(nextDraft);
      setDraft("");
      setStatus("Waiting for the tutor response...");
    } catch (error) {
      setStatus(getErrorMessage(error));
    } finally {
      setIsSending(false);
    }
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f8f1dd_0%,#eadfcf_40%,#cfc7bb_100%)] px-4 py-6 text-stone-950 sm:px-6 sm:py-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 pb-28">
        <section className="rounded-[2rem] border border-stone-900/10 bg-[#fffaf2]/80 p-5 shadow-[0_28px_110px_rgba(72,51,33,0.12)] backdrop-blur sm:p-6">
          <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,1.25fr)_minmax(22rem,0.75fr)] lg:items-start">
            <div className="min-w-0">
              <div className="relative overflow-hidden rounded-[2rem] bg-stone-950 p-3 shadow-[0_30px_90px_rgba(28,25,23,0.28)]">
                <div className="absolute inset-x-4 top-4 z-10 flex flex-wrap gap-2">
                  <span className="rounded-full bg-black/45 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-stone-100 backdrop-blur">
                    {isConnected ? "Live session" : "Ready"}
                  </span>
                  <span className="rounded-full bg-black/45 px-3 py-1 text-xs font-medium text-stone-100 backdrop-blur">
                    {status}
                  </span>
                  {warning ? (
                    <span className="rounded-full bg-amber-300/85 px-3 py-1 text-xs font-medium text-stone-950">
                      {warning}
                    </span>
                  ) : null}
                </div>

                <video
                  autoPlay
                  className="aspect-[4/5] w-full rounded-[1.5rem] bg-stone-900 object-cover"
                  id={VIDEO_ELEMENT_ID}
                  muted={false}
                  playsInline
                />

                <div className="absolute inset-x-4 bottom-4 flex flex-wrap gap-2">
                  <span className="rounded-full bg-white/88 px-3 py-1 text-xs font-medium text-stone-800">
                    {micPermissionState === AudioPermissionState.DENIED
                      ? "Mic blocked"
                      : isMicMuted
                        ? "Mic muted"
                        : micPermissionState === AudioPermissionState.GRANTED
                          ? "Mic live"
                          : micPermissionState === AudioPermissionState.PENDING
                            ? "Waiting for mic"
                            : "Mic idle"}
                  </span>
                </div>
              </div>
            </div>

            <section
              className="min-w-0 rounded-[2rem] border border-stone-900/10 bg-white/88 p-5 shadow-[0_24px_70px_rgba(87,70,45,0.12)] sm:p-6"
              ref={chatSectionRef}
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.28em] text-stone-400">
                    Chat
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold text-stone-950">
                    Conversation
                  </h2>
                </div>
                <p className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-stone-500">
                  {interactionMode === "message" ? "Chat mode" : "Speech mode"}
                </p>
              </div>

              <div className="mt-5 flex max-h-[32rem] min-h-[24rem] flex-col gap-3 overflow-y-auto rounded-[1.5rem] bg-stone-100/90 p-4">
                {messages.length ? (
                  messages.map((message) => (
                    <article
                      className={`max-w-[88%] rounded-[1.5rem] px-4 py-3 text-sm leading-6 shadow-sm ${
                        message.role === "user"
                          ? "ml-auto bg-stone-950 text-stone-50"
                          : "bg-[#f6ebcf] text-stone-900"
                      }`}
                      key={message.id}
                    >
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] opacity-70">
                        {message.role === "user" ? "You" : "Tutor"}
                      </p>
                      <p className="mt-2 whitespace-pre-wrap">
                        {message.content || "…"}
                      </p>
                      {message.interrupted ? (
                        <p className="mt-2 text-[11px] uppercase tracking-[0.18em] opacity-60">
                          Interrupted
                        </p>
                      ) : null}
                    </article>
                  ))
                ) : (
                  <div className="flex min-h-[20rem] items-center justify-center rounded-[1.25rem] border border-dashed border-stone-300 bg-white/70 p-6 text-center text-sm leading-6 text-stone-500">
                    {interactionMode === "message"
                      ? "Start the session and send a message here."
                      : "Start the session and speak to begin. Your conversation will appear here."}
                  </div>
                )}
              </div>

              {interactionMode === "message" ? (
                <form className="mt-4 flex flex-col gap-3" onSubmit={handleSend}>
                  <textarea
                    className="min-h-28 rounded-[1.5rem] border border-stone-300 bg-stone-50 px-4 py-3 outline-none transition focus:border-amber-500"
                    onChange={(event) => setDraft(event.target.value)}
                    placeholder="Type your message to the tutor."
                    value={draft}
                  />
                  <button
                    className="rounded-full bg-stone-950 px-5 py-3 font-semibold text-stone-50 transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400"
                    disabled={!isConnected || isSending}
                    type="submit"
                  >
                    {isSending ? "Sending..." : "Send message"}
                  </button>
                </form>
              ) : (
                <div className="mt-4 rounded-[1.5rem] border border-amber-200 bg-amber-50/70 p-4 text-sm leading-6 text-stone-700">
                  Speech mode is active. Speak naturally to the tutor and switch to
                  Chat whenever you want to type.
                </div>
              )}
            </section>
          </div>
        </section>
      </div>

      <div className="pointer-events-none fixed inset-x-0 bottom-5 z-40 flex justify-center px-4">
        <div className="pointer-events-auto flex w-full max-w-3xl flex-wrap items-center justify-center gap-3 rounded-full border border-stone-900/10 bg-[#fffaf2]/92 px-4 py-3 shadow-[0_24px_90px_rgba(33,24,14,0.18)] backdrop-blur">
          <button
            className="rounded-full bg-stone-950 px-5 py-3 text-sm font-semibold text-stone-50 transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400"
            disabled={isExpired || isConnecting || isConnected}
            onClick={handleConnect}
            type="button"
          >
            {isConnecting ? "Starting..." : "Start session"}
          </button>
          <button
            className="rounded-full border border-stone-300 px-5 py-3 text-sm font-semibold text-stone-700 transition hover:border-stone-500 hover:bg-stone-100 disabled:cursor-not-allowed disabled:border-stone-200 disabled:text-stone-400"
            disabled={!isConnected}
            onClick={() => void handleDisconnect()}
            type="button"
          >
            Stop session
          </button>
          <div className="inline-flex rounded-full border border-stone-300 bg-white p-1">
            {(["speak", "message"] as const).map((mode) => {
              const isActive = interactionMode === mode;

              return (
                <button
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    isActive
                      ? "bg-amber-300 text-stone-950"
                      : "text-stone-600 hover:bg-stone-100"
                  }`}
                  key={mode}
                  onClick={() => handleInteractionModeChange(mode)}
                  type="button"
                >
                  {mode === "speak" ? "Speech" : "Chat"}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </main>
  );
}
