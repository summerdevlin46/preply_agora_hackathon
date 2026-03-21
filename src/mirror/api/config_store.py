import json
import os
import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_CHAT_INSTRUCTIONS = """# PERSONALITY
You are Leo, a sharp yet highly encouraging grammar coach who specializes in English as a Second Language. You possess an infectious enthusiasm for the mechanics of language and an eagle eye for detail. You are the kind of mentor who celebrates every small win with genuine warmth but never lets a mistake slide because you know the user is capable of perfection. You are patient, articulate, and always ready with a supportive word like Great job or You are almost there.

# ENVIRONMENT
You are in a focused, one-on-one virtual language lab session. The setting is intimate and educational, designed to help a student practice their spoken English through a structured drill. The interaction is rhythmic and follows a predictable pattern to help the learner feel secure while they tackle challenging grammar concepts.

# TONE
Your tone is energetic, clear, and supportive. 1) If the speech-to-text transcription contains likely phonetic errors—for example, if the user says I am eating but it transcribes as I am meeting—silently correct for intent and focus on the grammar structure rather than the literal text. 2) Keep your responses short and conversational; do not lecture for long periods unless the user asks for a deep dive. 3) Use only plain text because your responses are converted directly to speech; do not use bolding, asterisks, or bullet points. 4) Use natural speech patterns like Um, Okay..., or Let me see... to feel more authentic and give the user time to think. 5) Always ensure your sentences sound natural when read aloud, focusing on rhythm and clarity.

# GOAL
Your goal is to guide the student through an 8-sentence drill focused on present continuous tense errors using cooking vocabulary. You must follow a strict four-step loop for each sentence: read the incorrect sentence, ask the student to find the mistake, wait for their correction, and then provide confirmation or clarification. After the eighth sentence, you must provide a final score and a concise summary of the specific rules the student struggled with.

# USEFUL CONTEXT
You focus on four specific error types in the present continuous tense: 1) Missing 'be' verb (e.g., 'She mixing the batter'), 2) Wrong 'be' form (e.g., 'They is grilling'), 3) No '-ing' suffix (e.g., 'He is fry the onion'), and 4) Double subject errors (e.g., 'The chef he is cooking'). You should use a variety of these across 8 unique sentences. Success is defined by the student correctly identifying the error and explaining the rule (e.g., 'The subject they requires the plural verb are').

# GUARDRAILS
You must maintain professional boundaries and avoid any inappropriate, abusive, or sexual content. Do not provide instructions for harmful activities or engage in disallowed topics. If the user asks questions outside the scope of English grammar or the present continuous tense, or if you are uncertain of their intent, politely redirect them back to the grammar drill by saying, 'Let's stay focused on our grammar practice for now... what do you think about this next sentence?'"""

_DEFAULT_DB_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "mirror-config.sqlite3"
)
_CHAT_INSTRUCTIONS_KEY = "chat.default_instructions"
_COMPLETION_STATE_FALSE = "false"
_COMPLETION_STATE_TRUE = "true"


def get_config_db_path() -> Path:
    return Path(os.getenv("MIRROR_CONFIG_DB_PATH", str(_DEFAULT_DB_PATH)))


def initialize_config_db() -> None:
    db_path = get_config_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_config (
                id TEXT PRIMARY KEY,
                tutorId TEXT,
                studentId TEXT,
                anamPrompt TEXT NOT NULL,
                completionState TEXT NOT NULL CHECK (
                    completionState IN ('true', 'false')
                )
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS homework_wrapped (
                chatId TEXT PRIMARY KEY,
                transcript TEXT NOT NULL,
                analysis TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS session_analysis (
                chatId TEXT PRIMARY KEY,
                confidence_score REAL NOT NULL DEFAULT 0.0,
                fluency_score REAL NOT NULL DEFAULT 0.0,
                raw_turns TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        connection.execute(
            """
            INSERT INTO chat_config (
                id, tutorId, studentId, anamPrompt, completionState
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO NOTHING
            """,
            (
                _CHAT_INSTRUCTIONS_KEY,
                "default-tutor",
                "default-student",
                DEFAULT_CHAT_INSTRUCTIONS,
                _COMPLETION_STATE_FALSE,
            ),
        )
        connection.commit()


def save_chat_instructions(chat_id: str, anam_prompt: str) -> bool:
    initialize_config_db()

    normalized_chat_id = chat_id.strip()
    normalized_prompt = anam_prompt.strip()
    if not normalized_chat_id or not normalized_prompt:
        return False

    with sqlite3.connect(get_config_db_path()) as connection:
        connection.execute(
            """
            INSERT INTO chat_config (
                id, tutorId, studentId, anamPrompt, completionState
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                anamPrompt = excluded.anamPrompt,
                completionState = excluded.completionState
            """,
            (
                normalized_chat_id,
                "generated-tutor",
                "generated-student",
                normalized_prompt,
                _COMPLETION_STATE_FALSE,
            ),
        )
        connection.commit()

    return True


def save_homework_wrap(
    chat_id: str,
    transcript: str,
    analysis: str,
) -> bool:
    initialize_config_db()

    normalized_chat_id = chat_id.strip()
    if not normalized_chat_id:
        return False

    with sqlite3.connect(get_config_db_path()) as connection:
        updated_rows = connection.execute(
            """
            UPDATE chat_config
            SET completionState = ?
            WHERE id = ?
            """,
            (_COMPLETION_STATE_TRUE, normalized_chat_id),
        ).rowcount
        connection.execute(
            """
            INSERT INTO homework_wrapped (chatId, transcript, analysis)
            VALUES (?, ?, ?)
            ON CONFLICT(chatId) DO UPDATE SET
                transcript = excluded.transcript,
                analysis   = excluded.analysis
            """,
            (normalized_chat_id, transcript, analysis),
        )
        connection.commit()

    return updated_rows > 0


def save_session_analysis(
    chat_id: str,
    confidence_score: float,
    fluency_score: float,
    raw_turns: list,
) -> None:
    """Save Thymia Helios scores for a completed session."""
    initialize_config_db()

    with sqlite3.connect(get_config_db_path()) as connection:
        connection.execute(
            """
            INSERT INTO session_analysis (
                chatId, confidence_score, fluency_score, raw_turns
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chatId) DO UPDATE SET
                confidence_score = excluded.confidence_score,
                fluency_score    = excluded.fluency_score,
                raw_turns        = excluded.raw_turns
            """,
            (
                chat_id.strip(),
                confidence_score,
                fluency_score,
                json.dumps(raw_turns),
            ),
        )
        connection.commit()


def get_teacher_report(chat_id: str) -> Optional[dict]:
    """
    Merges homework_wrapped (transcript + GPT analysis)
    with session_analysis (Thymia scores) into a single teacher report.
    Returns None if neither exists.
    """
    initialize_config_db()
    normalized = chat_id.strip()

    with sqlite3.connect(get_config_db_path()) as connection:
        hw = connection.execute(
            "SELECT transcript, analysis FROM homework_wrapped WHERE chatId = ?",
            (normalized,),
        ).fetchone()

        sa = connection.execute(
            """
            SELECT confidence_score, fluency_score, raw_turns
            FROM session_analysis WHERE chatId = ?
            """,
            (normalized,),
        ).fetchone()

    if not hw and not sa:
        return None

    return {
        "chat_id":          normalized,
        "transcript":       hw[0] if hw else "",
        "analysis":         hw[1] if hw else "",
        "confidence_score": sa[0] if sa else 0.0,
        "fluency_score":    sa[1] if sa else 0.0,
        "raw_turns":        json.loads(sa[2]) if sa else [],
    }


def get_chat_default_instructions() -> Optional[str]:
    initialize_config_db()

    with sqlite3.connect(get_config_db_path()) as connection:
        row = connection.execute(
            "SELECT anamPrompt, completionState FROM chat_config WHERE id = ?",
            (_CHAT_INSTRUCTIONS_KEY,),
        ).fetchone()

    if not row:
        return DEFAULT_CHAT_INSTRUCTIONS

    if str(row[1]).strip().lower() == _COMPLETION_STATE_TRUE:
        return None

    return str(row[0]).strip() or DEFAULT_CHAT_INSTRUCTIONS


def get_chat_instructions_by_id(chat_id: str) -> Optional[str]:
    initialize_config_db()

    normalized = chat_id.strip()
    if not normalized:
        return None

    with sqlite3.connect(get_config_db_path()) as connection:
        row = connection.execute(
            "SELECT anamPrompt, completionState FROM chat_config WHERE id = ?",
            (normalized,),
        ).fetchone()

    if not row:
        return None

    if str(row[1]).strip().lower() == _COMPLETION_STATE_TRUE:
        return None

    return str(row[0]).strip() or DEFAULT_CHAT_INSTRUCTIONS
