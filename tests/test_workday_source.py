from types import SimpleNamespace

import pytest
import requests

from sources import fetch_workday_jobs, WORKDAY_MAX_JOBS, WORKDAY_PAGE_SIZE


def _company():
    return {"tenant": "acme", "site": "External", "host": "wd1"}


def _posting(i):
    return {
        "title": f"Graduate Software Engineer {i}",
        "externalPath": f"/job/London/Graduate-Software-Engineer_R{i}",
        "locationsText": "London, UK",
        "postedOn": "Posted 3 Days Ago",
    }


def test_fetch_workday_jobs_maps_fields_and_builds_link(monkeypatch):
    payload = {"total": 1, "jobPostings": [_posting(1)]}
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return SimpleNamespace(json=lambda: payload)

    monkeypatch.setattr("sources.requests.post", fake_post)

    jobs = fetch_workday_jobs(_company())

    assert captured["url"] == "https://acme.wd1.myworkdayjobs.com/wday/cxs/acme/External/jobs"
    assert captured["json"] == {"appliedFacets": {}, "limit": WORKDAY_PAGE_SIZE, "offset": 0, "searchText": ""}
    assert captured["headers"] == {"Accept": "application/json"}
    assert jobs == [
        {
            "title": "Graduate Software Engineer 1",
            "company": "acme",
            "location": "London, UK",
            "link": "https://acme.wd1.myworkdayjobs.com/External/job/London/Graduate-Software-Engineer_R1",
            "id": "/job/London/Graduate-Software-Engineer_R1",
        }
    ]


def test_fetch_workday_jobs_paginates_via_offset_until_total_reached(monkeypatch):
    # 45 postings total, page size 20 -> pages of 20, 20, 5.
    all_postings = [_posting(i) for i in range(45)]
    requested_offsets = []

    def fake_post(url, json=None, headers=None, timeout=None):
        offset = json["offset"]
        requested_offsets.append(offset)
        page = all_postings[offset:offset + WORKDAY_PAGE_SIZE]
        return SimpleNamespace(json=lambda: {"total": 45, "jobPostings": page})

    monkeypatch.setattr("sources.requests.post", fake_post)

    jobs = fetch_workday_jobs(_company())

    assert requested_offsets == [0, 20, 40]
    assert len(jobs) == 45


def test_fetch_workday_jobs_caps_at_max_jobs(monkeypatch):
    # An implausibly large `total` must not make the fetcher paginate forever.
    def fake_post(url, json=None, headers=None, timeout=None):
        offset = json["offset"]
        page = [_posting(offset + i) for i in range(WORKDAY_PAGE_SIZE)]
        return SimpleNamespace(json=lambda: {"total": 100000, "jobPostings": page})

    monkeypatch.setattr("sources.requests.post", fake_post)

    jobs = fetch_workday_jobs(_company())

    assert len(jobs) == WORKDAY_MAX_JOBS


def test_fetch_workday_jobs_skips_posting_missing_required_field(monkeypatch):
    good = _posting(1)
    malformed = {"title": "No externalPath here", "locationsText": "Remote"}
    payload = {"total": 2, "jobPostings": [malformed, good]}
    monkeypatch.setattr("sources.requests.post", lambda url, json=None, headers=None, timeout=None: SimpleNamespace(json=lambda: payload))

    jobs = fetch_workday_jobs(_company())

    assert len(jobs) == 1
    assert jobs[0]["id"] == "/job/London/Graduate-Software-Engineer_R1"


def test_fetch_workday_jobs_defaults_missing_location(monkeypatch):
    posting = {"title": "Graduate Software Engineer", "externalPath": "/job/R1"}
    payload = {"total": 1, "jobPostings": [posting]}
    monkeypatch.setattr("sources.requests.post", lambda url, json=None, headers=None, timeout=None: SimpleNamespace(json=lambda: payload))

    jobs = fetch_workday_jobs(_company())

    assert jobs[0]["location"] == ""


def test_fetch_workday_jobs_handles_network_error_without_raising(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr("sources.requests.post", fake_post)

    assert fetch_workday_jobs(_company()) == []


def test_fetch_workday_jobs_handles_invalid_json_without_raising(monkeypatch):
    def fake_post(url, json=None, headers=None, timeout=None):
        def raise_value_error():
            raise ValueError("not json")
        return SimpleNamespace(json=raise_value_error)

    monkeypatch.setattr("sources.requests.post", fake_post)

    assert fetch_workday_jobs(_company()) == []


def test_fetch_workday_jobs_handles_unexpected_response_shape(monkeypatch):
    # e.g. the endpoint returns a bare list or null instead of the expected object.
    monkeypatch.setattr("sources.requests.post", lambda url, json=None, headers=None, timeout=None: SimpleNamespace(json=lambda: ["not", "a", "dict"]))

    assert fetch_workday_jobs(_company()) == []


def test_fetch_workday_jobs_stops_on_empty_postings(monkeypatch):
    payload = {"total": 0, "jobPostings": []}
    calls = []

    def fake_post(url, json=None, headers=None, timeout=None):
        calls.append(json["offset"])
        return SimpleNamespace(json=lambda: payload)

    monkeypatch.setattr("sources.requests.post", fake_post)

    jobs = fetch_workday_jobs(_company())

    assert jobs == []
    assert calls == [0]
