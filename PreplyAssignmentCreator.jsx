import { useState, useRef, useCallback } from "react";

const ASSIGNMENT_TYPES = [
  {
    id: "vocab",
    label: "Vocabulary",
    sublabel: "Reinforcement",
    icon: "📖",
    color: "#7C3AED",
    bg: "#F5F3FF",
    border: "#DDD6FE",
  },
  {
    id: "speaking",
    label: "Speaking",
    sublabel: "Practice",
    icon: "🎙️",
    color: "#0891B2",
    bg: "#ECFEFF",
    border: "#A5F3FC",
  },
  {
    id: "writing",
    label: "Writing",
    sublabel: "Exercise",
    icon: "✍️",
    color: "#059669",
    bg: "#ECFDF5",
    border: "#A7F3D0",
  },
  {
    id: "reading",
    label: "Reading",
    sublabel: "Comprehension",
    icon: "📄",
    color: "#D97706",
    bg: "#FFFBEB",
    border: "#FDE68A",
  },
];

const ACCEPT_TYPES = ".pdf,.jpg,.jpeg,.png,.docx,.doc";

export default function PreplyAssignmentCreator() {
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generated, setGenerated] = useState(null);
  const fileInputRef = useRef(null);

  const toggleType = (id) => {
    setSelectedTypes((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
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
    if (name.endsWith(".pdf")) return "📕";
    if (name.match(/\.(jpg|jpeg|png)$/i)) return "🖼️";
    return "📝";
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  };

  const canGenerate = selectedTypes.length > 0 && prompt.trim().length > 0;

  const handleGenerate = async () => {
    if (!canGenerate) return;
    setIsGenerating(true);
    setGenerated(null);

    const typeLabels = selectedTypes.map((id) => ASSIGNMENT_TYPES.find((t) => t.id === id)?.label).join(", ");
    const fileNote = files.length > 0 ? ` Files uploaded: ${files.map((f) => f.file.name).join(", ")}.` : "";

    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: `You are an expert language tutor assistant on Preply. Generate a concise, ready-to-use assignment for a student based on the teacher's instructions. Format your response with:
1. A short assignment title
2. Clear objective (1 sentence)  
3. 3–5 specific tasks or questions
Keep it practical and engaging. No preamble.`,
          messages: [
            {
              role: "user",
              content: `Assignment type(s): ${typeLabels}${fileNote}\nTeacher instructions: ${prompt}`,
            },
          ],
        }),
      });

      const data = await response.json();
      const text = data.content?.find((b) => b.type === "text")?.text || "No response generated.";
      setGenerated(text);
    } catch (err) {
      setGenerated("⚠️ Failed to generate assignment. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div style={styles.page}>
      {/* Top nav strip matching Preply */}
      <div style={styles.topBar}>
        <span style={styles.topBarLabel}>✨ Assignment Creator</span>
        <span style={styles.topBarBadge}>Hackathon Feature</span>
      </div>

      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>Create Assignment</h1>
          <p style={styles.subtitle}>Upload materials, describe your goal, and let AI build it for your student.</p>
        </div>

        <div style={styles.grid}>
          {/* LEFT COLUMN */}
          <div style={styles.leftCol}>

            {/* Upload */}
            <section style={styles.card}>
              <div style={styles.cardHeader}>
                <span style={styles.cardStep}>1</span>
                <div>
                  <h2 style={styles.cardTitle}>Upload Worksheet</h2>
                  <p style={styles.cardDesc}>PDF, JPEG, DOCX supported</p>
                </div>
              </div>

              <div
                style={{ ...styles.dropzone, ...(isDragging ? styles.dropzoneDrag : {}) }}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept={ACCEPT_TYPES}
                  style={{ display: "none" }}
                  onChange={(e) => handleFiles(e.target.files)}
                />
                <div style={styles.dropzoneIcon}>📂</div>
                <p style={styles.dropzoneText}>
                  {isDragging ? "Drop files here" : "Drag & drop or click to browse"}
                </p>
                <p style={styles.dropzoneHint}>PDF · JPEG · DOCX</p>
              </div>

              {files.length > 0 && (
                <ul style={styles.fileList}>
                  {files.map(({ file, id }) => (
                    <li key={id} style={styles.fileItem}>
                      <span style={styles.fileIcon}>{getFileIcon(file.name)}</span>
                      <span style={styles.fileName}>{file.name}</span>
                      <span style={styles.fileSize}>{formatSize(file.size)}</span>
                      <button style={styles.removeBtn} onClick={() => removeFile(id)}>✕</button>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Prompt */}
            <section style={styles.card}>
              <div style={styles.cardHeader}>
                <span style={styles.cardStep}>2</span>
                <div>
                  <h2 style={styles.cardTitle}>Teacher Prompt</h2>
                  <p style={styles.cardDesc}>Describe your goal for this assignment</p>
                </div>
              </div>
              <textarea
                style={styles.textarea}
                placeholder="e.g. Create 5 fill-in-the-blank sentences using vocabulary from the worksheet, targeting B1 level..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={5}
              />
              <div style={styles.promptMeta}>
                <span style={styles.charCount}>{prompt.length} / 500</span>
              </div>
            </section>
          </div>

          {/* RIGHT COLUMN */}
          <div style={styles.rightCol}>

            {/* Assignment type */}
            <section style={styles.card}>
              <div style={styles.cardHeader}>
                <span style={styles.cardStep}>3</span>
                <div>
                  <h2 style={styles.cardTitle}>Assignment Type</h2>
                  <p style={styles.cardDesc}>Select one or more</p>
                </div>
              </div>
              <div style={styles.typeGrid}>
                {ASSIGNMENT_TYPES.map((type) => {
                  const active = selectedTypes.includes(type.id);
                  return (
                    <button
                      key={type.id}
                      style={{
                        ...styles.typeBtn,
                        background: active ? type.bg : "#FAFAFA",
                        border: `2px solid ${active ? type.color : "#E5E7EB"}`,
                        color: active ? type.color : "#6B7280",
                      }}
                      onClick={() => toggleType(type.id)}
                    >
                      <span style={styles.typeBtnIcon}>{type.icon}</span>
                      <span style={styles.typeBtnLabel}>{type.label}</span>
                      <span style={styles.typeBtnSub}>{type.sublabel}</span>
                      {active && (
                        <span style={{ ...styles.typeCheck, background: type.color }}>✓</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </section>

            {/* Generate */}
            <button
              style={{
                ...styles.generateBtn,
                opacity: canGenerate ? 1 : 0.5,
                cursor: canGenerate ? "pointer" : "not-allowed",
              }}
              disabled={!canGenerate || isGenerating}
              onClick={handleGenerate}
            >
              {isGenerating ? (
                <span style={styles.spinnerWrap}><span style={styles.spinner} /> Generating...</span>
              ) : (
                "✨ Generate Assignment"
              )}
            </button>

            {!canGenerate && (
              <p style={styles.generateHint}>
                {selectedTypes.length === 0 && !prompt ? "Select a type and add a prompt to continue" :
                  selectedTypes.length === 0 ? "Select at least one assignment type" :
                    "Add a teacher prompt to continue"}
              </p>
            )}

            {/* Output */}
            {(isGenerating || generated) && (
              <section style={styles.outputCard}>
                <div style={styles.outputHeader}>
                  <span style={styles.outputTitle}>📋 Generated Assignment</span>
                  {generated && (
                    <button
                      style={styles.copyBtn}
                      onClick={() => navigator.clipboard.writeText(generated)}
                    >Copy</button>
                  )}
                </div>
                {isGenerating ? (
                  <div style={styles.skeleton}>
                    <div style={{ ...styles.skeletonLine, width: "70%" }} />
                    <div style={{ ...styles.skeletonLine, width: "90%" }} />
                    <div style={{ ...styles.skeletonLine, width: "60%" }} />
                    <div style={{ ...styles.skeletonLine, width: "80%" }} />
                    <div style={{ ...styles.skeletonLine, width: "50%" }} />
                  </div>
                ) : (
                  <pre style={styles.outputText}>{generated}</pre>
                )}
              </section>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');
        * { box-sizing: border-box; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100%{opacity:0.4} 50%{opacity:0.8} }
      `}</style>
    </div>
  );
}

const styles = {
  page: {
    fontFamily: "'DM Sans', sans-serif",
    background: "#F9FAFB",
    minHeight: "100vh",
    color: "#111827",
  },
  topBar: {
    background: "#fff",
    borderBottom: "1px solid #E5E7EB",
    padding: "12px 32px",
    display: "flex",
    alignItems: "center",
    gap: 12,
  },
  topBarLabel: {
    fontWeight: 600,
    fontSize: 15,
    color: "#111827",
  },
  topBarBadge: {
    background: "#FEF3C7",
    color: "#92400E",
    fontSize: 11,
    fontWeight: 600,
    padding: "2px 8px",
    borderRadius: 20,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  container: {
    maxWidth: 1100,
    margin: "0 auto",
    padding: "40px 24px",
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontFamily: "'DM Serif Display', serif",
    fontSize: 32,
    fontWeight: 400,
    margin: "0 0 6px",
    color: "#111827",
  },
  subtitle: {
    fontSize: 15,
    color: "#6B7280",
    margin: 0,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 24,
    alignItems: "start",
  },
  leftCol: { display: "flex", flexDirection: "column", gap: 24 },
  rightCol: { display: "flex", flexDirection: "column", gap: 16 },
  card: {
    background: "#fff",
    border: "1px solid #E5E7EB",
    borderRadius: 16,
    padding: "24px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
  },
  cardHeader: {
    display: "flex",
    alignItems: "flex-start",
    gap: 14,
    marginBottom: 18,
  },
  cardStep: {
    width: 28,
    height: 28,
    borderRadius: "50%",
    background: "#111827",
    color: "#fff",
    fontSize: 13,
    fontWeight: 700,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    marginTop: 2,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 600,
    margin: "0 0 2px",
    color: "#111827",
  },
  cardDesc: {
    fontSize: 13,
    color: "#9CA3AF",
    margin: 0,
  },
  dropzone: {
    border: "2px dashed #D1D5DB",
    borderRadius: 12,
    padding: "32px 24px",
    textAlign: "center",
    cursor: "pointer",
    transition: "all 0.2s ease",
    background: "#FAFAFA",
  },
  dropzoneDrag: {
    border: "2px dashed #6366F1",
    background: "#EEF2FF",
  },
  dropzoneIcon: { fontSize: 32, marginBottom: 8 },
  dropzoneText: { fontSize: 14, fontWeight: 500, color: "#374151", margin: "0 0 4px" },
  dropzoneHint: { fontSize: 12, color: "#9CA3AF", margin: 0 },
  fileList: {
    listStyle: "none",
    margin: "14px 0 0",
    padding: 0,
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  fileItem: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    background: "#F9FAFB",
    border: "1px solid #E5E7EB",
    borderRadius: 8,
    padding: "8px 12px",
  },
  fileIcon: { fontSize: 16 },
  fileName: { fontSize: 13, color: "#374151", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
  fileSize: { fontSize: 11, color: "#9CA3AF", flexShrink: 0 },
  removeBtn: {
    background: "none",
    border: "none",
    color: "#9CA3AF",
    cursor: "pointer",
    fontSize: 12,
    padding: "0 4px",
    flexShrink: 0,
  },
  textarea: {
    width: "100%",
    border: "1.5px solid #E5E7EB",
    borderRadius: 10,
    padding: "12px 14px",
    fontSize: 14,
    color: "#374151",
    fontFamily: "'DM Sans', sans-serif",
    resize: "vertical",
    outline: "none",
    lineHeight: 1.6,
    transition: "border-color 0.15s",
  },
  promptMeta: {
    display: "flex",
    justifyContent: "flex-end",
    marginTop: 6,
  },
  charCount: { fontSize: 11, color: "#9CA3AF" },
  typeGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 10,
  },
  typeBtn: {
    borderRadius: 12,
    padding: "16px 12px",
    cursor: "pointer",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: 3,
    position: "relative",
    transition: "all 0.15s ease",
    textAlign: "center",
  },
  typeBtnIcon: { fontSize: 24, marginBottom: 2 },
  typeBtnLabel: { fontSize: 14, fontWeight: 600 },
  typeBtnSub: { fontSize: 11, opacity: 0.7 },
  typeCheck: {
    position: "absolute",
    top: 8,
    right: 8,
    width: 18,
    height: 18,
    borderRadius: "50%",
    color: "#fff",
    fontSize: 10,
    fontWeight: 700,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  generateBtn: {
    width: "100%",
    background: "#111827",
    color: "#fff",
    border: "none",
    borderRadius: 12,
    padding: "16px",
    fontSize: 15,
    fontWeight: 600,
    fontFamily: "'DM Sans', sans-serif",
    transition: "all 0.15s ease",
    letterSpacing: "0.01em",
  },
  generateHint: {
    textAlign: "center",
    fontSize: 12,
    color: "#9CA3AF",
    margin: "0",
  },
  spinnerWrap: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  spinner: {
    width: 16,
    height: 16,
    border: "2px solid rgba(255,255,255,0.3)",
    borderTop: "2px solid #fff",
    borderRadius: "50%",
    display: "inline-block",
    animation: "spin 0.7s linear infinite",
  },
  outputCard: {
    background: "#fff",
    border: "1.5px solid #E5E7EB",
    borderRadius: 16,
    overflow: "hidden",
    boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
  },
  outputHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "14px 18px",
    borderBottom: "1px solid #F3F4F6",
    background: "#F9FAFB",
  },
  outputTitle: { fontSize: 13, fontWeight: 600, color: "#374151" },
  copyBtn: {
    background: "none",
    border: "1px solid #D1D5DB",
    borderRadius: 6,
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 500,
    color: "#6B7280",
    cursor: "pointer",
    fontFamily: "'DM Sans', sans-serif",
  },
  outputText: {
    padding: "18px",
    margin: 0,
    fontSize: 13,
    lineHeight: 1.7,
    color: "#374151",
    whiteSpace: "pre-wrap",
    fontFamily: "'DM Sans', sans-serif",
  },
  skeleton: { padding: "18px", display: "flex", flexDirection: "column", gap: 10 },
  skeletonLine: {
    height: 12,
    background: "#F3F4F6",
    borderRadius: 6,
    animation: "pulse 1.5s ease-in-out infinite",
  },
};
