"""Rule tests use fixed strings, not images, so they check the regex logic alone."""
import pytest

from sharesafe.rules import find_rule_matches, luhn_ok


def found(text):
    return {(f.category, f.text) for f in find_rule_matches(text)}


def test_email():
    assert ("email", "jane.sample@example.com") in found("Email: jane.sample@example.com")


@pytest.mark.parametrize("phone", [
    "(206) 555-0142", "415-555-0198", "415.555.0198", "415 555 0198", "+1 415-555-0198",
])
def test_phone_formats(phone):
    assert ("phone", phone) in found(f"Call {phone} today")


def test_ssn():
    assert ("ssn", "123-45-6789") in found("SSN 123-45-6789")


def test_luhn():
    assert luhn_ok("4111 1111 1111 1111")
    assert not luhn_ok("4111 1111 1111 1112")


def test_test_card_is_flagged():
    assert ("card", "4111 1111 1111 1111") in found("Card: 4111 1111 1111 1111")


def test_digits_that_fail_luhn_are_not_cards():
    assert found("Card: 4111 1111 1111 1112") == set()


def test_order_number_is_not_flagged():
    # From the hard sample: looks like an account/card number but is neither.
    assert found("Order number: 4000-1234-5678") == set()


def test_ocr_misread_card_is_missed():
    # Real output from the blurry sample. Documents a known limitation:
    # once OCR garbles the digits, Luhn fails and the rule cannot catch it.
    assert found("Card 4999 1999 1999 1999") == set()


def test_plain_text_has_no_matches():
    assert found("Office closed Monday for maintenance.") == set()
