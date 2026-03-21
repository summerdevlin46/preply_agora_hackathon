"use client";

import { useState, useRef, useCallback } from "react";
import styled, { keyframes } from "styled-components";
import {
  Wallet, ChevronDown, CalendarClock, HelpCircle, Bell,
  BookOpen, Mic, PenLine, FileText, FolderOpen, Image,
  FilePen, X, Sparkles, ClipboardList, FileSpreadsheet, Check, ArrowLeft,
} from "lucide-react";

const ASSIGNMENT_TYPES = [
  {
    id: "vocab",
    label: "Vocabulary",
    sublabel: "Reinforcement",
    icon: BookOpen,
    color: "#7C3AED",
    bg: "#F5F3FF",
    border: "#DDD6FE",
  },
  {
    id: "speaking",
    label: "Speaking",
    sublabel: "Practice",
    icon: Mic,
    color: "#0891B2",
    bg: "#ECFEFF",
    border: "#A5F3FC",
  },
  {
    id: "writing",
    label: "Writing",
    sublabel: "Exercise",
    icon: PenLine,
    color: "#059669",
    bg: "#ECFDF5",
    border: "#A7F3D0",
  },
  {
    id: "reading",
    label: "Reading",
    sublabel: "Comprehension",
    icon: FileText,
    color: "#D97706",
    bg: "#FFFBEB",
    border: "#FDE68A",
  },
];

const ACCEPT_TYPES = ".pdf,.jpg,.jpeg,.png,.docx,.doc";

/* ── keyframes ── */
const spin = keyframes`
  to { transform: rotate(360deg); }
`;

const pulse = keyframes`
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
`;

/* ── styled components ── */
const Page = styled.div`
  font-family: inherit;
  background: #fff;
  min-height: 100vh;
  color: #111827;
`;

const TopBar = styled.div`
  background: #fff;
  border-bottom: 1px solid #efeef3;
  padding: 24px 32px;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const TopBarLabel = styled.span`
  font-weight: 600;
  font-size: 15px;
  color: #111827;
`;

const TopBarBadge = styled.span`
  background: #fef3c7;
  color: #92400e;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
`;

const TopBarRight = styled.div`
  display: flex;
  align-items: center;
  gap: 20px;
  margin-left: auto;
`;

const BalanceItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: "PreplyInter", sans-serif;
  font-size: 15px;
  font-weight: 400;
  color: #111827;
`;

const EarnButton = styled.button`
  background: #fff;
  border: 1.5px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 20px;
  font-family: "PreplyInter", sans-serif;
  font-size: 15px;
  font-weight: 400;
  color: #111827;
  cursor: pointer;
  transition: border-color 0.15s;

  &:hover {
    border-color: #9ca3af;
  }
`;

const LangSelector = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: "PreplyInter", sans-serif;
  font-size: 15px;
  font-weight: 400;
  color: #111827;
  cursor: pointer;
`;

const IconButton = styled.button`
  position: relative;
  background: none;
  border: none;
  padding: 4px;
  cursor: pointer;
  color: #111827;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const BadgeCount = styled.span`
  position: absolute;
  top: -4px;
  right: -6px;
  background: #111827;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
`;

const Avatar = styled.img`
  width: 36px;
  height: 36px;
  border-radius: 8px;
  object-fit: cover;
  cursor: pointer;
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

const PromptMeta = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
`;

const CharCount = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  color: #9ca3af;
`;

const TypeGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
`;

const TypeBtn = styled.button`
  border-radius: 12px;
  padding: 16px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  position: relative;
  transition: all 0.15s ease;
  text-align: center;
  background: ${(props) => (props.$active ? props.$bg : "#FAFAFA")};
  border: 2px solid ${(props) => (props.$active ? props.$color : "#E5E7EB")};
  color: ${(props) => (props.$active ? props.$color : "#6B7280")};
`;

const TypeBtnIcon = styled.span`
  margin-bottom: 2px;
  display: flex;
`;

const TypeBtnLabel = styled.span`
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.06em;
`;

const TypeBtnSub = styled.span`
  font-family: "PreplyInter", sans-serif;
  font-size: 11px;
  opacity: 0.7;
`;

const TypeCheck = styled.span`
  position: absolute;
  top: 8px;
  right: 8px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${(props) => props.$color};
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
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid #fff;
  border-radius: 50%;
  display: inline-block;
  animation: ${spin} 0.7s linear infinite;
`;

const OutputCard = styled.section`
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: none;
`;

const OutputHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid #f3f4f6;
  background: #fff;
`;

const OutputTitle = styled.span`
  font-size: 13px;
  font-weight: 600;
  color: #374151;
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
`;

const OutputText = styled.pre`
  padding: 18px;
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: #374151;
  white-space: pre-wrap;
  font-family: "PreplyInter", sans-serif;
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

const NavBar = styled.nav`
  background: #fff;
  padding: 0 32px;
  display: flex;
  align-items: stretch;
  gap: 0;
  border-bottom: 1px solid #e5e7eb;
  overflow-x: auto;
`;

const NavItem = styled.a`
  font-family: inherit;
  font-size: 14px;
  font-weight: ${(props) => (props.$active ? "600" : "500")};
  color: ${(props) => (props.$active ? "#111827" : "#6b7280")};
  padding: 14px 16px;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  position: relative;
  transition: color 0.15s;
  letter-spacing: 0.04em;

  &::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 16px;
    right: 16px;
    height: 4px;
    border-radius: 1px;
    background: ${(props) => (props.$active ? "#ff7aac" : "transparent")};
  }

  &:hover {
    color: #111827;
  }
`;

const Wrapper = styled.div``

/* ── component ── */
export default function PreplyTeacherDashboard() {
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
    if (name.endsWith(".pdf")) return <FileText size={16} />;
    if (name.match(/\.(jpg|jpeg|png)$/i)) return <Image size={16} />;
    return <FilePen size={16} />;
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
3. 3\u20135 specific tasks or questions
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
      setGenerated("Failed to generate assignment. Please try again.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Page>
      <TopBar>
        <TopBarLabel>
          <img src="/preply.svg" alt="Preply" />
        </TopBarLabel>
        <TopBarBadge>Hackathon submission</TopBarBadge>

        <TopBarRight>
          <BalanceItem>
            <Wallet size={20} />
            0.00 USD
          </BalanceItem>
          <EarnButton>Earn $25</EarnButton>
          <LangSelector>
            English, USD
            <ChevronDown size={18} />
          </LangSelector>
          <IconButton>
            <CalendarClock size={22} />
            <BadgeCount>14</BadgeCount>
          </IconButton>
          <IconButton>
            <HelpCircle size={22} />
          </IconButton>
          <IconButton>
            <Bell size={22} />
          </IconButton>
          <Avatar src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&h=80&fit=crop&crop=face" alt="Profile" />
        </TopBarRight>
      </TopBar>

      <NavBar>
        <NavItem href="#">Home</NavItem>
        <NavItem href="#">Messages</NavItem>
        <NavItem href="#">Calendar</NavItem>
        <NavItem href="#">Students</NavItem>
        <NavItem href="#">Classroom</NavItem>
        <NavItem href="#">Insights</NavItem>
        <NavItem href="#">My profile</NavItem>
        <NavItem href="#">Settings</NavItem>
        <NavItem href="#">Academy</NavItem>
        <NavItem href="#">Community</NavItem>
        <NavItem href="#" $active>Teacher Dashboard</NavItem>
      </NavBar>

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
                const active = selectedTypes.includes(type.id);
                return (
                  <SidebarItem
                    key={type.id}
                    $active={active}
                    $bg={type.bg}
                    $color={type.color}
                    onClick={() => toggleType(type.id)}
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
                {selectedTypes.length === 0
                  ? "Select an assignment type"
                  : selectedTypes
                      .map((id) => ASSIGNMENT_TYPES.find((t) => t.id === id)?.label)
                      .join(" + ")}
              </SectionTitle>

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
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={5}
                />
                <PromptMeta>
                  <CharCount>{prompt.length} / 500</CharCount>
                </PromptMeta>
              </Card>

              {/* Generate */}
              <GenerateBtn
                $canGenerate={canGenerate}
                disabled={!canGenerate || isGenerating}
                onClick={handleGenerate}
              >
                {isGenerating ? (
                  <SpinnerWrap><Spinner /> Generating...</SpinnerWrap>
                ) : (
                  <SpinnerWrap><FileSpreadsheet size={20} /> Generate assignment</SpinnerWrap>
                )}
              </GenerateBtn>

              {!canGenerate && (
                <GenerateHint>
                  {selectedTypes.length === 0 && !prompt ? "Select a type and add a prompt to continue" :
                    selectedTypes.length === 0 ? "Select at least one assignment type" :
                      "Add a teacher prompt to continue"}
                </GenerateHint>
              )}

              {/* Output */}
              {(isGenerating || generated) && (
                <OutputCard>
                  <OutputHeader>
                    <OutputTitle><ClipboardList size={14} style={{ marginRight: 6, verticalAlign: "middle" }} /> Generated Assignment</OutputTitle>
                    {generated && (
                      <CopyBtn onClick={() => navigator.clipboard.writeText(generated)}>Copy</CopyBtn>
                    )}
                  </OutputHeader>
                  {isGenerating ? (
                    <Skeleton>
                      <SkeletonLine $width="70%" />
                      <SkeletonLine $width="90%" />
                      <SkeletonLine $width="60%" />
                      <SkeletonLine $width="80%" />
                      <SkeletonLine $width="50%" />
                    </Skeleton>
                  ) : (
                    <OutputText>{generated}</OutputText>
                  )}
                </OutputCard>
              )}
            </MainCol>
          </Grid>
        </Container>
      </Wrapper>
    </Page>
  );
}
