"use client";

import { getApiBaseUrl, getAppBaseUrl } from "@/lib/api";
import { useState, useRef, useCallback } from "react";
import styled, { keyframes } from "styled-components";
import { getTeacherReport } from "@/lib/chat-instructions";
import {
  BookOpen, Mic, PenLine, FileText, FolderOpen, ImageIcon,
  FilePen, X, Sparkles, ClipboardList, FileSpreadsheet, Check, ArrowLeft,
  Lightbulb, RefreshCw, ChevronDown, ChevronUp
} from "lucide-react";

const ASSIGNMENT_TYPES = [
  {
    id: "speaking",
    label: "Avatar Conversation",
    sublabel: "Fluency & Turn-Taking",
    icon: Mic,
    color: "#7C3AED",
    bg: "#F5F3FF",
    border: "#DDD6FE",
    avatarRole: "Conversational partner",
    avatarVerb: "speaks with",
    mechanicLabel: "How the conversation works:",
    mechanic: "The avatar opens the session with a warm greeting and a context-setting question drawn from your worksheet. It listens to the student\u2019s full spoken response, mirrors key phrases back naturally, and gently recasts any errors before asking a follow-up \u2014 keeping the dialogue flowing in real-time turns until the topic is covered.",
    tip: "Sofia waits for your complete answer before speaking. Take your time \u2014 there\u2019s no need to rush or interrupt.",
  },
  {
    id: "vocab",
    label: "Vocabulary Challenge",
    sublabel: "Spoken Word Production",
    icon: BookOpen,
    color: "#0891B2",
    bg: "#ECFEFF",
    border: "#A5F3FC",
    avatarRole: "Vocabulary coach",
    avatarVerb: "quizzes",
    mechanicLabel: "How the vocabulary drill works:",
    mechanic: "The avatar presents each target word through a spoken definition, an example context, or a fill-in-the-blank prompt. The student says the word aloud and uses it in a sentence \u2014 or types it in chat if unsure. The avatar confirms correct usage instantly or models the right form, then moves to the next word until the full set is drilled.",
    tip: "Max won\u2019t show you anything visual \u2014 all clues are spoken. You can also type a word in the chat if you\u2019re unsure how to pronounce it.",
  },
  {
    id: "writing",
    label: "Dictation & Feedback",
    sublabel: "Writing + Spoken Review",
    icon: PenLine,
    color: "#059669",
    bg: "#ECFDF5",
    border: "#A7F3D0",
    avatarRole: "Writing coach",
    avatarVerb: "coaches",
    mechanicLabel: "How the dictation works:",
    mechanic: "The avatar reads a sentence aloud \u2014 built from your worksheet\u2019s vocabulary and structures \u2014 and waits for the student to type it into the chat. After each entry, it highlights spelling or grammar slips with spoken feedback and re-reads the sentence if asked. At the end, it summarises recurring error patterns so the student knows what to review.",
    tip: "Type into the chat exactly what you hear \u2014 don\u2019t edit as you go. Priya will give spoken corrections after each sentence.",
  },
  {
    id: "grammar",
    label: "Error Detective",
    sublabel: "Form-Focused Grammar",
    icon: FileText,
    color: "#D97706",
    bg: "#FFFBEB",
    border: "#FDE68A",
    avatarRole: "Grammar coach",
    avatarVerb: "coaches",
    mechanicLabel: "How the error detection works:",
    mechanic: "The avatar reads a sentence containing a deliberate grammar mistake and challenges the student to spot and fix it \u2014 by voice or chat. Once the student responds, the avatar asks them to explain the underlying rule before confirming or clarifying it. Difficulty ramps up across rounds, reinforcing the target structures from your worksheet.",
    tip: "Leo reads the full sentence first without signalling the error. Listen to the whole thing before deciding if it sounds right \u2014 just like you would in real life.",
  },
];

const DEMO_OUTPUTS = {
  speaking: {
    title: "Kitchen Chat: Present Continuous Conversation",
    objective: "Student practises present continuous fluency through a structured back-and-forth conversation with Sofia about cooking actions.",
    avatar_name: "Sofia",
    avatar_prompt: `You are Sofia, a warm and encouraging cooking show host conducting a spoken conversation with a B1 English student. Your goal is to practise the present continuous tense through natural dialogue about cooking.

Structure the session in three turns:
1. Ask the student what they are doing right now in the kitchen \u2014 wait for their full response before reacting.
2. Ask them to describe the steps of making their favourite dish one by one, responding naturally between each step.
3. Ask them a follow-up opinion question about cooking (e.g. \u201cWhich do you prefer \u2014 baking or frying? What are you thinking about making this weekend?\u201d).

After each student turn: acknowledge what they said, correct any present continuous errors naturally in your reply (model the correct form, do not just say \u201cwrong\u201d), and ask the next question. Vocabulary to reinforce: fry, bake, boil, whisk, chop, grill, pour, mix; utensils: pan, pot, spatula, cutting board.`,
    tasks: [
      { label: "Opening Question", content: "Sofia opens by asking what you are doing in the kitchen right now. Answer in full present continuous sentences \u2014 describe what you\u2019re cooking step by step." },
      { label: "Dish Description", content: "Sofia asks you to describe making your favourite dish. Talk through the steps conversationally, using present continuous: \u201cFirst I am chopping the onion, now I am frying it\u2026\u201d" },
      { label: "Opinion Follow-Up", content: "Sofia asks a broader question about your cooking habits. Answer naturally in conversation \u2014 she\u2019ll pick up on any tense errors and weave corrections into her reply." },
    ],
    tip: "Sofia waits for your complete answer before speaking. Take your time \u2014 there\u2019s no need to rush or interrupt.",
  },
  vocab: {
    title: "Cooking Vocabulary: Spoken Word Challenge",
    objective: "Student retrieves and produces cooking vocabulary aloud by responding to verbal definitions and using target words in full sentences.",
    avatar_name: "Max",
    avatar_prompt: `You are Max, an encouraging vocabulary coach working with a B1 English student on cooking vocabulary. You will run a spoken word challenge \u2014 no images or visual cues, everything is verbal.

For each word, follow this pattern:
1. Give a clear verbal description or definition of the target word (e.g. \u201cThis is a flat tool you use to flip food in a frying pan \u2014 what is it called?\u201d)
2. Wait for the student to say the word aloud OR type it in the chat.
3. If correct: confirm enthusiastically, then ask them to use it in a present continuous sentence (e.g. \u201cGreat! Now use it in a sentence \u2014 what is the chef doing?\u201d)
4. If incorrect or unsure: say the word clearly, explain it again briefly, then move to the next.

Run through these words in order: spatula, whisk, chopping board, kettle, pan, pot \u2014 then these verbs: fry, bake, boil, chop, grill, pour, mix. After all words, briefly recap any the student missed.`,
    tasks: [
      { label: "Listen & Respond", content: "Max describes each word or utensil out loud. Say the word aloud when you know it \u2014 or type it in the chat if you prefer. No guessing pressure: Max will tell you if you\u2019re stuck." },
      { label: "Use It in a Sentence", content: "After each correct answer, Max asks you to use the word in a present continuous sentence. Speak naturally \u2014 Max responds to what you say before moving on." },
      { label: "Missed Words Recap", content: "At the end, Max revisits any words you hesitated on. Listen to his description again and try once more." },
    ],
    tip: "Max won\u2019t show you anything visual \u2014 all clues are spoken. You can also type a word in the chat if you\u2019re unsure how to pronounce it.",
  },
  writing: {
    title: "Cooking Dictation & Spoken Feedback",
    objective: "Student types sentences dictated by the avatar, practising spelling and grammar, then receives spoken feedback on patterns of error.",
    avatar_name: "Priya",
    avatar_prompt: `You are Priya, a patient and precise writing coach working with a B1 English student. You will run a spoken dictation exercise using present continuous sentences about cooking.

For each sentence:
1. Read the sentence clearly and at natural speed (e.g. \u201cShe is whisking the cake batter in a large bowl.\u201d)
2. Tell the student to type what they heard into the chat.
3. Wait for their typed response.
4. Give brief spoken feedback: confirm if correct, or point out the specific spelling or grammar error and say the correct version.
5. Move to the next sentence.

Use 6 dictation sentences that combine lesson vocabulary (fry, bake, boil, whisk, chop, grill, pour, mix) with utensils (pan, pot, spatula, cutting board) in present continuous form. After all 6, give a spoken summary of any patterns you noticed \u2014 e.g. spelling errors, missing -ing, wrong verb form.`,
    tasks: [
      { label: "Type What You Hear", content: "Priya reads a sentence aloud at natural pace. Type exactly what you hear into the chat. Don\u2019t worry about perfection \u2014 Priya gives feedback after each one." },
      { label: "Listen for Corrections", content: "After you type, Priya speaks her feedback. If you made an error, she says the correct version. Listen carefully before she moves to the next sentence." },
      { label: "Error Pattern Summary", content: "After 6 sentences, Priya gives a spoken summary of patterns in your errors \u2014 e.g. missing -ing, spelling of irregular verbs. Note down anything to review." },
    ],
    tip: "Type into the chat exactly what you hear \u2014 don\u2019t edit as you go. Priya will give spoken corrections after each sentence.",
  },
  grammar: {
    title: "Error Detective: Present Continuous",
    objective: "Student listens to sentences with deliberate grammar errors, responds with the correction by voice or chat, then explains the rule.",
    avatar_name: "Leo",
    avatar_prompt: `You are Leo, a sharp and encouraging grammar coach working with a B1 English student. You will read sentences aloud that contain deliberate present continuous errors.

For each sentence:
1. Read the sentence clearly \u2014 do not signal that it contains an error.
2. Say: \u201cDoes that sound right to you?\u201d
3. Wait for the student to respond by voice or to type their correction in the chat.
4. If they identify the error: ask them to explain the rule \u2014 \u201cWhy is that wrong \u2014 what\u2019s the grammar rule?\u201d
5. Confirm the rule or gently clarify if their explanation is incomplete.
6. Say the corrected sentence clearly before moving on.

Use these error types across 6 sentences: missing \u2018be\u2019 verb (\u201cShe mixing the batter\u201d), wrong be-form (\u201cThey is grilling the vegetables\u201d), missing -ing (\u201cHe is fry the onion\u201d), and incorrect word order. After all 6, give a score and briefly summarise any rules they struggled with.`,
    tasks: [
      { label: "Does That Sound Right?", content: "Leo reads a sentence aloud and asks if it sounds correct. Respond by voice \u2014 say \u201cyes\u201d or say the corrected version in full. You can also type your correction in the chat." },
      { label: "Explain the Rule", content: "When you spot an error, Leo asks you to explain why it\u2019s wrong. Say the grammar rule out loud in your own words \u2014 e.g. \u201cThe verb \u2018be\u2019 has to match the subject.\u201d" },
      { label: "Score & Summary", content: "After 6 sentences, Leo tells you your score and talks through any rules you found tricky. Listen to his summary and ask follow-up questions if anything is unclear." },
    ],
    tip: "Leo reads the full sentence first without signalling the error. Listen to the whole thing before deciding if it sounds right \u2014 just like you would in real life.",
  },
};

const HOW_STEPS = [
  { icon: FileText, text: "Worksheet & lesson context sent to an AI agent" },
  { icon: Sparkles, text: "Tailored avatar prompt is generated per mode" },
  { icon: Mic, text: "Student launches a live Anam AI session" },
  { icon: ClipboardList, text: "Avatar guides the exercise with spoken feedback" },
  { icon: Check, text: "Lesson report sent back to the teacher" },
];

const ACCEPT_TYPES = ".pdf,.jpg,.jpeg,.png,.docx,.doc";

const MODE_MAP = {
  speaking: "avatar_conversation",
  vocab: "vocabulary_challenge",
  writing: "read_aloud_review",
  grammar: "error_detective",
};

const DEMO_FILE = {
  file: { name: "SV-Cooking-Present-Continuous.pdf", size: 812400 },
  id: "demo-file",
};

const DEMO_PROMPT =
  "Student practised present continuous using a cooking-themed worksheet. They know vocabulary: fry, bake, boil, whisk, chop, grill, pour, mix, pan, pot, spatula, cutting board. Level B1.";

/* -- keyframes -- */
const spin = keyframes`
  to { transform: rotate(360deg); }
`;

const pulse = keyframes`
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
`;

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

const Header = styled.div`
  margin-bottom: 32px;
`;

const TitleRow = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
`;

const BackButton = styled.button`
  background: none;
  border: none;
  padding: 6px;
  cursor: pointer;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  transition: all 0.15s;

  &:hover {
    color: #111827;
    background: #f3f4f6;
  }
`;

const Title = styled.h1`
  font-family: inherit;
  font-size: 32px;
  font-weight: 400;
  letter-spacing: 0.04em;
  margin: 0;
  color: #111827;
`;

const Subtitle = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 15px;
  color: #6b7280;
  margin: 0;
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 32px;
  align-items: start;
`;

const Sidebar = styled.nav`
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const SidebarItem = styled.button`
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  letter-spacing: 0.04em;
  font-weight: ${(props) => (props.$active ? "600" : "500")};
  color: ${(props) => (props.$active ? props.$color || "#111827" : "#6b7280")};
  background: ${(props) => (props.$active ? props.$bg || "#f3f4f6" : "transparent")};
  transition: all 0.15s;
  text-align: left;

  &:hover {
    background: ${(props) => props.$bg || "#f3f4f6"};
    color: ${(props) => props.$color || "#111827"};
  }
`;

const MainCol = styled.div`
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const SectionTitle = styled.h2`
  font-family: inherit;
  font-size: 22px;
  font-weight: 500;
  letter-spacing: 0.06em;
  margin: 0;
  color: #111827;
`;

const Card = styled.section`
  background: #fff;
  border: 2px solid #dad9de;
  border-radius: 12px;
  padding: 24px;
  box-shadow: none;
`;

const CardHeader = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
`;

const CardStep = styled.span`
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #111827;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
`;

const CardTitle = styled.h2`
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.06em;
  margin: 0 0 2px;
  color: #111827;
`;

const CardDesc = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 13px;
  color: #9ca3af;
  margin: 0;
`;

const Dropzone = styled.div`
  border: 2px solid #000;
  border-radius: 12px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: ${(props) => (props.$dragging ? "#EEF2FF" : "#FAFAFA")};
  display:flex;
  align-items:center;
  flex-direction:column;
`;

const DropzoneIcon = styled.div`
  margin-bottom: 8px;
  color: #000;
`;

const DropzoneText = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 4px;
`;

const DropzoneHint = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 12px;
  color: rgba(0,0,0,.5);
  margin: 0;
`;

const FileList = styled.ul`
  list-style: none;
  margin: 14px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const FileItem = styled.li`
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 12px;
`;

const FileIcon = styled.span`
  display: flex;
  color: #6b7280;
`;

const FileName = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 13px;
  color: #374151;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const FileSize = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  color: #9ca3af;
  flex-shrink: 0;
`;

const RemoveBtn = styled.button`
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 12px;
  padding: 0 4px;
  flex-shrink: 0;
`;

const Textarea = styled.textarea`
  width: 100%;
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
`;

const CharCount = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  color: #9ca3af;
`;

const PromptFooter = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
`;

const OptimizeBtn = styled.button`
  display: flex;
  align-items: center;
  gap: 6px;
  background: #ff7aac;
  border: 2px solid #000;
  border-radius: 12px;
  padding: 7px 14px;
  font-size: 14px;
  font-weight: 600;
  color: #000;
  cursor: pointer;
  font-family: "PreplyInter", sans-serif;
  transition: all 0.17s ease;
  letter-spacing: 0.01em;

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
`;

const OptSpinner = styled.span`
  width: 14px;
  height: 14px;
  border: 2px solid rgba(0,0,0,.1);
  border-top: 2px solid #000000;
  border-radius: 50%;
  display: inline-block;
  animation: ${spin} 0.7s linear infinite;
`;

const OptimizedBanner = styled.div`
  display: flex;
  align-items: center;
  gap: 7px;
  background: #ECFDF5;
  border: 2px solid #A7F3D0;
  border-radius: 12px;
  padding: 8px 12px;
  margin-top: 10px;
  font-family: "PreplyInter", sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: #065F46;
  animation: ${fadeUp} 0.25s ease;
`;

const MechanicBox = styled.div`
  display: flex;
  gap: 10px;
  align-items: flex-start;
  background: #fff7c1;
  border: 2px solid #000;
  border-radius: 12px;
  padding: 12px 14px;
  animation: ${fadeUp} 0.2s ease;
`;

const MechanicText = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 16px;
  color: #4B5563;
  margin: 0;
  letter-spacing: -0.02em;
  
  strong {
    color:#000;
  }
`;

const GenerateBtn = styled.button`
  width: 100%;
  background: #ff7aac;
  color: #000;
  border: none;
  border-radius: 12px;
  padding: 16px;
  font-size: 15px;
  font-weight: 700;
  font-family: "PreplyInter", sans-serif;
  transition: all 0.15s ease;
  letter-spacing: 0.01em;
  border: 2px solid #000;
  opacity: ${(props) => (props.$canGenerate ? 1 : 0.5)};
  cursor: ${(props) => (props.$canGenerate ? "pointer" : "not-allowed")};
`;

const GenerateHint = styled.p`
  font-family: "PreplyInter", sans-serif;
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
  margin: 0;
`;

const SpinnerWrap = styled.span`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
`;

const Spinner = styled.span`
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0,0,0,.1);
  border-top: 2px solid #000;
  border-radius: 50%;
  display: inline-block;
  animation: ${spin} 0.7s linear infinite;
`;

const OutputCard = styled.section`
  background: #fff;
  border: 2px solid ${(props) => props.$borderColor || "#dad9de"};
  border-radius: 12px;
  overflow: hidden;
  box-shadow: none;
  animation: ${fadeUp} 0.3s ease;
`;

const OutputHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid #f3f4f6;
  background: #fff;
`;

const OutputHeaderLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`;

const OutputDot = styled.span`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
`;

const OutputTitle = styled.span`
  font-size: 13px;
  font-weight: 600;
  color: #374151;
`;

const ModePill = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
`;

const CopyBtn = styled.button`
  background: none;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s;

  &:hover {
    background: #F3F4F6;
  }
`;

const AvatarBanner = styled.div`
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  color: #fff;
`;

const AvatarCircle = styled.div`
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
`;

const AvatarInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
`;

const AvatarName = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-weight: 600;
  font-size: 13px;
`;

const AvatarSub = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 10px;
  opacity: 0.75;
`;

const LaunchBtn = styled.button`
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-radius: 12px;
  padding: 8px 14px;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  font-family: "PreplyInter", sans-serif;
  flex-shrink: 0;
  transition: all 0.17s ease;

  &:hover {
    filter: brightness(1.15);
    transform: translateY(-1px);
  }
`;

const RichBody = styled.div`
  padding: 18px 20px 22px;
`;

const RichTitle = styled.h3`
  font-family: inherit;
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 6px;
  color: #111827;
`;

const RichObjective = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 12px;
  color: #4B5563;
  line-height: 1.65;
  margin: 0 0 14px;
`;

const PromptBox = styled.div`
  background: #F9F8FF;
  border: 2px solid ${(props) => props.$borderColor || "#dad9de"};
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 16px;
`;

const PromptBoxHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 8px;
`;

const PromptBoxLabel = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  font-weight: 600;
  flex: 1;
`;

const PromptBoxBadge = styled.span`
  font-family: "PreplyInter", sans-serif;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
`;

const PromptBoxText = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  color: #6B7280;
  line-height: 1.65;
  margin: 0;
  font-style: italic;
  white-space: pre-wrap;
`;

const TasksHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
`;

const TasksLabel = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
`;

const TasksCount = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  color: #9CA3AF;
`;

const TasksList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const TaskCard = styled.div`
  display: flex;
  gap: 12px;
  align-items: flex-start;
  border: 2px solid #dad9de;
  border-radius: 12px;
  padding: 11px 14px;
  background: #FAFAFF;
  transition: border-color 0.15s;

  &:hover {
    border-color: #C4B5FD;
  }
`;

const TaskIndex = styled.div`
  width: 20px;
  height: 20px;
  border-radius: 50%;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
`;

const TaskBody = styled.div`
  flex: 1;
`;

const TaskLabel = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  display: block;
  margin-bottom: 3px;
`;

const TaskContent = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  color: #6B7280;
  line-height: 1.65;
  margin: 0;
`;

const TipRow = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 14px;
  padding: 10px 12px;
  background: #FFFBEB;
  border-radius: 12px;
  border: 2px solid #FDE68A;
  color: #92400E;
`;

const TipText = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  color: #92400E;
  line-height: 1.55;
`;

const ReportRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 12px;
  padding: 12px 14px;
  background: #F5F3FF;
  border-radius: 12px;
  border: 2px solid #DDD6FE;
`;

const ReportLeft = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
`;

const ReportTitle = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 12px;
  font-weight: 600;
  color: #5B21B6;
  margin: 0;
`;

const ReportSub = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 10px;
  color: #7C3AED;
  margin: 0;
  opacity: 0.75;
`;

const ReportTags = styled.div`
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  justify-content: flex-end;
`;

const ReportTag = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 9px;
  font-weight: 600;
  padding: 3px 8px;
  background: #EDE9FE;
  color: #5B21B6;
  border-radius: 10px;
`;

const ModalOverlay = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: ${fadeUp} 0.2s ease;
`;

const ModalPanel = styled.div`
  background: #fff;
  border: 2px solid #000;
  border-radius: 12px;
  width: 580px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: none;
`;

const ModalClose = styled.button`
  background: none;
  border: none;
  padding: 6px;
  cursor: pointer;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  transition: all 0.15s;

  &:hover {
    color: #000;
    background: #f3f4f6;
  }
`;

const ReportTrigger = styled.button`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  background: #fafafa;
  border-radius: 12px;
  border: 2px solid #dad9de;
  width: 100%;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease, border-color 0.15s ease;

  &:hover {
    background: #f5f3ff;
    border-color: #c4b5fd;
  }
`;

const ReportModalPanel = styled(ModalPanel)`
  width: min(920px, calc(100vw - 32px));
  max-height: min(88vh, 920px);
`;

const ReportSummary = styled.div`
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
`;

const ReportSummaryCard = styled.div`
  border: 2px solid #dad9de;
  border-radius: 12px;
  padding: 12px 14px;
  background: #fafafa;
`;

const ReportSummaryLabel = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 4px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
`;

const ReportSummaryValue = styled.p`
  font-family: inherit;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
`;

const FoldableSection = styled.section`
  border: 2px solid #dad9de;
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
`;

const FoldableButton = styled.button`
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: none;
  border-bottom: ${(props) => (props.$open ? "2px solid #dad9de" : "none")};
  background: ${(props) => (props.$open ? "#fafafa" : "#fff")};
  cursor: pointer;
  text-align: left;
`;

const FoldableTitle = styled.span`
  font-family: inherit;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
`;

const FoldableMeta = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  color: #9ca3af;
`;

const FoldableContent = styled.div`
  padding: 0;
`;

const ReportTableWrap = styled.div`
  overflow-x: auto;
`;

const ReportTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  min-width: 640px;
`;

const ReportHeadCell = styled.th`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  text-align: left;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #e5e7eb;
`;

const ReportCell = styled.td`
  font-family: "PreplyInter", sans-serif;
  font-size: 12px;
  color: #374151;
  padding: 12px 16px;
  vertical-align: top;
  border-bottom: 1px solid #f3f4f6;
  white-space: pre-wrap;
  line-height: 1.6;
`;

const ReportCellMuted = styled(ReportCell)`
  color: #9ca3af;
`;

const ReportEmptyState = styled.div`
  padding: 20px 16px;
  font-family: "PreplyInter", sans-serif;
  font-size: 12px;
  color: #9ca3af;
`;

const ReportFeedback = styled.div`
  padding: 14px 16px;
  border-radius: 12px;
  border: 2px solid ${(props) => (props.$error ? "#fecaca" : "#ddd6fe")};
  background: ${(props) => (props.$error ? "#fef2f2" : "#f5f3ff")};
  color: ${(props) => (props.$error ? "#991b1b" : "#5b21b6")};
  font-family: "PreplyInter", sans-serif;
  font-size: 12px;
  line-height: 1.6;
`;

const HowCard = styled.section`
  border: 2px solid #dad9de;
  border-radius: 12px;
  padding: 24px;
`;

const HowTitle = styled.p`
  font-family: inherit;
  font-size: 20px;
  font-weight: 700;
  color: #000;
  margin: 0 0 16px;
  letter-spacing: 0.07em;
`;

const HowList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0;
`;

const HowRow = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 12px;
`;

const HowLeft = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
`;

const HowIconWrap = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #000;
`;

const HowLine = styled.div`
  width: 1px;
  height: 14px;
  background: #DDD6FE;
  margin: 2px 0;
`;

const HowText = styled.p`
  font-family: "PreplyInter", sans-serif;
  font-size: 14px;
  line-height: 2;
  margin: 6px 0 14px;
`;

const Skeleton = styled.div`
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const SkeletonLine = styled.div`
  height: 12px;
  background: #f3f4f6;
  border-radius: 6px;
  animation: ${pulse} 1.5s ease-in-out infinite;
  width: ${(props) => props.$width};
`;

const HiddenInput = styled.input`
  display: none;
`;


const Wrapper = styled.div``

function parseTranscriptRows(transcript) {
  return transcript
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const match = line.match(/^(\d+)\.\s+([A-Z]+):\s*(.*)$/);
      if (!match) {
        return {
          id: index + 1,
          line: index + 1,
          speaker: "Note",
          content: line,
        };
      }

      return {
        id: `${match[1]}-${match[2]}`,
        line: Number(match[1]),
        speaker: match[2],
        content: match[3] || "",
      };
    });
}

function parseOverviewRows(analysis) {
  const lines = analysis
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const rows = [];
  let struggleIndex = 1;

  lines.forEach((line, index) => {
    if (line.startsWith("Overall outcome:")) {
      rows.push({ id: `overall-${index}`, label: "Overall outcome", details: line.replace("Overall outcome:", "").trim() });
      return;
    }

    if (line.startsWith("Strengths:")) {
      rows.push({ id: `strengths-${index}`, label: "Strengths", details: line.replace("Strengths:", "").trim() });
      return;
    }

    if (line.startsWith("Recommended follow-up:")) {
      rows.push({ id: `follow-up-${index}`, label: "Recommended follow-up", details: line.replace("Recommended follow-up:", "").trim() });
      return;
    }

    if (line.startsWith("- ")) {
      rows.push({ id: `struggle-${index}`, label: `Struggle ${struggleIndex}`, details: line.replace(/^-+\s*/, "").trim() });
      struggleIndex += 1;
      return;
    }

    rows.push({ id: `note-${index}`, label: "Notes", details: line });
  });

  return rows;
}

function stringifyReportValue(value) {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? String(value) : "n/a";
  }

  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function buildStudentAnalysisRows(studentAnalysis) {
  const rows = [
    {
      id: "confidence",
      metric: "Confidence score",
      value: studentAnalysis?.confidence_score ?? 0,
      notes: "Final Helios confidence score.",
    },
    {
      id: "fluency",
      metric: "Fluency score",
      value: studentAnalysis?.fluency_score ?? 0,
      notes: "Final Helios fluency score.",
    },
    {
      id: "turn-count",
      metric: "Analyzed turns",
      value: Array.isArray(studentAnalysis?.raw_turns) ? studentAnalysis.raw_turns.length : 0,
      notes: "Number of biomarker result payloads stored for the session.",
    },
  ];

  if (Array.isArray(studentAnalysis?.raw_turns)) {
    studentAnalysis.raw_turns.forEach((turn, index) => {
      const scores = turn && typeof turn === "object" && !Array.isArray(turn) ? turn.scores : undefined;
      rows.push({
        id: `turn-${index + 1}`,
        metric: `Turn ${index + 1}`,
        value: stringifyReportValue(scores && Object.keys(scores).length ? scores : turn),
        notes: "Raw Thymia payload snapshot.",
      });
    });
  }

  return rows;
}

/* -- component -- */
export default function PreplyTeacherDashboard() {
  const [selectedType, setSelectedType] = useState("speaking");
  const [prompt, setPrompt] = useState(DEMO_PROMPT);
  const [files, setFiles] = useState([DEMO_FILE]);
  const [isDragging, setIsDragging] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generated, setGenerated] = useState(null);
  const [chatId, setChatId] = useState(null);
  const [generationWarnings, setGenerationWarnings] = useState([]);
  const [copied, setCopied] = useState(false);
  const [launchCopied, setLaunchCopied] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimized, setOptimized] = useState(false);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [isReportLoading, setIsReportLoading] = useState(false);
  const [reportError, setReportError] = useState("");
  const [reportData, setReportData] = useState(null);
  const [openSections, setOpenSections] = useState({
    transcript: true,
    overview: true,
    studentAnalysis: true,
  });
  const fileInputRef = useRef(null);

  const selectType = (id) => {
    setSelectedType(id);
    setGenerated(null);
  };

  const handleFiles = (incoming) => {
    const arr = Array.from(incoming);
    setFiles((prev) => [
      ...prev,
      ...arr.map((f) => ({ file: f, id: Math.random().toString(36).slice(2) })),
    ]);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, []);

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const onDragLeave = () => setIsDragging(false);

  const removeFile = (id) => setFiles((prev) => prev.filter((f) => f.id !== id));

  const getFileIcon = (name) => {
    if (name.endsWith(".pdf")) return <FileText size={16} />;
    if (name.match(/\.(jpg|jpeg|png)$/i)) return <ImageIcon size={16} />;
    return <FilePen size={16} />;
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  };

  const activeType = ASSIGNMENT_TYPES.find((t) => t.id === selectedType);
  const canGenerate = prompt.trim().length > 0;
  const canOptimize = prompt.trim().length > 10 && !isOptimizing && !isGenerating;

  const handleOptimize = async () => {
    if (!canOptimize) return;
    setIsOptimizing(true);
    setOptimized(false);
    try {
      const response = await fetch("/api/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await response.json();
      if (data.improved) {
        setPrompt(data.improved);
        setOptimized(true);
        setTimeout(() => setOptimized(false), 3000);
      }
    } catch (err) {
      // fail silently, keep original prompt
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleGenerate = async () => {
  if (!canGenerate) return;
  setIsGenerating(true);
  setGenerated(null);
  setChatId(null);
  setGenerationWarnings([]);

  try {
    const backendMode = MODE_MAP[selectedType];
    const apiBase = getApiBaseUrl();
    const topic = prompt.split(".")[0].trim().slice(0, 120) || prompt.slice(0, 80).trim();

    // Parse a real uploaded file if one exists
    let worksheetJson = null;
    const realFile = files.find((f) => f.file instanceof File);
    if (realFile) {
      const formData = new FormData();
      formData.append("file", realFile.file);
      const parseRes = await fetch(`${apiBase}/api/worksheet/parse`, {
        method: "POST",
        body: formData,
      });
      if (parseRes.ok) {
        const parseData = await parseRes.json();
        worksheetJson = parseData.worksheet_json ?? null;
      }
    }

    // No real file — build a minimal worksheet from teacher notes so the backend accepts it
    if (!worksheetJson || Object.keys(worksheetJson).length === 0) {
      worksheetJson = {
        title: topic,
        topic,
        worksheet_type: "Teacher Notes",
        level: "unknown",
        instructions: [prompt],
        sections: [],
        answer_key: [],
        notes: [prompt],
        raw_text: prompt,
      };
    }

    const response = await fetch(`${apiBase}/api/exercises/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        teacher_notes: prompt,
        topic,
        worksheet_json: worksheetJson,
        mode: backendMode,
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail ?? `Generate failed (${response.status})`);
    }

    const data = await response.json();
    setGenerationWarnings(Array.isArray(data.warnings) ? data.warnings : []);

    const avatarPrompt = data.avatar_prompts?.[backendMode] ?? "";
    const rawTasks = data.tasks?.[backendMode] ?? [];
    const returnedChatId = data.chat_ids?.[backendMode] ?? null;

    const nameMatch = avatarPrompt.match(/^You are ([A-Z][a-z]+)/);
    const avatarName = nameMatch ? nameMatch[1] : activeType?.label ?? "Mirror";

    setChatId(returnedChatId);
    setGenerated({
      title: `${activeType?.label ?? "Session"}: ${data.topic}`,
      objective: activeType?.mechanic ?? "",
      avatar_name: avatarName,
      avatar_prompt: avatarPrompt,
      tasks: rawTasks.map((t) => ({ label: t.title, content: t.description })),
      tip: activeType?.tip ?? "",
    });
  } catch (err) {
    alert(err instanceof Error ? err.message : "Generation failed. Check the backend is running.");
  } finally {
    setIsGenerating(false);
  }
};



  const handleCopy = () => {
    if (!generated) return;
    const text = `${generated.title}\n\nObjective: ${generated.objective}\n\nAvatar Prompt:\n${generated.avatar_prompt}\n\nTasks:\n${generated.tasks.map((t, i) => `${i + 1}. ${t.label}: ${t.content}`).join("\n")}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLaunchSession = async () => {
    if (!chatId) return;
    const launchLink = `${getAppBaseUrl()}/chat/${chatId}`;
    window.open(launchLink, "_blank");
    try {
      await navigator.clipboard.writeText(launchLink);
      setLaunchCopied(true);
      setTimeout(() => setLaunchCopied(false), 2000);
    } catch (err) {
      // clipboard may be unavailable
    }
  };

  const toggleSection = (section) => {
    setOpenSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleOpenReport = async () => {
    if (!chatId) return;
    setIsReportOpen(true);
    setIsReportLoading(true);
    setReportError("");

    try {
      const report = await getTeacherReport(chatId);
      setReportData(report);
    } catch (err) {
      setReportData(null);
      setReportError(err instanceof Error ? err.message : "Unable to load report.");
    } finally {
      setIsReportLoading(false);
    }
  };

  const handleCloseReport = () => {
    setIsReportOpen(false);
  };

  const transcriptRows = reportData ? parseTranscriptRows(reportData.transcript) : [];
  const overviewRows = reportData ? parseOverviewRows(reportData.homework_analysis) : [];
  const studentAnalysisRows = reportData ? buildStudentAnalysisRows(reportData.student_analysis) : [];

  return (
    <Page>

      <Wrapper>
        <Container>
          <Header>
            <TitleRow>
              <BackButton><ArrowLeft size={20} /></BackButton>
              <Title>Create Assignment</Title>
            </TitleRow>
            <Subtitle>Upload materials, describe your goal, and let AI build it for your student.</Subtitle>
          </Header>

          <Grid>
            {/* SIDEBAR - Assignment types */}
            <Sidebar>
              {ASSIGNMENT_TYPES.map((type) => {
                const active = selectedType === type.id;
                return (
                  <SidebarItem
                    key={type.id}
                    $active={active}
                    $bg={type.bg}
                    $color={type.color}
                    onClick={() => selectType(type.id)}
                  >
                    <type.icon size={18} />
                    {type.label}
                  </SidebarItem>
                );
              })}
            </Sidebar>

            {/* MAIN CONTENT */}
            <MainCol>
              <SectionTitle>
                {activeType?.label ?? "Select an assignment type"}
                <CardDesc style={{letterSpacing: '0.02em'}}>Powered by Anam AI</CardDesc>
              </SectionTitle>

              {/* Mechanic description */}
              {activeType && (
                <MechanicBox key={selectedType}>
                  <activeType.icon size={24} style={{ flexShrink: 0, color: '#000' }} />
                  <MechanicText>
                    <strong>{activeType.mechanicLabel} </strong>
                    {activeType.mechanic}
                  </MechanicText>
                </MechanicBox>
              )}

              {/* Upload */}
              <Card>
                <CardHeader>
                  <CardStep>1</CardStep>
                  <div>
                    <CardTitle>Upload your worksheet</CardTitle>
                    <CardDesc>PDF, JPEG, DOCX files supported</CardDesc>
                  </div>
                </CardHeader>

                <Dropzone
                  $dragging={isDragging}
                  onDrop={onDrop}
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <HiddenInput
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept={ACCEPT_TYPES}
                    onChange={(e) => handleFiles(e.target.files)}
                  />
                  <DropzoneIcon><FolderOpen size={32} /></DropzoneIcon>
                  <DropzoneText>
                    {isDragging ? "Drop files here" : "Drag & drop or click to browse"}
                  </DropzoneText>
                  <DropzoneHint>PDF, JPEG, DOCX</DropzoneHint>
                </Dropzone>

                {files.length > 0 && (
                  <FileList>
                    {files.map(({ file, id }) => (
                      <FileItem key={id}>
                        <FileIcon>{getFileIcon(file.name)}</FileIcon>
                        <FileName>{file.name}</FileName>
                        <FileSize>{formatSize(file.size)}</FileSize>
                        <RemoveBtn onClick={() => removeFile(id)}><X size={14} /></RemoveBtn>
                      </FileItem>
                    ))}
                  </FileList>
                )}
              </Card>

              {/* Prompt */}
              <Card>
                <CardHeader>
                  <CardStep>2</CardStep>
                  <div>
                    <CardTitle>What is the assignment goal?</CardTitle>
                    <CardDesc>Describe the goal for this assignment below</CardDesc>
                  </div>
                </CardHeader>
                <Textarea
                  placeholder="e.g. Create 5 fill-in-the-blank sentences using vocabulary from the worksheet, targeting B1 level..."
                  value={prompt}
                  onChange={(e) => { setPrompt(e.target.value); setOptimized(false); }}
                  rows={5}
                  style={optimized ? { borderColor: "#059669" } : undefined}
                />
                <PromptFooter>
                  <CharCount>{prompt.length} / 500</CharCount>
                  <OptimizeBtn disabled={!canOptimize} onClick={handleOptimize}>
                    {isOptimizing ? (
                      <SpinnerWrap><OptSpinner /> Optimizing...</SpinnerWrap>
                    ) : optimized ? (
                      <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                        <Check size={16} /> Done!
                      </span>
                    ) : (
                      <>
                        <RefreshCw size={16} />
                        Optimize prompt
                      </>
                    )}
                  </OptimizeBtn>
                </PromptFooter>
              </Card>

              {/* How it works */}
              <HowCard>
                <HowTitle>How it works</HowTitle>
                <HowList>
                  {HOW_STEPS.map((item, i) => (
                    <HowRow key={i}>
                      <HowLeft>
                        <HowIconWrap style={{
                          background: i === HOW_STEPS.length - 1 ? "#ff7aac" : "#fff"
                        }}>
                          <item.icon size={20} />
                        </HowIconWrap>
                        {i < HOW_STEPS.length - 1 && <HowLine />}
                      </HowLeft>
                      <HowText style={{
                        fontWeight: i === HOW_STEPS.length - 1 ? 600 : 400,
                        color: i === HOW_STEPS.length - 1 ? "#000" : "#4B5563",
                      }}>{item.text}</HowText>
                    </HowRow>
                  ))}
                </HowList>
              </HowCard>

              {/* Generate */}
              <GenerateBtn
                $canGenerate={canGenerate}
                disabled={!canGenerate || isGenerating}
                onClick={handleGenerate}
              >
                {isGenerating ? (
                  <SpinnerWrap><Spinner /> Building avatar session...</SpinnerWrap>
                ) : (
                  <SpinnerWrap><FileSpreadsheet size={20} /> Generate {activeType?.label ?? "Assignment"}</SpinnerWrap>
                )}
              </GenerateBtn>

              {!canGenerate && (
                <GenerateHint>
                  Add a teacher prompt to continue
                </GenerateHint>
              )}

            </MainCol>
          </Grid>
        </Container>
      </Wrapper>

      {/* Output modal */}
      {generated && (
        <ModalOverlay onClick={() => setGenerated(null)}>
          <ModalPanel onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "20px 24px", borderBottom: "2px solid rgba(0,0,0,.08)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <activeType.icon size={18} style={{ color: "#000" }} />
                <span style={{ fontFamily: "inherit", fontSize: 15, fontWeight: 600, letterSpacing: "0.04em", color: "#000" }}>Avatar Session</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <CopyBtn onClick={handleCopy}>
                  {copied ? "Copied!" : "Copy prompt"}
                </CopyBtn>
                <ModalClose onClick={() => setGenerated(null)}>
                  <X size={18} />
                </ModalClose>
              </div>
            </div>

            {/* Avatar banner */}
            <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 24px", background: "#fff7c1", borderBottom: "2px solid rgba(0,0,0,.08)" }}>
              <div style={{ width: 40, height: 40, borderRadius: "50%", background: "#000", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", flexShrink: 0 }}>
                <activeType.icon size={18} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: "inherit", fontSize: 14, fontWeight: 600, color: "#000", letterSpacing: "0.02em" }}>{generated.avatar_name} — AI {activeType?.avatarRole}</div>
                <div style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 12, color: "#4B5563", marginTop: 1 }}>Live voice + text chat · {activeType?.sublabel}</div>
                {launchCopied && (
                  <div style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 12, fontWeight: 600, color: "#059669", marginTop: 6 }}>
                    Copied link to clipboard
                  </div>
                )}
              </div>
              <LaunchBtn onClick={handleLaunchSession} style={{ background: "#ff7aac", border: "2px solid #000", color: "#000", borderRadius: 12, padding: "8px 16px", fontSize: 12 }}>Launch Session</LaunchBtn>
            </div>

            {/* Body */}
            <div style={{ padding: "24px" }}>
              <h3 style={{ fontFamily: "inherit", fontSize: 18, fontWeight: 500, letterSpacing: "0.04em", margin: "0 0 6px", color: "#000" }}>{generated.title}</h3>
              {generationWarnings.length > 0 && (
                <div style={{
                  background: "#fff7c1",
                  border: "2px solid #000",
                  borderRadius: 12,
                  padding: "10px 12px",
                  margin: "0 0 16px",
                  fontFamily: "'PreplyInter', sans-serif",
                  fontSize: 12,
                  color: "#000",
                  lineHeight: 1.5,
                }}>
                  {generationWarnings.map((warning, index) => (
                    <div key={index}>{warning}</div>
                  ))}
                </div>
              )}
              <p style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 13, color: "#4B5563", lineHeight: 1.65, margin: "0 0 20px" }}><strong style={{ color: "#000" }}>Objective:</strong> {generated.objective}</p>

              {/* System prompt box */}
              <div style={{ background: "#FAFAFA", border: "2px solid #dad9de", borderRadius: 12, padding: "14px 16px", marginBottom: 20 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8 }}>
                  <Sparkles size={14} style={{ color: "#000" }} />
                  <span style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 12, fontWeight: 600, color: "#000", flex: 1 }}>Avatar System Prompt</span>
                  <span style={{ fontFamily: "'PreplyInter', sans-serif", color: "#000", fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 10, background: "#ff7aac" }}>Sent to Anam</span>
                </div>
                <p style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 12, color: "#4B5563", lineHeight: 1.65, margin: 0, fontStyle: "italic", whiteSpace: "pre-wrap" }}>{generated.avatar_prompt}</p>
              </div>

              {/* Tasks */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                <span style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 13, fontWeight: 600, color: "#000" }}>Student Tasks</span>
                <span style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 12, color: "#9ca3af" }}>{generated.tasks.length} activities</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
                {generated.tasks.map((task, i) => (
                  <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start", border: "2px solid #dad9de", borderRadius: 12, padding: "11px 14px", background: "#fff" }}>
                    <div style={{ width: 20, height: 20, borderRadius: "50%", background: "#000", color: "#fff", fontSize: 9, fontWeight: 700, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", marginTop: 1 }}>{i + 1}</div>
                    <div style={{ flex: 1 }}>
                      <span style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 13, fontWeight: 600, color: "#000", display: "block", marginBottom: 3 }}>{task.label}</span>
                      <p style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 12, color: "#4B5563", lineHeight: 1.65, margin: 0 }}>{task.content}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Tip */}
              <div style={{ display: "flex", alignItems: "flex-start", gap: 8, padding: "10px 12px", background: "#fff7c1", borderRadius: 12, border: "2px solid #000", marginBottom: 12 }}>
                <Lightbulb size={14} style={{ flexShrink: 0, marginTop: 1, color: "#000" }} />
                <span style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 12, color: "#000", lineHeight: 1.55 }}>{generated.tip}</span>
              </div>

              {/* Lesson report */}
              <ReportTrigger onClick={handleOpenReport}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <FileSpreadsheet size={18} style={{ color: "#000" }} />
                  <div>
                    <p style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 13, fontWeight: 600, color: "#000", margin: 0 }}>Lesson Report</p>
                    <p style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 11, color: "#9ca3af", margin: 0 }}>Click here to see how your student did</p>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 5, flexWrap: "wrap", justifyContent: "flex-end" }}>
                  {["Errors flagged", "Words used", "Tasks completed"].map((tag) => (
                    <span key={tag} style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 9, fontWeight: 600, padding: "3px 8px", background: "rgba(0,0,0,.05)", color: "#000", borderRadius: 10 }}>{tag}</span>
                  ))}
                </div>
              </ReportTrigger>
            </div>
          </ModalPanel>
        </ModalOverlay>
      )}
      {generated && isReportOpen && (
        <ModalOverlay onClick={handleCloseReport}>
          <ReportModalPanel onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: "20px 24px", borderBottom: "1px solid #f3f4f6", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
              <div>
                <h3 style={{ fontFamily: "inherit", fontSize: 20, fontWeight: 500, letterSpacing: "0.04em", color: "#000", margin: 0 }}>Lesson Report</h3>
                <p style={{ fontFamily: "'PreplyInter', sans-serif", fontSize: 12, color: "#9ca3af", margin: "4px 0 0" }}>Transcript, overview, and student analysis for this session.</p>
              </div>
              <ModalClose onClick={handleCloseReport}><X size={18} /></ModalClose>
            </div>

            <div style={{ padding: "20px 24px 24px", display: "flex", flexDirection: "column", gap: 16 }}>
              {isReportLoading && (
                <ReportFeedback>
                  <SpinnerWrap><Spinner /> Loading report...</SpinnerWrap>
                </ReportFeedback>
              )}

              {!isReportLoading && reportError && (
                <ReportFeedback $error>{reportError}</ReportFeedback>
              )}

              {!isReportLoading && reportData && (
                <>
                  <ReportSummary>
                    <ReportSummaryCard>
                      <ReportSummaryLabel>Chat ID</ReportSummaryLabel>
                      <ReportSummaryValue style={{ fontSize: 14, lineHeight: 1.45 }}>{reportData.chat_id}</ReportSummaryValue>
                    </ReportSummaryCard>
                    <ReportSummaryCard>
                      <ReportSummaryLabel>Confidence</ReportSummaryLabel>
                      <ReportSummaryValue>{reportData.student_analysis.confidence_score.toFixed(3)}</ReportSummaryValue>
                    </ReportSummaryCard>
                    <ReportSummaryCard>
                      <ReportSummaryLabel>Fluency</ReportSummaryLabel>
                      <ReportSummaryValue>{reportData.student_analysis.fluency_score.toFixed(3)}</ReportSummaryValue>
                    </ReportSummaryCard>
                  </ReportSummary>

                  <FoldableSection>
                    <FoldableButton $open={openSections.transcript} onClick={() => toggleSection("transcript")}>
                      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        <FoldableTitle>Transcript</FoldableTitle>
                        <FoldableMeta>{transcriptRows.length} rows</FoldableMeta>
                      </div>
                      {openSections.transcript ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </FoldableButton>
                    {openSections.transcript && (
                      <FoldableContent>
                        {transcriptRows.length ? (
                          <ReportTableWrap>
                            <ReportTable>
                              <thead>
                                <tr>
                                  <ReportHeadCell>Line</ReportHeadCell>
                                  <ReportHeadCell>Speaker</ReportHeadCell>
                                  <ReportHeadCell>Content</ReportHeadCell>
                                </tr>
                              </thead>
                              <tbody>
                                {transcriptRows.map((row) => (
                                  <tr key={row.id}>
                                    <ReportCellMuted>{row.line}</ReportCellMuted>
                                    <ReportCell>{row.speaker}</ReportCell>
                                    <ReportCell>{row.content || "n/a"}</ReportCell>
                                  </tr>
                                ))}
                              </tbody>
                            </ReportTable>
                          </ReportTableWrap>
                        ) : (
                          <ReportEmptyState>No transcript saved for this session.</ReportEmptyState>
                        )}
                      </FoldableContent>
                    )}
                  </FoldableSection>

                  <FoldableSection>
                    <FoldableButton $open={openSections.overview} onClick={() => toggleSection("overview")}>
                      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        <FoldableTitle>Overview</FoldableTitle>
                        <FoldableMeta>{overviewRows.length} rows</FoldableMeta>
                      </div>
                      {openSections.overview ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </FoldableButton>
                    {openSections.overview && (
                      <FoldableContent>
                        {overviewRows.length ? (
                          <ReportTableWrap>
                            <ReportTable>
                              <thead>
                                <tr>
                                  <ReportHeadCell>Category</ReportHeadCell>
                                  <ReportHeadCell>Details</ReportHeadCell>
                                </tr>
                              </thead>
                              <tbody>
                                {overviewRows.map((row) => (
                                  <tr key={row.id}>
                                    <ReportCell>{row.label}</ReportCell>
                                    <ReportCell>{row.details || "n/a"}</ReportCell>
                                  </tr>
                                ))}
                              </tbody>
                            </ReportTable>
                          </ReportTableWrap>
                        ) : (
                          <ReportEmptyState>No homework analysis saved for this session.</ReportEmptyState>
                        )}
                      </FoldableContent>
                    )}
                  </FoldableSection>

                  <FoldableSection>
                    <FoldableButton $open={openSections.studentAnalysis} onClick={() => toggleSection("studentAnalysis")}>
                      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                        <FoldableTitle>Student Analysis</FoldableTitle>
                        <FoldableMeta>{studentAnalysisRows.length} rows</FoldableMeta>
                      </div>
                      {openSections.studentAnalysis ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </FoldableButton>
                    {openSections.studentAnalysis && (
                      <FoldableContent>
                        {studentAnalysisRows.length ? (
                          <ReportTableWrap>
                            <ReportTable>
                              <thead>
                                <tr>
                                  <ReportHeadCell>Metric</ReportHeadCell>
                                  <ReportHeadCell>Value</ReportHeadCell>
                                  <ReportHeadCell>Notes</ReportHeadCell>
                                </tr>
                              </thead>
                              <tbody>
                                {studentAnalysisRows.map((row) => (
                                  <tr key={row.id}>
                                    <ReportCell>{row.metric}</ReportCell>
                                    <ReportCell>{stringifyReportValue(row.value)}</ReportCell>
                                    <ReportCell>{row.notes}</ReportCell>
                                  </tr>
                                ))}
                              </tbody>
                            </ReportTable>
                          </ReportTableWrap>
                        ) : (
                          <ReportEmptyState>No student analysis saved for this session.</ReportEmptyState>
                        )}
                      </FoldableContent>
                    )}
                  </FoldableSection>
                </>
              )}
            </div>
          </ReportModalPanel>
        </ModalOverlay>
      )}
    </Page>
  );
}
