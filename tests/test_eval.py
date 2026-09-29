"""The eval is code too; a wrong scorer would give misleading numbers."""
from eval import score
from sharesafe.rules import Finding

EXPECTED = {
    "should_flag": [{"text": "Jane Sample", "category": "name"},
                    {"text": "jane.sample@example.com", "category": "email"}],
    "must_not_flag": [{"text": "4000-1234-5678"}],
}


def test_email_does_not_count_as_finding_the_name():
    email = Finding("jane.sample@example.com", "email", "r", "rule", boxes=[(0, 0, 1, 1)])
    rows, extras, traps = score(EXPECTED, [email])
    assert [r[0] for r in rows] == ["MISSED", "found"]
    assert extras == [] and traps == [("avoided", "4000-1234-5678")]


def test_unexpected_finding_is_extra_and_trap_is_hit():
    order = Finding("4000-1234-5678", "account_id", "r", "llm")
    _, extras, traps = score(EXPECTED, [order])
    assert extras == [order] and traps[0][0] == "TRAP HIT"
