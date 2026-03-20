"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { AnamEvent, createClient, type AnamClient, type Message } from "@anam-ai/js-sdk";

const VIDEO_ELEMENT_ID = "anam-persona-video";
const DEFAULT_INSTRUCTIONS = `You are the live speaking tutor for the Mirror demo.
Keep answers concise, spoken, and natural.
Guide the learner through English practice with specific feedback and clear next steps.
Avoid markdown, bullet points, or long monologues unless explicitly requested.`;

type SessionResponse = {
  sessionToken: string;
};

type ChatRole = "user" | "persona";

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

export default function ChatPage() {
  const clientRef = useRef<AnamClient | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  const [instructions, setInstructions] = useState(DEFAULT_INSTRUCTIONS);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState(
    "Add your instructions, then start the persona session.",
  );
  const [sessionId, setSessionId] = useState("");
  const [warning, setWarning] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isApplyingContext, setIsApplyingContext] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

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

  const handleDisconnect = async () => {
    const client = clientRef.current;
    cleanupRef.current?.();
    cleanupRef.current = null;
    clientRef.current = null;

    if (!client) {
      setIsConnected(false);
      setSessionId("");
      setStatus("Session closed.");
      return;
    }

    try {
      await client.stopStreaming();
      setStatus("Session closed.");
    } catch (error) {
      setStatus(getErrorMessage(error));
    } finally {
      setIsConnected(false);
      setSessionId("");
    }
  };

  const handleConnect = async () => {
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
          instructions,
        }),
      });

      if (!response.ok) {
        throw new Error(await parseErrorResponse(response));
      }

      const data = (await response.json()) as SessionResponse;
      const client = createClient(data.sessionToken, {
        disableInputAudio: true,
        metrics: {
          disableClientMetrics: true,
        },
      });

      const handleMessageHistoryUpdated = (nextMessages: Message[]) => {
        setMessages(mapMessages(nextMessages));
      };
      const handleConnectionEstablished = () => {
        setIsConnected(true);
        setStatus("Persona connected. Send a message to begin.");
      };
      const handleConnectionClosed = (_reason: unknown, details?: string) => {
        setIsConnected(false);
        setSessionId("");
        setStatus(details ? `Connection closed: ${details}` : "Connection closed.");
      };
      const handleSessionReady = (nextSessionId: string) => {
        setSessionId(nextSessionId);
      };
      const handleServerWarning = (message: string) => {
        setWarning(message);
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
      client.addListener(AnamEvent.SESSION_READY, handleSessionReady);
      client.addListener(AnamEvent.SERVER_WARNING, handleServerWarning);

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
        client.removeListener(AnamEvent.SESSION_READY, handleSessionReady);
        client.removeListener(AnamEvent.SERVER_WARNING, handleServerWarning);
      };

      clientRef.current = client;
      setMessages([]);
      setStatus("Starting persona stream...");
      await client.streamToVideoElement(VIDEO_ELEMENT_ID);
    } catch (error) {
      cleanupRef.current?.();
      cleanupRef.current = null;
      clientRef.current = null;
      setIsConnected(false);
      setSessionId("");
      setStatus(getErrorMessage(error));
    } finally {
      setIsConnecting(false);
    }
  };

  const handleSend = async (event: FormEvent<HTMLFormElement>) => {
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
      setStatus("Waiting for the persona response...");
    } catch (error) {
      setStatus(getErrorMessage(error));
    } finally {
      setIsSending(false);
    }
  };

  const handleApplyContext = async () => {
    const client = clientRef.current;
    const nextInstructions = instructions.trim();

    if (!client || !isConnected) {
      setStatus("Start the session before applying live context.");
      return;
    }

    if (!nextInstructions) {
      setStatus("Add instructions before applying them.");
      return;
    }

    setIsApplyingContext(true);

    try {
      client.addContext(
        `Instruction update from the Mirror team:\n${nextInstructions}`,
      );
      setStatus("Instructions pushed into the active session as context.");
    } catch (error) {
      setStatus(getErrorMessage(error));
    } finally {
      setIsApplyingContext(false);
    }
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f8f1dd_0%,#eadfcf_42%,#c9c3b3_100%)] px-6 py-10 text-stone-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <section className="rounded-[2rem] border border-stone-900/10 bg-[#fffaf2]/90 p-8 shadow-[0_28px_110px_rgba(72,51,33,0.14)] backdrop-blur">
          <p className="text-sm font-semibold uppercase tracking-[0.35em] text-amber-700">
            Anam Persona Chat
          </p>
          <h1 className="mt-4 max-w-4xl text-4xl font-semibold tracking-tight sm:text-6xl">
            Run a live tutor persona with instructions we control.
          </h1>
          <p className="mt-4 max-w-3xl text-lg leading-8 text-stone-700">
            This page requests a server-side Anam session token, streams the
            persona into the browser, and sends typed chat messages through the
            active realtime session.
          </p>
        </section>

        <div className="grid gap-6 xl:grid-cols-[0.82fr_1.18fr]">
          <section className="rounded-[2rem] bg-stone-950 p-6 text-stone-50 shadow-[0_30px_100px_rgba(28,25,23,0.35)]">
            <div className="flex flex-col gap-5">
              <div>
                <h2 className="text-2xl font-semibold">Persona control</h2>
                <p className="mt-2 text-sm leading-6 text-stone-300">
                  The instructions below are sent to the server and injected
                  into Anam&apos;s <code>systemPrompt</code> when the session starts.
                </p>
              </div>

              <label className="flex flex-col gap-2 text-sm font-medium text-stone-200">
                Team instructions
                <textarea
                  className="min-h-56 rounded-[1.5rem] border border-stone-700 bg-stone-900/80 px-4 py-3 text-stone-100 outline-none transition focus:border-amber-300"
                  onChange={(event) => setInstructions(event.target.value)}
                  placeholder="Describe tone, teaching rules, and constraints."
                  value={instructions}
                />
              </label>

              <div className="flex flex-wrap gap-3">
                <button
                  className="rounded-full bg-amber-300 px-5 py-3 font-semibold text-stone-950 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:bg-stone-700 disabled:text-stone-300"
                  disabled={isConnecting || isConnected}
                  onClick={handleConnect}
                  type="button"
                >
                  {isConnecting ? "Starting..." : "Start session"}
                </button>
                <button
                  className="rounded-full border border-stone-600 px-5 py-3 font-semibold text-stone-100 transition hover:border-stone-400 hover:bg-stone-900/70 disabled:cursor-not-allowed disabled:border-stone-800 disabled:text-stone-500"
                  disabled={!isConnected}
                  onClick={() => void handleDisconnect()}
                  type="button"
                >
                  Stop session
                </button>
                <button
                  className="rounded-full border border-amber-300/40 px-5 py-3 font-semibold text-amber-100 transition hover:bg-amber-300/10 disabled:cursor-not-allowed disabled:border-stone-800 disabled:text-stone-500"
                  disabled={!isConnected || isApplyingContext}
                  onClick={handleApplyContext}
                  type="button"
                >
                  {isApplyingContext ? "Applying..." : "Apply live context"}
                </button>
              </div>

              <div className="rounded-[1.5rem] border border-stone-800 bg-stone-900/70 p-4 text-sm leading-7 text-stone-300">
                <p>
                  <span className="font-semibold text-stone-100">Status:</span>{" "}
                  {status}
                </p>
                <p>
                  <span className="font-semibold text-stone-100">Session ID:</span>{" "}
                  {sessionId || "Waiting for session start"}
                </p>
                <p>
                  <span className="font-semibold text-stone-100">Live context:</span>{" "}
                  Reconnect to fully replace the system prompt. Use live context
                  to push updates into the current session.
                </p>
                {warning ? (
                  <p className="text-amber-200">
                    <span className="font-semibold text-amber-100">Warning:</span>{" "}
                    {warning}
                  </p>
                ) : null}
              </div>
            </div>
          </section>

          <section className="grid gap-6">
            <div className="grid gap-6 lg:grid-cols-[0.88fr_1.12fr]">
              <div className="rounded-[2rem] border border-stone-900/10 bg-[#f4eadb] p-5 shadow-[0_24px_70px_rgba(87,70,45,0.1)]">
                <div className="rounded-[1.5rem] bg-stone-950 p-3 shadow-inner">
                  <video
                    autoPlay
                    className="aspect-[4/5] w-full rounded-[1.2rem] bg-stone-900 object-cover"
                    id={VIDEO_ELEMENT_ID}
                    muted={false}
                    playsInline
                  />
                </div>
                <p className="mt-4 text-sm leading-6 text-stone-600">
                  The Anam persona video stream appears here after the session is
                  established.
                </p>
              </div>

              <div className="rounded-[2rem] border border-stone-900/10 bg-white/85 p-6 shadow-[0_24px_70px_rgba(87,70,45,0.12)]">
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-semibold">Chat</h2>
                    <p className="mt-2 text-sm leading-6 text-stone-600">
                      Messages are sent through Anam&apos;s active realtime session.
                    </p>
                  </div>
                  <p className="text-xs font-semibold uppercase tracking-[0.25em] text-stone-400">
                    {isConnected ? "Connected" : "Offline"}
                  </p>
                </div>

                <div className="mt-6 flex min-h-96 flex-col gap-3 overflow-y-auto rounded-[1.5rem] bg-stone-100/90 p-4">
                  {messages.length ? (
                    messages.map((message) => (
                      <article
                        className={`max-w-[85%] rounded-[1.5rem] px-4 py-3 text-sm leading-6 shadow-sm ${
                          message.role === "user"
                            ? "ml-auto bg-stone-950 text-stone-50"
                            : "bg-[#f6ebcf] text-stone-900"
                        }`}
                        key={message.id}
                      >
                        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] opacity-70">
                          {message.role === "user" ? "You" : "Persona"}
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
                    <div className="flex min-h-80 items-center justify-center rounded-[1.25rem] border border-dashed border-stone-300 bg-white/70 p-6 text-center text-sm leading-6 text-stone-500">
                      Start a session to see the conversation history here.
                    </div>
                  )}
                </div>

                <form className="mt-4 flex flex-col gap-3" onSubmit={handleSend}>
                  <label className="flex flex-col gap-2 text-sm font-medium text-stone-700">
                    Message
                    <textarea
                      className="min-h-28 rounded-[1.5rem] border border-stone-300 bg-stone-50 px-4 py-3 outline-none transition focus:border-amber-500"
                      onChange={(event) => setDraft(event.target.value)}
                      placeholder="Ask the persona to roleplay, explain, or coach."
                      value={draft}
                    />
                  </label>

                  <button
                    className="rounded-full bg-stone-950 px-5 py-3 font-semibold text-stone-50 transition hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-400"
                    disabled={!isConnected || isSending}
                    type="submit"
                  >
                    {isSending ? "Sending..." : "Send message"}
                  </button>
                </form>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
