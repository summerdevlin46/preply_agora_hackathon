"use client";

import { SyntheticEvent, useEffect, useRef, useState } from "react";
import styled, { keyframes } from "styled-components";
import {
  AnamEvent,
  AudioPermissionState,
  createClient,
  type AnamClient,
  type Message,
  type MessageStreamEvent,
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

function applyMessageStreamEvent(
  currentMessages: ChatMessage[],
  event: MessageStreamEvent,
): ChatMessage[] {
  if (event.role === "user") {
    return [
      ...currentMessages,
      {
        id: event.id,
        content: event.content,
        role: event.role,
      },
    ];
  }

  const existingMessageIndex = currentMessages.findIndex(
    (message) => message.id === event.id,
  );

  if (existingMessageIndex === -1) {
    return [
      ...currentMessages,
      {
        id: event.id,
        content: event.content,
        role: event.role,
        interrupted: event.interrupted,
      },
    ];
  }

  return currentMessages.map((message, index) =>
    index === existingMessageIndex
      ? {
          ...message,
          content: message.content + event.content,
          interrupted: Boolean(message.interrupted || event.interrupted),
        }
      : message,
  );
}

/* -- keyframes -- */
const fadeUp = keyframes`
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
`;

/* -- styled components -- */
const Page = styled.div`
  font-family: inherit;
  background: #fff;
  min-height: 100vh;
  color: #111827;
`;

const Container = styled.div`
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 24px;
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: 1.25fr 0.75fr;
  gap: 24px;
  align-items: start;
`;

const Card = styled.section`
  background: #fff;
  border: 2px solid #dad9de;
  border-radius: 12px;
  overflow: hidden;
  animation: ${fadeUp} 0.3s ease;
`;

const VideoWrap = styled.div`
  position: relative;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  margin: 14px;
`;

const Video = styled.video`
  aspect-ratio: 4 / 5;
  width: 100%;
  background: #000;
  display: block;
  object-fit: cover;
`;

const VideoOverlay = styled.div`
  position: absolute;
  left: 12px;
  right: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  z-index: 10;
`;

const TopOverlay = styled(VideoOverlay)`
  top: 12px;
`;

const BottomOverlay = styled(VideoOverlay)`
  bottom: 12px;
`;

const VideoPill = styled.span<{ $variant?: "warning" }>`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  background: ${(props) => (props.$variant === "warning" ? "#fff7c1" : "rgba(0,0,0,0.5)")};
  color: ${(props) => (props.$variant === "warning" ? "#000" : "#fff")};
`;

const ChatSection = styled.section`
  background: #fff;
  border: 2px solid #dad9de;
  border-radius: 12px;
  padding: 24px;
  animation: ${fadeUp} 0.3s ease;
`;

const ChatHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
`;

const ChatLabel = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #9ca3af;
  margin: 0 0 4px;
`;

const ChatTitle = styled.h2`
  font-family: inherit;
  font-size: 22px;
  font-weight: 500;
  letter-spacing: 0.04em;
  margin: 0;
  color: #111827;
`;

const ModePill = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 10px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(0,0,0,.05);
  color: #000;
  text-transform: uppercase;
  letter-spacing: 0.04em;
`;

const MessagesWrap = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 32rem;
  min-height: 24rem;
  overflow-y: auto;
  background: #FAFAFA;
  border: 2px solid #dad9de;
  border-radius: 12px;
  padding: 14px;
`;

const EmptyMessages = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 20rem;
  border: 2px dashed #dad9de;
  border-radius: 12px;
  background: #fff;
  padding: 24px;
  text-align: center;
  font-family: "PreplyInter", sans-serif;
  font-size: 13px;
  color: #9ca3af;
  line-height: 1.6;
`;

const MessageBubble = styled.article<{ $isUser: boolean }>`
  max-width: 88%;
  border-radius: 12px;
  padding: 10px 14px;
  font-family: "PreplyInter", sans-serif;
  font-size: 13px;
  line-height: 1.6;
  margin-left: ${(props) => (props.$isUser ? "auto" : "0")};
  background: ${(props) => (props.$isUser ? "#000" : "#fff7c1")};
  color: ${(props) => (props.$isUser ? "#fff" : "#000")};
  border: ${(props) => (props.$isUser ? "none" : "2px solid rgba(0,0,0,.08)")};
`;

const MessageRole = styled.p`
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.6;
  margin: 0 0 4px;
`;

const MessageContent = styled.p`
  margin: 0;
  white-space: pre-wrap;
`;

const InterruptedTag = styled.p`
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.5;
  margin: 4px 0 0;
`;

const SpeechHint = styled.div`
  font-family: "PreplyInter", sans-serif;
  font-size: 13px;
  color: #000;
  line-height: 1.6;
  background: #fff7c1;
  border: 2px solid #000;
  border-radius: 12px;
  padding: 12px 14px;
  margin-top: 14px;
`;

const ChatForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
`;

const Textarea = styled.textarea`
  width: 100%;
  min-height: 80px;
  border: 2px solid #dad9de;
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 14px;
  color: #374151;
  font-family: "PreplyInter", sans-serif;
  resize: vertical;
  outline: none;
  line-height: 1.6;
  transition: border-color 0.15s;

  &:focus {
    border-color: #000;
  }
`;

const SendBtn = styled.button`
  width: 100%;
  background: #ff7aac;
  color: #000;
  border: 2px solid #000;
  border-radius: 12px;
  padding: 12px;
  font-size: 14px;
  font-weight: 600;
  font-family: "PreplyInter", sans-serif;
  cursor: pointer;
  transition: all 0.15s;
  letter-spacing: 0.01em;

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
`;

const BottomBar = styled.div`
  position: fixed;
  bottom: 20px;
  left: 0;
  right: 0;
  z-index: 40;
  display: flex;
  justify-content: center;
  padding: 0 16px;
  pointer-events: none;
`;

const BottomBarInner = styled.div`
  pointer-events: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  background: #fff;
  border: 2px solid #000;
  border-radius: 12px;
  padding: 10px 16px;
`;

const StartBtn = styled.button`
  background: #ff7aac;
  color: #000;
  border: 2px solid #000;
  border-radius: 12px;
  padding: 10px 20px;
  font-size: 13px;
  font-weight: 600;
  font-family: "PreplyInter", sans-serif;
  cursor: pointer;
  transition: all 0.15s;
  letter-spacing: 0.01em;

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
`;

const StopBtn = styled.button`
  background: #fff;
  color: #000;
  border: 2px solid #dad9de;
  border-radius: 12px;
  padding: 10px 20px;
  font-size: 13px;
  font-weight: 600;
  font-family: "PreplyInter", sans-serif;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    border-color: #000;
  }

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
`;

const ModeToggle = styled.div`
  display: inline-flex;
  border: 2px solid #dad9de;
  border-radius: 12px;
  background: #fff;
  padding: 3px;
`;

const ModeBtn = styled.button<{ $active: boolean }>`
  font-family: "PreplyInter", sans-serif;
  font-size: 13px;
  font-weight: 600;
  padding: 7px 14px;
  border: none;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.15s;
  background: ${(props) => (props.$active ? "#ff7aac" : "transparent")};
  color: #000;
`;

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
      const handleMessageStreamEventReceived = (
        messageEvent: MessageStreamEvent,
      ) => {
        setMessages((currentMessages) => {
          const nextMessages = applyMessageStreamEvent(
            currentMessages,
            messageEvent,
          );
          messagesRef.current = nextMessages;
          return nextMessages;
        });
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
        AnamEvent.MESSAGE_STREAM_EVENT_RECEIVED,
        handleMessageStreamEventReceived,
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
          AnamEvent.MESSAGE_STREAM_EVENT_RECEIVED,
          handleMessageStreamEventReceived,
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

  const micLabel =
    micPermissionState === AudioPermissionState.DENIED
      ? "Mic blocked"
      : isMicMuted
        ? "Mic muted"
        : micPermissionState === AudioPermissionState.GRANTED
          ? "Mic live"
          : micPermissionState === AudioPermissionState.PENDING
            ? "Waiting for mic"
            : "Mic idle";

  return (
    <Page>
      <Container>
        <Grid>
          {/* Video */}
          <Card>
            <VideoWrap>
              <TopOverlay>
                <VideoPill>{isConnected ? "Live session" : "Ready"}</VideoPill>
                <VideoPill>{status}</VideoPill>
                {warning ? <VideoPill $variant="warning">{warning}</VideoPill> : null}
              </TopOverlay>

              <Video
                autoPlay
                id={VIDEO_ELEMENT_ID}
                muted={false}
                playsInline
              />

              <BottomOverlay>
                <VideoPill>{micLabel}</VideoPill>
              </BottomOverlay>
            </VideoWrap>
          </Card>

          {/* Chat */}
          <ChatSection ref={chatSectionRef}>
            <ChatHeader>
              <div>
                <ChatLabel>Chat</ChatLabel>
                <ChatTitle>Conversation</ChatTitle>
              </div>
              <ModePill>
                {interactionMode === "message" ? "Chat mode" : "Speech mode"}
              </ModePill>
            </ChatHeader>

            <MessagesWrap>
              {messages.length ? (
                messages.map((message) => (
                  <MessageBubble $isUser={message.role === "user"} key={message.id}>
                    <MessageRole>
                      {message.role === "user" ? "You" : "Tutor"}
                    </MessageRole>
                    <MessageContent>{message.content || "…"}</MessageContent>
                    {message.interrupted ? (
                      <InterruptedTag>Interrupted</InterruptedTag>
                    ) : null}
                  </MessageBubble>
                ))
              ) : (
                <EmptyMessages>
                  {interactionMode === "message"
                    ? "Start the session and send a message here."
                    : "Start the session and speak to begin. Your conversation will appear here."}
                </EmptyMessages>
              )}
            </MessagesWrap>

            {interactionMode === "message" ? (
              <ChatForm onSubmit={handleSend}>
                <Textarea
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="Type your message to the tutor."
                  value={draft}
                />
                <SendBtn disabled={!isConnected || isSending} type="submit">
                  {isSending ? "Sending..." : "Send message"}
                </SendBtn>
              </ChatForm>
            ) : (
              <SpeechHint>
                Speech mode is active. Speak naturally to the tutor and switch to
                Chat whenever you want to type.
              </SpeechHint>
            )}
          </ChatSection>
        </Grid>
      </Container>

      {/* Bottom bar */}
      <BottomBar>
        <BottomBarInner>
          <StartBtn
            disabled={isExpired || isConnecting || isConnected}
            onClick={handleConnect}
            type="button"
          >
            {isConnecting ? "Starting..." : "Start session"}
          </StartBtn>
          <StopBtn
            disabled={!isConnected}
            onClick={() => void handleDisconnect()}
            type="button"
          >
            Stop session
          </StopBtn>
          <ModeToggle>
            {(["speak", "message"] as const).map((mode) => (
              <ModeBtn
                $active={interactionMode === mode}
                key={mode}
                onClick={() => handleInteractionModeChange(mode)}
                type="button"
              >
                {mode === "speak" ? "Speech" : "Chat"}
              </ModeBtn>
            ))}
          </ModeToggle>
        </BottomBarInner>
      </BottomBar>
    </Page>
  );
}
