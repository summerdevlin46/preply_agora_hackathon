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
