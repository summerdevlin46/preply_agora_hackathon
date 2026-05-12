"use client";

import { useState, useRef, useCallback, useEffect } from "react";


// All four modes work within Anam's actual capabilities:
// - Avatar speaks and listens in live turns (no mid-turn interruption)
// - Student can also type in a text chat alongside the voice session
// - Avatar cannot present images or visual materials
// - Avatar drives the exercise through conversation, prompts, and questions

const ASSIGNMENT_TYPES = [
  {
    id: "speaking",
    label: "Avatar Conversation",
    sublabel: "Fluency & Turn-Taking",
    icon: "🎙️",
    color: "#7C3AED",
    bg: "#F5F3FF",
    border: "#DDD6FE",
    avatarRole: "Conversational partner",
    avatarVerb: "speaks with",
    mechanic: "The avatar leads a structured spoken conversation on the lesson topic. It asks open questions, waits for the student's full response, then replies with natural follow-ups and gentle corrections — all within real back-and-forth turns.",
  },
  {
    id: "vocab",
    label: "Vocabulary Challenge",
    sublabel: "Spoken Word Production",
    icon: "🃏",
    color: "#0891B2",
    bg: "#ECFEFF",
    border: "#A5F3FC",
    avatarRole: "Vocabulary coach",
    avatarVerb: "quizzes",
    mechanic: "The avatar verbally describes or gives definitions of lesson vocabulary and waits for the student to say the target word aloud and use it in a sentence. Students can also type words in the chat if unsure, and the avatar responds with spoken confirmation or correction.",
  },
  {
    id: "writing",
    label: "Dictation & Feedback",
    sublabel: "Writing + Spoken Review",
    icon: "✍️",
    color: "#059669",
    bg: "#ECFDF5",
    border: "#A7F3D0",
    avatarRole: "Writing coach",
    avatarVerb: "coaches",
    mechanic: "The avatar dictates sentences using lesson vocabulary for the student to type into the chat. After each one, it gives spoken feedback on spelling and grammar, then moves on. At the end, it summarises patterns in the student's errors.",
  },
  {
    id: "grammar",
    label: "Error Detective",
    sublabel: "Form-Focused Grammar",
    icon: "🔍",
    color: "#D97706",
    bg: "#FFFBEB",
    border: "#FDE68A",
    avatarRole: "Grammar coach",
    avatarVerb: "coaches",
    mechanic: "The avatar reads sentences aloud that contain deliberate grammar errors. The student must respond — by voice or chat — with the corrected sentence. The avatar then asks the student to explain the rule before confirming it and moving on.",
  },
];

const ACCEPT_TYPES = ".pdf,.jpg,.jpeg,.png,.docx,.doc";

const DEMO_OUTPUTS = {
  speaking: {
    title: "🍳 Kitchen Chat: Present Continuous Conversation",
    objective: "Student practises present continuous fluency through a structured back-and-forth conversation with Sofia about cooking actions.",
    avatar_name: "Sofia",
    avatar_emoji: "🧑‍🍳",
    avatar_prompt: `You are Sofia, a warm and encouraging cooking show host conducting a spoken conversation with a B1 English student. Your goal is to practise the present continuous tense through natural dialogue about cooking.

Structure the session in three turns:
1. Ask the student what they are doing right now in the kitchen — wait for their full response before reacting.
2. Ask them to describe the steps of making their favourite dish one by one, responding naturally between each step.
3. Ask them a follow-up opinion question about cooking (e.g. "Which do you prefer — baking or frying? What are you thinking about making this weekend?").

After each student turn: acknowledge what they said, correct any present continuous errors naturally in your reply (model the correct form, do not just say "wrong"), and ask the next question. Vocabulary to reinforce: fry, bake, boil, whisk, chop, grill, pour, mix; utensils: pan, pot, spatula, cutting board.`,
    tasks: [
      { icon: "💬", label: "Opening Question", content: "Sofia opens by asking what you are doing in the kitchen right now. Answer in full present continuous sentences — describe what you're cooking step by step." },
      { icon: "🍝", label: "Dish Description", content: "Sofia asks you to describe making your favourite dish. Talk through the steps conversationally, using present continuous: \"First I am chopping the onion, now I am frying it…\"" },
      { icon: "🗣️", label: "Opinion Follow-Up", content: "Sofia asks a broader question about your cooking habits. Answer naturally in conversation — she'll pick up on any tense errors and weave corrections into her reply." },
    ],
    tip: "Sofia waits for your complete answer before speaking. Take your time — there's no need to rush or interrupt.",
  },
  vocab: {
    title: "🃏 Cooking Vocabulary: Spoken Word Challenge",
    objective: "Student retrieves and produces cooking vocabulary aloud by responding to verbal definitions and using target words in full sentences.",
    avatar_name: "Max",
    avatar_emoji: "🎤",
    avatar_prompt: `You are Max, an encouraging vocabulary coach working with a B1 English student on cooking vocabulary. You will run a spoken word challenge — no images or visual cues, everything is verbal.

For each word, follow this pattern:
1. Give a clear verbal description or definition of the target word (e.g. "This is a flat tool you use to flip food in a frying pan — what is it called?")
2. Wait for the student to say the word aloud OR type it in the chat.
3. If correct: confirm enthusiastically, then ask them to use it in a present continuous sentence (e.g. "Great! Now use it in a sentence — what is the chef doing?")
4. If incorrect or unsure: say the word clearly, explain it again briefly, then move to the next.

Run through these words in order: spatula, whisk, chopping board, kettle, pan, pot — then these verbs: fry, bake, boil, chop, grill, pour, mix. After all words, briefly recap any the student missed.`,
    tasks: [
      { icon: "👂", label: "Listen & Respond", content: "Max describes each word or utensil out loud. Say the word aloud when you know it — or type it in the chat if you prefer. No guessing pressure: Max will tell you if you're stuck." },
      { icon: "🗣️", label: "Use It in a Sentence", content: "After each correct answer, Max asks you to use the word in a present continuous sentence. Speak naturally — Max responds to what you say before moving on." },
      { icon: "🔁", label: "Missed Words Recap", content: "At the end, Max revisits any words you hesitated on. Listen to his description again and try once more." },
    ],
    tip: "Max won't show you anything visual — all clues are spoken. You can also type a word in the chat if you're unsure how to pronounce it.",
  },
  writing: {
    title: "✍️ Cooking Dictation & Spoken Feedback",
    objective: "Student types sentences dictated by the avatar, practising spelling and grammar, then receives spoken feedback on patterns of error.",
    avatar_name: "Priya",
    avatar_emoji: "📋",
    avatar_prompt: `You are Priya, a patient and precise writing coach working with a B1 English student. You will run a spoken dictation exercise using present continuous sentences about cooking.

For each sentence:
1. Read the sentence clearly and at natural speed (e.g. "She is whisking the cake batter in a large bowl.")
2. Tell the student to type what they heard into the chat.
3. Wait for their typed response.
4. Give brief spoken feedback: confirm if correct, or point out the specific spelling or grammar error and say the correct version.
5. Move to the next sentence.

Use 6 dictation sentences that combine lesson vocabulary (fry, bake, boil, whisk, chop, grill, pour, mix) with utensils (pan, pot, spatula, cutting board) in present continuous form. After all 6, give a spoken summary of any patterns you noticed — e.g. spelling errors, missing -ing, wrong verb form.`,
    tasks: [
      { icon: "✏️", label: "Type What You Hear", content: "Priya reads a sentence aloud at natural pace. Type exactly what you hear into the chat. Don't worry about perfection — Priya gives feedback after each one." },
      { icon: "🔊", label: "Listen for Corrections", content: "After you type, Priya speaks her feedback. If you made an error, she says the correct version. Listen carefully before she moves to the next sentence." },
      { icon: "📊", label: "Error Pattern Summary", content: "After 6 sentences, Priya gives a spoken summary of patterns in your errors — e.g. missing -ing, spelling of irregular verbs. Note down anything to review." },
    ],
    tip: "Type into the chat exactly what you hear — don't edit as you go. Priya will give spoken corrections after each sentence.",
  },
  grammar: {
    title: "🔍 Error Detective: Present Continuous",
    objective: "Student listens to sentences with deliberate grammar errors, responds with the correction by voice or chat, then explains the rule.",
    avatar_name: "Leo",
    avatar_emoji: "🕵️",
    avatar_prompt: `You are Leo, a sharp and encouraging grammar coach working with a B1 English student. You will read sentences aloud that contain deliberate present continuous errors.

For each sentence:
1. Read the sentence clearly — do not signal that it contains an error.
2. Say: "Does that sound right to you?"
3. Wait for the student to respond by voice or to type their correction in the chat.
4. If they identify the error: ask them to explain the rule — "Why is that wrong — what's the grammar rule?"
5. Confirm the rule or gently clarify if their explanation is incomplete.
6. Say the corrected sentence clearly before moving on.

Use these error types across 6 sentences: missing 'be' verb ("She mixing the batter"), wrong be-form ("They is grilling the vegetables"), missing -ing ("He is fry the onion"), and incorrect word order. After all 6, give a score and briefly summarise any rules they struggled with.`,
    tasks: [
      { icon: "👂", label: "Does That Sound Right?", content: "Leo reads a sentence aloud and asks if it sounds correct. Respond by voice — say \"yes\" or say the corrected version in full. You can also type your correction in the chat." },
      { icon: "📖", label: "Explain the Rule", content: "When you spot an error, Leo asks you to explain why it's wrong. Say the grammar rule out loud in your own words — e.g. \"The verb 'be' has to match the subject.\"" },
      { icon: "🏆", label: "Score & Summary", content: "After 6 sentences, Leo tells you your score and talks through any rules you found tricky. Listen to his summary and ask follow-up questions if anything is unclear." },
    ],
    tip: "Leo reads the full sentence first without signalling the error. Listen to the whole thing before deciding if it sounds right — just like you would in real life.",
  },
};

export default function PreplyAssignmentCreator() {
  const [selectedType, setSelectedType] = useState("speaking");
  const [prompt, setPrompt] = useState("");
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generated, setGenerated] = useState(null);
  const [copied, setCopied] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimized, setOptimized] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    setFiles([{ file: { name: "SV-Cooking-Present-Continuous.pdf", size: 812400 }, id: "demo-file" }]);
    setPrompt("Student practised present continuous using a cooking-themed worksheet. They know vocabulary: fry, bake, boil, whisk, chop, grill, pour, mix, pan, pot, spatula, cutting board. Level B1.");
  }, []);

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
    if (name.endsWith(".pdf")) return "📕";
    if (name.match(/\.(jpg|jpeg|png)$/i)) return "🖼️";
    return "📝";
  };
  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  };

  const canGenerate = selectedType && prompt.trim().length > 0;
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
      const improved = data.improved?.trim();
      if (improved) {
        setPrompt(improved);
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
    await new Promise(r => setTimeout(r, 2000));
    setGenerated(DEMO_OUTPUTS[selectedType]);
    setIsGenerating(false);
  };

  const activeType = ASSIGNMENT_TYPES.find(t => t.id === selectedType);
  const demo = generated;

  const handleCopy = () => {
    if (!demo) return;
    const text = `${demo.title}\n\nObjective: ${demo.objective}\n\nAvatar Prompt:\n${demo.avatar_prompt}\n\nTasks:\n${demo.tasks.map((t, i) => `${i + 1}. ${t.label}: ${t.content}`).join("\n")}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const HOW_STEPS = [
    { icon: "📄", text: "Worksheet & lesson context sent to Claude" },
    { icon: "🤖", text: "Tailored avatar prompt is generated per mode" },
    { icon: "🎙️", text: "Student launches a live Anam AI session" },
    { icon: "✅", text: "Avatar guides the exercise with spoken feedback" },
    { icon: "📊", text: "Lesson report sent back to the teacher" },
  ];

  return (
    <div style={S.page}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=Lora:ital,wght@0,600;1,600&display=swap');
        * { box-sizing: border-box; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
        @keyframes shimmer { 0%{background-position:-500px 0} 100%{background-position:500px 0} }
        @keyframes glow { 0%,100%{box-shadow:0 0 0 0 rgba(124,58,237,0.3)} 50%{box-shadow:0 0 0 10px rgba(124,58,237,0);} }
        @keyframes slideIn { from{opacity:0;transform:translateX(-8px)} to{opacity:1;transform:translateX(0)} }
        @keyframes optimizedPop { 0%{opacity:0;transform:scale(0.92)} 60%{transform:scale(1.03)} 100%{opacity:1;transform:scale(1)} }
        .type-btn { transition: all 0.17s ease !important; }
        .type-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1) !important; }
        .gen-btn { transition: all 0.18s ease !important; }
        .gen-btn:hover:not(:disabled) { filter: brightness(1.1); transform: translateY(-1px); box-shadow: 0 8px 24px rgba(0,0,0,0.2) !important; }
        .launch-btn { transition: all 0.17s ease !important; }
        .launch-btn:hover { filter: brightness(1.15); transform: translateY(-1px); }
        .copy-btn:hover { background: #F3F4F6 !important; }
        .remove-btn:hover { color: #EF4444 !important; }
        .task-card { transition: border-color 0.15s !important; }
        .task-card:hover { border-color: #C4B5FD !important; }
        textarea:focus { border-color: #7C3AED !important; box-shadow: 0 0 0 3px rgba(124,58,237,0.1) !important; outline: none; }
        .dropzone:hover { border-color: #A78BFA !important; }
        .opt-btn { transition: all 0.17s ease !important; }
        .opt-btn:hover:not(:disabled) { background: #EDE9FE !important; border-color: #A78BFA !important; }
        .opt-btn:disabled { opacity: 0.45; cursor: not-allowed; }
      `}</style>

      {/* Top bar */}
      <div style={S.topBar}>
        <div style={S.topBarLeft}>
          <div style={S.preplyLogo}>
            <div style={S.logoMark}><span style={S.logoDot} /></div>
            <span style={S.preplyName}>preply</span>
          </div>
          <div style={S.topBarDivider} />
          <span style={S.topBarLabel}>Assignment Creator</span>
        </div>
        <div style={S.topBarRight}>
          <div style={S.anamBadge}>
            <span style={S.anamPulse} />
            <span>Anam AI · All Modes</span>
          </div>
          <span style={S.hackBadge}>Hackathon Build</span>
        </div>
      </div>

      <div style={S.container}>
        <div style={S.header}>
          <p style={S.eyebrow}>✦ Avatar-powered homework</p>
          <h1 style={S.title}>Every assignment,<br /><em style={S.titleEm}>a conversation.</em></h1>
          <p style={S.subtitle}>Upload your lesson worksheet, choose a practice mode — each one launches a live Anam AI avatar session tailored to that pedagogy.</p>
        </div>

        <div style={S.grid}>
          {/* LEFT */}
          <div style={S.leftCol}>

            {/* Upload */}
            <section style={S.card}>
              <div style={S.cardHeader}>
                <span style={S.step}>1</span>
                <div>
                  <h2 style={S.cardTitle}>Lesson Worksheet</h2>
                  <p style={S.cardDesc}>Upload the materials from today's class</p>
                </div>
              </div>
              <div
                className="dropzone"
                style={{ ...S.dropzone, ...(isDragging ? S.dropzoneDrag : {}) }}
                onDrop={onDrop} onDragOver={onDragOver} onDragLeave={onDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <input ref={fileInputRef} type="file" multiple accept={ACCEPT_TYPES}
                  style={{ display: "none" }} onChange={(e) => handleFiles(e.target.files)} />
                <div style={S.dropzoneIcon}>{isDragging ? "🎯" : "📂"}</div>
                <p style={S.dropzoneText}>{isDragging ? "Release to upload" : "Drag & drop or click to browse"}</p>
                <p style={S.dropzoneHint}>PDF · JPEG · PNG · DOCX</p>
              </div>
              {files.length > 0 && (
                <ul style={S.fileList}>
                  {files.map(({ file, id }) => (
                    <li key={id} style={S.fileItem}>
                      <span>{getFileIcon(file.name)}</span>
                      <span style={S.fileName}>{file.name}</span>
                      <span style={S.fileSize}>{formatSize(file.size)}</span>
                      <button className="remove-btn" style={S.removeBtn} onClick={() => removeFile(id)}>✕</button>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Lesson Context + Optimize */}
            <section style={S.card}>
              <div style={S.cardHeader}>
                <span style={S.step}>2</span>
                <div>
                  <h2 style={S.cardTitle}>Lesson Context</h2>
                  <p style={S.cardDesc}>What did you cover? What should the student focus on?</p>
                </div>
              </div>

              <div style={{ position: "relative" }}>
                <textarea
                  style={{
                    ...S.textarea,
                    ...(optimized ? { borderColor: "#059669", boxShadow: "0 0 0 3px rgba(5,150,105,0.1)", animation: "optimizedPop 0.4s ease" } : {}),
                  }}
                  placeholder="e.g. Student practised present continuous with a cooking theme. Vocabulary: fry, bake, boil, chop, whisk. Level B1."
                  value={prompt}
                  onChange={(e) => { setPrompt(e.target.value); setOptimized(false); }}
                  rows={5}
                />
              </div>

              <div style={S.promptFooter}>
                <span style={S.charCount}>{prompt.length} chars</span>
                <button
                  className="opt-btn"
                  style={S.optimizeBtn}
                  disabled={!canOptimize}
                  onClick={handleOptimize}
                >
                  {isOptimizing ? (
                    <span style={S.spinnerWrap}>
                      <span style={{ ...S.spinner, borderTopColor: "#7C3AED", borderColor: "#DDD6FE" }} />
                      Optimizing…
                    </span>
                  ) : optimized ? (
                    <span style={{ color: "#059669", display: "flex", alignItems: "center", gap: 5 }}>
                      <span>✓</span> Optimized!
                    </span>
                  ) : (
                    <span style={S.optBtnInner}>
                      <span style={S.optBtnIcon}>✦</span>
                      Optimize prompt
                    </span>
                  )}
                </button>
              </div>

              {optimized && (
                <div style={S.optimizedBanner}>
                  <span>✦</span>
                  <span>Prompt rewritten for better avatar session generation</span>
                </div>
              )}
            </section>

            {/* How it works */}
            <section style={{ ...S.card, background: "linear-gradient(135deg,#F5F3FF 0%,#EFF6FF 100%)", border: "1px solid #DDD6FE" }}>
              <p style={S.howTitle}>How it works</p>
              <div style={S.howList}>
                {HOW_STEPS.map((item, i) => (
                  <div key={i} style={S.howRow}>
                    <div style={S.howLeft}>
                      <div style={{
                        ...S.howIconWrap,
                        background: i === HOW_STEPS.length - 1 ? "#EDE9FE" : "#fff",
                        border: i === HOW_STEPS.length - 1 ? "1.5px solid #A78BFA" : "1.5px solid #DDD6FE",
                      }}>
                        <span style={S.howIcon}>{item.icon}</span>
                      </div>
                      {i < HOW_STEPS.length - 1 && <div style={S.howLine} />}
                    </div>
                    <p style={{
                      ...S.howText,
                      fontWeight: i === HOW_STEPS.length - 1 ? 600 : 400,
                      color: i === HOW_STEPS.length - 1 ? "#5B21B6" : "#4B5563",
                    }}>{item.text}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>

          {/* RIGHT */}
          <div style={S.rightCol}>
            <section style={S.card}>
              <div style={S.cardHeader}>
                <span style={S.step}>3</span>
                <div>
                  <h2 style={S.cardTitle}>Avatar Practice Mode</h2>
                  <p style={S.cardDesc}>Each mode uses Anam AI with a different pedagogical exercise</p>
                </div>
              </div>

              <div style={S.typeGrid}>
                {ASSIGNMENT_TYPES.map((type) => {
                  const active = selectedType === type.id;
                  return (
                    <button
                      key={type.id}
                      className="type-btn"
                      style={{
                        ...S.typeBtn,
                        background: active ? type.bg : "#FAFAFA",
                        border: `2px solid ${active ? type.color : "#E5E7EB"}`,
                        color: active ? type.color : "#6B7280",
                        boxShadow: active ? `0 0 0 4px ${type.bg}` : "none",
                      }}
                      onClick={() => { setSelectedType(type.id); setGenerated(null); }}
                    >
                      <span style={S.typeBtnIcon}>{type.icon}</span>
                      <span style={S.typeBtnLabel}>{type.label}</span>
                      <span style={S.typeBtnSub}>{type.sublabel}</span>
                      <span style={{
                        ...S.anamTag,
                        background: active ? type.color : "#E5E7EB",
                        color: active ? "#fff" : "#9CA3AF",
                      }}>Anam AI</span>
                      {active && <span style={{ ...S.typeCheck, background: type.color }}>✓</span>}
                    </button>
                  );
                })}
              </div>

              {activeType && (
                <div style={S.mechanicBox} key={selectedType}>
                  <span style={{ fontSize: 18, flexShrink: 0 }}>{activeType.icon}</span>
                  <p style={S.mechanicText}>
                    <strong style={{ color: activeType.color }}>How the avatar works: </strong>
                    {activeType.mechanic}
                  </p>
                </div>
              )}
            </section>

            <button
              className="gen-btn"
              style={{
                ...S.generateBtn,
                background: canGenerate && activeType ? activeType.color : "#9CA3AF",
                opacity: canGenerate ? 1 : 0.55,
                cursor: canGenerate ? "pointer" : "not-allowed",
              }}
              disabled={!canGenerate || isGenerating}
              onClick={handleGenerate}
            >
              {isGenerating ? (
                <span style={S.spinnerWrap}>
                  <span style={S.spinner} />
                  Building avatar session…
                </span>
              ) : `✨  Generate ${activeType?.label ?? "Assignment"}`}
            </button>

            {!canGenerate && (
              <p style={S.generateHint}>Add lesson context above to continue</p>
            )}

            {/* Output */}
            {(isGenerating || demo) && (
              <section style={{ ...S.outputCard, borderColor: activeType?.border ?? "#EDE9FE", animation: "fadeUp 0.3s ease" }}>
                <div style={S.outputHeader}>
                  <div style={S.outputHeaderLeft}>
                    <span style={{ ...S.outputDot, background: activeType?.color ?? "#7C3AED" }} />
                    <span style={S.outputTitle}>Avatar Session</span>
                    {demo && (
                      <span style={{ ...S.modePill, background: activeType?.bg, color: activeType?.color }}>
                        {activeType?.label}
                      </span>
                    )}
                  </div>
                  {demo && (
                    <button className="copy-btn" style={S.copyBtn} onClick={handleCopy}>
                      {copied ? "✓ Copied" : "Copy prompt"}
                    </button>
                  )}
                </div>

                {isGenerating && (
                  <div style={S.skeleton}>
                    {[65, 85, 50, 75, 90, 60].map((w, i) => (
                      <div key={i} style={{ ...S.skeletonLine, width: `${w}%`, animationDelay: `${i * 0.07}s` }} />
                    ))}
                  </div>
                )}

                {demo && (
                  <div style={S.richOutput}>
                    {/* Avatar banner */}
                    <div style={{ ...S.avatarBanner, background: `linear-gradient(135deg, ${activeType?.color} 0%, ${activeType?.color}bb 100%)` }}>
                      <div style={S.avatarCircle}>
                        <span style={{ fontSize: 20 }}>{demo.avatar_emoji}</span>
                      </div>
                      <div style={S.avatarInfo}>
                        <span style={S.avatarName}>{demo.avatar_name} — AI {activeType?.avatarRole}</span>
                        <span style={S.avatarSub}>Live voice + text chat · {activeType?.sublabel}</span>
                      </div>
                      <button className="launch-btn" style={S.launchBtn}>▶ Launch Session</button>
                    </div>

                    <div style={S.richBody}>
                      <h3 style={S.richTitle}>{demo.title}</h3>
                      <p style={S.richObjective}><strong>Objective:</strong> {demo.objective}</p>

                      <div style={{ ...S.promptBox, borderColor: activeType?.border }}>
                        <div style={S.promptBoxHeader}>
                          <span>🤖</span>
                          <span style={{ ...S.promptBoxLabel, color: activeType?.color }}>Avatar System Prompt</span>
                          <span style={{ ...S.promptBoxBadge, background: activeType?.color }}>Sent to Anam</span>
                        </div>
                        <p style={S.promptBoxText}>{demo.avatar_prompt}</p>
                      </div>

                      <div style={S.tasksHeader}>
                        <span style={S.tasksLabel}>Student Tasks</span>
                        <span style={S.tasksCount}>{demo.tasks.length} activities</span>
                      </div>
                      <div style={S.tasksList}>
                        {demo.tasks.map((task, i) => (
                          <div key={i} className="task-card" style={{ ...S.taskCard, animation: `slideIn 0.3s ease ${i * 0.07}s both` }}>
                            <div style={{ ...S.taskIndex, background: activeType?.color }}>{i + 1}</div>
                            <div style={S.taskBody}>
                              <div style={S.taskTop}>
                                <span style={{ fontSize: 12 }}>{task.icon}</span>
                                <span style={S.taskLabel}>{task.label}</span>
                              </div>
                              <p style={S.taskContent}>{task.content}</p>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div style={S.tipRow}>
                        <span>💡</span>
                        <span style={S.tipText}>{demo.tip}</span>
                      </div>

                      {/* Lesson report callout */}
                      <div style={S.reportRow}>
                        <div style={S.reportLeft}>
                          <span style={S.reportIcon}>📊</span>
                          <div>
                            <p style={S.reportTitle}>Lesson Report</p>
                            <p style={S.reportSub}>Click here to see how your student did</p>
                          </div>
                        </div>
                        <div style={S.reportTags}>
                          {["Errors flagged", "Words used", "Tasks completed"].map(tag => (
                            <span key={tag} style={S.reportTag}>{tag}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const S = {
  page: { fontFamily: "'Sora', sans-serif", background: "#F7F6FF", minHeight: "100vh", color: "#111827" },
  topBar: {
    background: "#fff", borderBottom: "1px solid #EDE9FE",
    padding: "0 32px", height: 56,
    display: "flex", alignItems: "center", justifyContent: "space-between",
  },
  topBarLeft: { display: "flex", alignItems: "center", gap: 16 },
  topBarRight: { display: "flex", alignItems: "center", gap: 10 },
  logoMark: {
    width: 24, height: 24, borderRadius: 6,
    background: "linear-gradient(135deg,#7C3AED,#A78BFA)",
    display: "flex", alignItems: "center", justifyContent: "center",
  },
  logoDot: { width: 8, height: 8, borderRadius: "50%", background: "#fff" },
  preplyLogo: { display: "flex", alignItems: "center", gap: 8 },
  preplyName: { fontWeight: 700, fontSize: 17, letterSpacing: "-0.02em", color: "#111827" },
  topBarDivider: { width: 1, height: 20, background: "#E5E7EB" },
  topBarLabel: { fontSize: 13, fontWeight: 500, color: "#6B7280" },
  anamBadge: {
    display: "flex", alignItems: "center", gap: 6,
    background: "#EDE9FE", color: "#5B21B6",
    fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 20,
  },
  anamPulse: {
    width: 6, height: 6, borderRadius: "50%", background: "#7C3AED",
    animation: "glow 2s ease-in-out infinite", display: "inline-block",
  },
  hackBadge: { background: "#FEF3C7", color: "#92400E", fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 20 },
  container: { maxWidth: 1120, margin: "0 auto", padding: "44px 24px 64px" },
  header: { marginBottom: 40 },
  eyebrow: { fontSize: 11, fontWeight: 600, color: "#7C3AED", textTransform: "uppercase", letterSpacing: "0.1em", margin: "0 0 10px" },
  title: { fontFamily: "'Lora', serif", fontSize: 38, fontWeight: 600, lineHeight: 1.18, margin: "0 0 14px", color: "#111827" },
  titleEm: { fontStyle: "italic", color: "#7C3AED" },
  subtitle: { fontSize: 14, color: "#6B7280", lineHeight: 1.7, maxWidth: 520, margin: 0 },
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 28, alignItems: "start" },
  leftCol: { display: "flex", flexDirection: "column", gap: 20 },
  rightCol: { display: "flex", flexDirection: "column", gap: 14 },
  card: { background: "#fff", border: "1px solid #EDE9FE", borderRadius: 18, padding: 24, boxShadow: "0 1px 4px rgba(124,58,237,0.05)" },
  cardHeader: { display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 18 },
  step: {
    width: 26, height: 26, borderRadius: "50%", background: "#7C3AED", color: "#fff",
    fontSize: 11, fontWeight: 700, flexShrink: 0, marginTop: 2,
    display: "flex", alignItems: "center", justifyContent: "center",
  },
  cardTitle: { fontSize: 14, fontWeight: 600, margin: "0 0 2px", color: "#111827" },
  cardDesc: { fontSize: 12, color: "#9CA3AF", margin: 0 },
  dropzone: {
    border: "2px dashed #DDD6FE", borderRadius: 14, padding: "26px 20px",
    textAlign: "center", cursor: "pointer", transition: "border-color 0.2s", background: "#FAFAFA",
  },
  dropzoneDrag: { border: "2px dashed #7C3AED", background: "#F5F3FF" },
  dropzoneIcon: { fontSize: 26, marginBottom: 8 },
  dropzoneText: { fontSize: 13, fontWeight: 500, color: "#374151", margin: "0 0 4px" },
  dropzoneHint: { fontSize: 11, color: "#9CA3AF", margin: 0 },
  fileList: { listStyle: "none", margin: "14px 0 0", padding: 0, display: "flex", flexDirection: "column", gap: 8 },
  fileItem: {
    display: "flex", alignItems: "center", gap: 8,
    background: "#F9F8FF", border: "1px solid #EDE9FE", borderRadius: 10, padding: "8px 12px", fontSize: 13,
  },
  fileName: { flex: 1, fontSize: 12, color: "#374151", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  fileSize: { fontSize: 11, color: "#9CA3AF", flexShrink: 0 },
  removeBtn: { background: "none", border: "none", color: "#9CA3AF", cursor: "pointer", fontSize: 11, padding: "0 4px", transition: "color 0.15s", flexShrink: 0 },
  textarea: {
    width: "100%", border: "1.5px solid #E5E7EB", borderRadius: 12,
    padding: "12px 14px", fontSize: 13, color: "#374151",
    fontFamily: "'Sora', sans-serif", resize: "vertical", lineHeight: 1.65,
    transition: "border-color 0.2s, box-shadow 0.2s", background: "#FAFAFA",
  },
  promptFooter: { display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 10 },
  charCount: { fontSize: 11, color: "#C4B5FD" },
  optimizeBtn: {
    display: "flex", alignItems: "center",
    background: "#F5F3FF", border: "1.5px solid #DDD6FE",
    borderRadius: 10, padding: "7px 14px",
    fontSize: 12, fontWeight: 600, color: "#7C3AED",
    cursor: "pointer", fontFamily: "'Sora', sans-serif",
    gap: 6,
  },
  optBtnInner: { display: "flex", alignItems: "center", gap: 5 },
  optBtnIcon: { fontSize: 10, color: "#A78BFA" },
  optimizedBanner: {
    display: "flex", alignItems: "center", gap: 7,
    background: "#ECFDF5", border: "1px solid #A7F3D0",
    borderRadius: 10, padding: "8px 12px", marginTop: 10,
    fontSize: 12, fontWeight: 500, color: "#065F46",
    animation: "fadeUp 0.25s ease",
  },

  // How it works
  howTitle: { fontSize: 11, fontWeight: 700, color: "#5B21B6", margin: "0 0 16px", textTransform: "uppercase", letterSpacing: "0.07em" },
  howList: { display: "flex", flexDirection: "column", gap: 0 },
  howRow: { display: "flex", alignItems: "flex-start", gap: 12 },
  howLeft: { display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 },
  howIconWrap: {
    width: 30, height: 30, borderRadius: "50%",
    display: "flex", alignItems: "center", justifyContent: "center",
    background: "#fff", border: "1.5px solid #DDD6FE", flexShrink: 0,
  },
  howIcon: { fontSize: 13 },
  howLine: { width: 1, height: 14, background: "#DDD6FE", margin: "2px 0" },
  howText: { fontSize: 12, color: "#4B5563", lineHeight: 1.5, margin: "6px 0 14px" },

  typeGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 },
  typeBtn: {
    borderRadius: 14, padding: "16px 10px", cursor: "pointer",
    display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
    position: "relative", textAlign: "center",
  },
  typeBtnIcon: { fontSize: 22, marginBottom: 1 },
  typeBtnLabel: { fontSize: 12, fontWeight: 700, lineHeight: 1.2 },
  typeBtnSub: { fontSize: 10, opacity: 0.65, lineHeight: 1.3 },
  anamTag: { fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 10, letterSpacing: "0.04em", marginTop: 2, transition: "all 0.17s ease" },
  typeCheck: {
    position: "absolute", top: 8, right: 8, width: 17, height: 17,
    borderRadius: "50%", color: "#fff", fontSize: 9, fontWeight: 700,
    display: "flex", alignItems: "center", justifyContent: "center",
  },
  mechanicBox: {
    display: "flex", gap: 10, alignItems: "flex-start",
    background: "#F9F8FF", border: "1px solid #EDE9FE",
    borderRadius: 12, padding: "12px 14px", animation: "fadeUp 0.2s ease",
  },
  mechanicText: { fontSize: 12, color: "#4B5563", lineHeight: 1.65, margin: 0 },
  generateBtn: {
    width: "100%", color: "#fff", border: "none",
    borderRadius: 14, padding: "17px", fontSize: 14, fontWeight: 600,
    fontFamily: "'Sora', sans-serif", letterSpacing: "0.01em",
  },
  generateHint: { textAlign: "center", fontSize: 11, color: "#9CA3AF", margin: 0 },
  spinnerWrap: { display: "flex", alignItems: "center", justifyContent: "center", gap: 8 },
  spinner: {
    width: 14, height: 14, border: "2px solid rgba(255,255,255,0.3)",
    borderTop: "2px solid #fff", borderRadius: "50%",
    animation: "spin 0.7s linear infinite", display: "inline-block",
  },
  outputCard: { background: "#fff", border: "1.5px solid", borderRadius: 18, overflow: "hidden", boxShadow: "0 2px 12px rgba(124,58,237,0.07)" },
  outputHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "11px 16px", borderBottom: "1px solid #F3F4F6", background: "#FAFAFA",
  },
  outputHeaderLeft: { display: "flex", alignItems: "center", gap: 8 },
  outputDot: { width: 8, height: 8, borderRadius: "50%", animation: "glow 2s ease-in-out infinite" },
  outputTitle: { fontSize: 12, fontWeight: 600, color: "#374151" },
  modePill: { fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 10 },
  copyBtn: {
    background: "#fff", border: "1px solid #D1D5DB", borderRadius: 8, padding: "4px 12px",
    fontSize: 11, fontWeight: 500, color: "#6B7280", cursor: "pointer",
    fontFamily: "'Sora', sans-serif", transition: "background 0.15s",
  },
  skeleton: { padding: 20, display: "flex", flexDirection: "column", gap: 10 },
  skeletonLine: {
    height: 11, borderRadius: 6,
    background: "linear-gradient(90deg,#F3F4F6 25%,#E5E7EB 50%,#F3F4F6 75%)",
    backgroundSize: "500px 100%", animation: "shimmer 1.4s ease-in-out infinite",
  },
  richOutput: { display: "flex", flexDirection: "column" },
  avatarBanner: { display: "flex", alignItems: "center", gap: 14, padding: "16px 20px", color: "#fff" },
  avatarCircle: {
    width: 44, height: 44, borderRadius: "50%", background: "rgba(255,255,255,0.2)",
    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
    animation: "glow 2.5s ease-in-out infinite",
  },
  avatarInfo: { display: "flex", flexDirection: "column", gap: 2, flex: 1 },
  avatarName: { fontWeight: 600, fontSize: 13 },
  avatarSub: { fontSize: 10, opacity: 0.75 },
  launchBtn: {
    background: "rgba(255,255,255,0.2)", border: "1.5px solid rgba(255,255,255,0.4)",
    borderRadius: 10, padding: "8px 14px", color: "#fff",
    fontSize: 11, fontWeight: 600, cursor: "pointer",
    fontFamily: "'Sora', sans-serif", flexShrink: 0,
  },
  richBody: { padding: "18px 20px 22px" },
  richTitle: { fontFamily: "'Lora', serif", fontSize: 15, fontWeight: 600, margin: "0 0 6px", color: "#111827" },
  richObjective: { fontSize: 12, color: "#4B5563", lineHeight: 1.65, margin: "0 0 14px" },
  promptBox: { background: "#F9F8FF", border: "1px solid", borderRadius: 12, padding: "12px 14px", marginBottom: 16 },
  promptBoxHeader: { display: "flex", alignItems: "center", gap: 7, marginBottom: 8 },
  promptBoxLabel: { fontSize: 11, fontWeight: 600, flex: 1 },
  promptBoxBadge: { color: "#fff", fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 10 },
  promptBoxText: { fontSize: 11, color: "#6B7280", lineHeight: 1.65, margin: 0, fontStyle: "italic" },
  tasksHeader: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 },
  tasksLabel: { fontSize: 12, fontWeight: 600, color: "#374151" },
  tasksCount: { fontSize: 11, color: "#9CA3AF" },
  tasksList: { display: "flex", flexDirection: "column", gap: 8 },
  taskCard: {
    display: "flex", gap: 12, alignItems: "flex-start",
    border: "1px solid #EDE9FE", borderRadius: 12, padding: "11px 14px", background: "#FAFAFF",
  },
  taskIndex: {
    width: 20, height: 20, borderRadius: "50%", color: "#fff",
    fontSize: 9, fontWeight: 700, flexShrink: 0,
    display: "flex", alignItems: "center", justifyContent: "center", marginTop: 1,
  },
  taskBody: { flex: 1 },
  taskTop: { display: "flex", alignItems: "center", gap: 6, marginBottom: 3 },
  taskLabel: { fontSize: 12, fontWeight: 600, color: "#374151" },
  taskContent: { fontSize: 11, color: "#6B7280", lineHeight: 1.65, margin: 0 },
  tipRow: {
    display: "flex", alignItems: "flex-start", gap: 8, marginTop: 14,
    padding: "10px 12px", background: "#FFFBEB", borderRadius: 10, border: "1px solid #FDE68A",
  },
  tipText: { fontSize: 11, color: "#92400E", lineHeight: 1.55 },

  // Lesson report callout
  reportRow: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    gap: 10, marginTop: 12, padding: "12px 14px",
    background: "#F5F3FF", borderRadius: 12, border: "1px solid #DDD6FE",
  },
  reportLeft: { display: "flex", alignItems: "center", gap: 10 },
  reportIcon: { fontSize: 18 },
  reportTitle: { fontSize: 12, fontWeight: 600, color: "#5B21B6", margin: 0 },
  reportSub: { fontSize: 10, color: "#7C3AED", margin: 0, opacity: 0.75 },
  reportTags: { display: "flex", gap: 5, flexWrap: "wrap", justifyContent: "flex-end" },
  reportTag: {
    fontSize: 9, fontWeight: 600, padding: "3px 8px",
    background: "#EDE9FE", color: "#5B21B6", borderRadius: 10,
  },
};
