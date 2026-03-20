from app import build_ui, parse_and_store_worksheet


def test_build_ui_returns_blocks():
    demo = build_ui()
    assert demo is not None


def test_parse_and_store_worksheet_returns_preview_and_state(monkeypatch):
    monkeypatch.setattr("app.parse_worksheet", lambda _: "parsed worksheet text")

    preview, state = parse_and_store_worksheet("fake.pdf")

    assert preview == "parsed worksheet text"
    assert state == "parsed worksheet text"
