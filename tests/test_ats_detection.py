from types import SimpleNamespace

import bot


def _incoming(text):
    return {"result": [{"update_id": 1, "message": {"chat": {"id": 111}, "text": text}}]}


def test_bare_slug_detected_as_greenhouse_when_greenhouse_responds(monkeypatch, isolated_db):
    monkeypatch.setattr(bot.requests, "get", lambda url, params=None: SimpleNamespace(json=lambda: _incoming("acme")))
    monkeypatch.setattr(bot, "is_valid_greenhouse_board", lambda slug: True)
    lever_calls = []
    monkeypatch.setattr(bot, "is_valid_lever_board", lambda slug: lever_calls.append(slug) or True)
    sent = []
    monkeypatch.setattr(bot, "send_message", lambda chat_id, text: sent.append(text))

    bot.check_incoming_messages(0)

    assert lever_calls == []  # Greenhouse matched first, so Lever is never probed
    assert bot.get_company_ats("acme") == "greenhouse"
    assert "Greenhouse" in sent[0]


def test_bare_slug_falls_back_to_lever_when_greenhouse_fails(monkeypatch, isolated_db):
    monkeypatch.setattr(bot.requests, "get", lambda url, params=None: SimpleNamespace(json=lambda: _incoming("acme")))
    monkeypatch.setattr(bot, "is_valid_greenhouse_board", lambda slug: False)
    monkeypatch.setattr(bot, "is_valid_lever_board", lambda slug: True)
    sent = []
    monkeypatch.setattr(bot, "send_message", lambda chat_id, text: sent.append(text))

    bot.check_incoming_messages(0)

    assert bot.get_company_ats("acme") == "lever"
    assert "Lever" in sent[0]


def test_bare_slug_not_found_on_either_ats(monkeypatch, isolated_db):
    monkeypatch.setattr(bot.requests, "get", lambda url, params=None: SimpleNamespace(json=lambda: _incoming("acme")))
    monkeypatch.setattr(bot, "is_valid_greenhouse_board", lambda slug: False)
    monkeypatch.setattr(bot, "is_valid_lever_board", lambda slug: False)
    sent = []
    monkeypatch.setattr(bot, "send_message", lambda chat_id, text: sent.append(text))

    bot.check_incoming_messages(0)

    assert "acme" not in bot.get_companies()
    assert "Board not found" in sent[0]


def test_explicit_greenhouse_url_skips_lever_probe_even_when_greenhouse_fails(monkeypatch, isolated_db):
    text = "https://boards-api.greenhouse.io/v1/boards/acme/jobs"
    monkeypatch.setattr(bot.requests, "get", lambda url, params=None: SimpleNamespace(json=lambda: _incoming(text)))
    monkeypatch.setattr(bot, "is_valid_greenhouse_board", lambda slug: False)
    lever_calls = []
    monkeypatch.setattr(bot, "is_valid_lever_board", lambda slug: lever_calls.append(slug) or True)
    sent = []
    monkeypatch.setattr(bot, "send_message", lambda chat_id, text: sent.append(text))

    bot.check_incoming_messages(0)

    assert lever_calls == []  # explicit Greenhouse URL: no ATS ambiguity to resolve
    assert "Board not found" in sent[0]
    assert "acme" not in bot.get_companies()
