CREATE TABLE chat_config (
    id TEXT PRIMARY KEY,
    tutorId TEXT,
    studentId TEXT,
    anamPrompt TEXT NOT NULL,
    completionState TEXT NOT NULL CHECK (completionState IN ('true', 'false'))
);

CREATE TABLE homework_wrapped (
    chatId TEXT PRIMARY KEY,
    transcript TEXT NOT NULL,
    analysis TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_analysis (
    chatId TEXT PRIMARY KEY,
    confidence_score REAL NOT NULL DEFAULT 0.0,
    fluency_score REAL NOT NULL DEFAULT 0.0,
    raw_turns TEXT NOT NULL DEFAULT '[]'
);
