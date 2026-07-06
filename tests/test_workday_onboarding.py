from types import SimpleNamespace

import bot


def _incoming(text):
    return {"result": [{"update_id": 1, "message": {"chat": {"id": 111}, "text": text}}]}


def test_workday_shorthand_added_when_valid(monkeypatch, isolated_db):
    monkeypatch.setattr(bot.requests, "get", lambda url, params=None: SimpleNamespace(json=lambda: _incoming("workday:acme:External")))
    monkeypatch.setattr(bot, "is_valid_workday_board", lambda tenant, site, host: True)
    sent = []
    monkeypatch.setattr(bot, "send_message", lambda chat_id, text: sent.append(text))

    bot.check_incoming_messages(0)

    assert "acme:External" in bot.get_companies()
    assert bot.get_company_ats("acme:External") == "workday"
    assert bot.get_company_workday_info("acme:External") == {
        "tenant": "acme", "site": "External", "host": bot.WORKDAY_DEFAULT_HOST,
    }
    assert "Workday" in sent[0]


def test_workday_url_added_with_parsed_host(monkeypatch, isolated_db):
    url = "https://acme.wd3.myworkdayjobs.com/External"
    monkeypatch.setattr(bot.requests, "get", lambda u, params=None: SimpleNamespace(json=lambda: _incoming(url)))
    monkeypatch.setattr(bot, "is_valid_workday_board", lambda tenant, site, host: True)
    sent = []
    monkeypatch.setattr(bot, "send_message", lambda chat_id, text: sent.append(text))

    bot.check_incoming_messages(0)

    assert bot.get_company_workday_info("acme:External") == {"tenant": "acme", "site": "External", "host": "wd3"}


def test_workday_not_found_replies_and_does_not_add(monkeypatch, isolated_db):
    monkeypatch.setattr(bot.requests, "get", lambda url, params=None: SimpleNamespace(json=lambda: _incoming("workday:acme:External")))
    monkeypatch.setattr(bot, "is_valid_workday_board", lambda tenant, site, host: False)
    sent = []
    monkeypatch.setattr(bot, "send_message", lambda chat_id, text: sent.append(text))

    bot.check_incoming_messages(0)

    assert "acme:External" not in bot.get_companies()
    assert "not found" in sent[0].lower()


def test_workday_input_never_probes_greenhouse_or_lever(monkeypatch, isolated_db):
    monkeypatch.setattr(bot.requests, "get", lambda url, params=None: SimpleNamespace(json=lambda: _incoming("workday:acme:External")))
    monkeypatch.setattr(bot, "is_valid_workday_board", lambda tenant, site, host: True)
    monkeypatch.setattr(bot, "is_valid_greenhouse_board", lambda slug: (_ for _ in ()).throw(AssertionError("Greenhouse should not be probed")))
    monkeypatch.setattr(bot, "is_valid_lever_board", lambda slug: (_ for _ in ()).throw(AssertionError("Lever should not be probed")))
    monkeypatch.setattr(bot, "send_message", lambda chat_id, text: None)

    bot.check_incoming_messages(0)  # must not raise

    assert bot.get_company_ats("acme:External") == "workday"


def test_bare_slug_still_routes_to_greenhouse_lever_detection(monkeypatch, isolated_db):
    # Regression guard: a plain slug like "acme" must not be misparsed as Workday.
    monkeypatch.setattr(bot.requests, "get", lambda url, params=None: SimpleNamespace(json=lambda: _incoming("acme")))
    monkeypatch.setattr(bot, "is_valid_greenhouse_board", lambda slug: True)
    sent = []
    monkeypatch.setattr(bot, "send_message", lambda chat_id, text: sent.append(text))

    bot.check_incoming_messages(0)

    assert bot.get_company_ats("acme") == "greenhouse"
    assert "Greenhouse" in sent[0]
