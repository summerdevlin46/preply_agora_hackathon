CREATE TABLE chat_config (
    id TEXT PRIMARY KEY,
    tutorId TEXT,
    studentId TEXT,
    anamPrompt TEXT NOT NULL,
    completionState TEXT NOT NULL CHECK (completionState IN ('true', 'false'))
);
