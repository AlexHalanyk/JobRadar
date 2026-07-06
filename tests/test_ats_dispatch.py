import bot
import main


def _job(link, title="Graduate Software Engineer"):
    return {
        "title": title,
        "company": "Acme",
        "location": "London",
        "link": link,
        "id": link,
    }


def test_check_jobs_dispatches_greenhouse_company_to_greenhouse_fetcher(monkeypatch, isolated_db):
    bot.add_company("acme", "greenhouse")
    monkeypatch.setattr(main, "LLM_BACKEND", "gemini")
    monkeypatch.setattr(main, "is_relevant_ai", lambda j, profile: True)
    monkeypatch.setattr(main, "send_notification", lambda job, chat_ids: None)

    greenhouse_calls = []
    lever_calls = []
    monkeypatch.setattr(main, "fetch_greenhouse_jobs", lambda slug: greenhouse_calls.append(slug) or [_job("https://example.com/gh/1")])
    monkeypatch.setattr(main, "fetch_lever_jobs", lambda slug: lever_calls.append(slug) or [])

    main.check_jobs()

    assert greenhouse_calls == ["acme"]
    assert lever_calls == []


def test_check_jobs_dispatches_lever_company_to_lever_fetcher(monkeypatch, isolated_db):
    bot.add_company("acme", "lever")
    monkeypatch.setattr(main, "LLM_BACKEND", "gemini")
    monkeypatch.setattr(main, "is_relevant_ai", lambda j, profile: True)
    monkeypatch.setattr(main, "send_notification", lambda job, chat_ids: None)

    greenhouse_calls = []
    lever_calls = []
    monkeypatch.setattr(main, "fetch_greenhouse_jobs", lambda slug: greenhouse_calls.append(slug) or [])
    monkeypatch.setattr(main, "fetch_lever_jobs", lambda slug: lever_calls.append(slug) or [_job("https://example.com/lv/1")])

    main.check_jobs()

    assert lever_calls == ["acme"]
    assert greenhouse_calls == []


def test_check_jobs_dispatches_multiple_companies_by_their_own_ats(monkeypatch, isolated_db):
    bot.add_company("greenhouse-co", "greenhouse")
    bot.add_company("lever-co", "lever")
    monkeypatch.setattr(main, "LLM_BACKEND", "gemini")
    monkeypatch.setattr(main, "is_relevant_ai", lambda j, profile: True)
    monkeypatch.setattr(main, "send_notification", lambda job, chat_ids: None)

    monkeypatch.setattr(main, "fetch_greenhouse_jobs", lambda slug: [_job("https://example.com/gh/1")] if slug == "greenhouse-co" else [])
    monkeypatch.setattr(main, "fetch_lever_jobs", lambda slug: [_job("https://example.com/lv/1")] if slug == "lever-co" else [])

    main.check_jobs()

    assert bot.already_sent("https://example.com/gh/1") is True
    assert bot.already_sent("https://example.com/lv/1") is True


def test_company_without_stored_ats_defaults_to_greenhouse(monkeypatch, isolated_db):
    # No add_company call at all: mirrors legacy pre-migration companies
    # that only ever had a slug, never an ats value.
    monkeypatch.setattr(main, "get_companies", lambda: ["legacy-co"])
    monkeypatch.setattr(main, "LLM_BACKEND", "gemini")
    monkeypatch.setattr(main, "is_relevant_ai", lambda j, profile: True)
    monkeypatch.setattr(main, "send_notification", lambda job, chat_ids: None)

    greenhouse_calls = []
    monkeypatch.setattr(main, "fetch_greenhouse_jobs", lambda slug: greenhouse_calls.append(slug) or [])
    monkeypatch.setattr(main, "fetch_lever_jobs", lambda slug: (_ for _ in ()).throw(AssertionError("should not call Lever")))

    main.check_jobs()

    assert greenhouse_calls == ["legacy-co"]


def test_check_jobs_dispatches_workday_company_to_workday_fetcher(monkeypatch, isolated_db):
    bot.add_company("acme:External", "workday", tenant="acme", site="External", host="wd3")
    monkeypatch.setattr(main, "LLM_BACKEND", "gemini")
    monkeypatch.setattr(main, "is_relevant_ai", lambda j, profile: True)
    monkeypatch.setattr(main, "send_notification", lambda job, chat_ids: None)

    workday_calls = []
    monkeypatch.setattr(main, "fetch_greenhouse_jobs", lambda slug: (_ for _ in ()).throw(AssertionError("should not call Greenhouse")))
    monkeypatch.setattr(main, "fetch_lever_jobs", lambda slug: (_ for _ in ()).throw(AssertionError("should not call Lever")))
    monkeypatch.setattr(main, "fetch_workday_jobs", lambda company: workday_calls.append(company) or [_job("https://example.com/wd/1")])

    main.check_jobs()

    assert workday_calls == [{"tenant": "acme", "site": "External", "host": "wd3"}]
    assert bot.already_sent("https://example.com/wd/1") is True


def test_check_jobs_skips_workday_company_missing_stored_details(monkeypatch, isolated_db):
    # Defensive path: a workday-tagged row somehow missing tenant/site/host
    # (e.g. partial write) must be skipped, not crash the cycle.
    monkeypatch.setattr(main, "get_companies", lambda: ["broken-workday-co"])
    monkeypatch.setattr(main, "get_company_ats", lambda slug: "workday")
    monkeypatch.setattr(main, "get_company_workday_info", lambda slug: None)
    monkeypatch.setattr(main, "LLM_BACKEND", "gemini")
    monkeypatch.setattr(main, "fetch_workday_jobs", lambda company: (_ for _ in ()).throw(AssertionError("should not be called")))

    main.check_jobs()  # must not raise
