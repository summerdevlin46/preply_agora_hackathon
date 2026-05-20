from __future__ import annotations

import httpx
import os

from mirror.ocr.parser import parse_worksheet


BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = float(os.getenv("SMOKE_API_TIMEOUT", "300"))
BASE_CHAT_ID = "smoke-adverbs"
MODE = "avatar_conversation"
CHAT_ID = f"{BASE_CHAT_ID}-{MODE}"


def main() -> None:
    health = httpx.get(f"{BASE_URL}/api/health", timeout=10)
    health.raise_for_status()
    print("health:", health.json())

    parsed = parse_worksheet("sample_pdfs/Adverbs_of_frequency.pdf")

    generate_payload = {
        "chat_id": BASE_CHAT_ID,
        "learner_name": "Demo Student",
        "topic": "Adverbs of frequency",
        "worksheet_json": parsed["json"],
        "teacher_notes": parsed["reference"],
    }

    generated = httpx.post(
        f"{BASE_URL}/api/exercises/generate",
        json=generate_payload,
        timeout=REQUEST_TIMEOUT,
    )
    generated.raise_for_status()
    generated_json = generated.json()

    print("generate used_fallback:", generated_json.get("used_fallback"))
    print("generate warnings:", generated_json.get("warnings"))
    print("chat_id:", CHAT_ID)

    session = httpx.get(f"{BASE_URL}/api/chat/{CHAT_ID}/session", timeout=30)
    session.raise_for_status()
    session_json = session.json()

    assert session_json.get("instructions"), "missing session instructions"
    assert session_json.get("tasks"), "missing session tasks"
    print("session: ok")

    complete_payload = {
        "messages": [
            {"role": "persona", "content": "What are you cooking right now?"},
            {"role": "user", "content": "I am mixing the cake ingredients."},
            {"role": "persona", "content": "Great. What is your sister doing?"},
            {"role": "user", "content": "She is bake a cake."},
            {"role": "persona", "content": "Good try. Say: she is baking a cake."},
        ]
    }

    completed = httpx.post(
        f"{BASE_URL}/api/chat/{CHAT_ID}/complete",
        json=complete_payload,
        timeout=120,
    )
    completed.raise_for_status()
    assert completed.json().get("analysis"), "missing completion analysis"
    print("complete: ok")

    report = httpx.get(
        f"{BASE_URL}/api/chat/get-report",
        params={"chat_id": CHAT_ID},
        timeout=30,
    )
    report.raise_for_status()
    report_json = report.json()

    assert report_json.get("transcript"), "missing report transcript"
    assert report_json.get("homework_analysis"), "missing report analysis"
    print("report: ok")

    print("smoke backend: PASS")


if __name__ == "__main__":
    main()
