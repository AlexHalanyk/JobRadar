import pytest

from bot import extract_workday_company, WORKDAY_DEFAULT_HOST


@pytest.mark.parametrize("text,expected", [
    ("workday:acme:External", {"tenant": "acme", "host": WORKDAY_DEFAULT_HOST, "site": "External"}),
    ("workday:acme-corp:Careers_Site", {"tenant": "acme-corp", "host": WORKDAY_DEFAULT_HOST, "site": "Careers_Site"}),
])
def test_shorthand_format_defaults_to_wd1(text, expected):
    assert extract_workday_company(text) == expected


@pytest.mark.parametrize("text,expected", [
    (
        "https://acme.wd1.myworkdayjobs.com/External",
        {"tenant": "acme", "host": "wd1", "site": "External"},
    ),
    (
        "https://acme.wd3.myworkdayjobs.com/External",
        {"tenant": "acme", "host": "wd3", "site": "External"},
    ),
    (
        "https://acme.wd5.myworkdayjobs.com/en-US/External",
        {"tenant": "acme", "host": "wd5", "site": "External"},
    ),
    (
        "https://acme.wd1.myworkdayjobs.com/External/job/London/Graduate-Engineer_R123",
        {"tenant": "acme", "host": "wd1", "site": "External"},
    ),
])
def test_url_format_extracts_tenant_host_and_site(text, expected):
    assert extract_workday_company(text) == expected


@pytest.mark.parametrize("text", [
    "monzo",
    "https://boards-api.greenhouse.io/v1/boards/monzo/jobs",
    "hello world",
    "",
    "/start",
    "workday:acme",  # missing site
    "workday::External",  # missing tenant
])
def test_non_workday_input_returns_none(text):
    assert extract_workday_company(text) is None
