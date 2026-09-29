"""Locate tests use hand-made Word lists, so they test matching logic, not OCR."""
from sharesafe.locate import attach_boxes, merge
from sharesafe.ocr import Word
from sharesafe.rules import Finding


def w(text, left, line, top=100):
    return Word(text, left, top, 10 * len(text), 20, 95.0, line)


def f(text, source="rule"):
    return Finding(text, "x", "test", source)


def test_split_phone_gives_one_box():
    # OCR broke the number into three tokens; it should still be one box.
    words = [w("Call", 0, (1, 1, 1)), w("415.", 50, (1, 1, 1)), w("555.", 100, (1, 1, 1)), w("0198", 150, (1, 1, 1))]
    [found] = attach_boxes([f("415.555.0198")], words)
    assert len(found.boxes) == 1
    left, _, right, _ = found.boxes[0]
    assert left < 50 and right > 150 + 40  # covers all three pieces, not "Call"
    assert left > 0 + 40


def test_two_line_address_gives_two_boxes():
    words = [w("1200", 0, (1, 1, 1)), w("Miller", 50, (1, 1, 1)), w("Street,", 120, (1, 1, 1)),
             w("Springfield,", 0, (1, 2, 1), top=140), w("OR", 130, (1, 2, 1), top=140)]
    [found] = attach_boxes([f("1200 Miller Street, Springfield, OR", "llm")], words)
    assert len(found.boxes) == 2


def test_missing_text_gets_no_box():
    [found] = attach_boxes([f("not on the page")], [w("hello", 0, (1, 1, 1))])
    assert found.boxes == []


def test_repeated_text_is_boxed_everywhere():
    words = [w("a@example.com", 0, (1, 1, 1)), w("a@example.com", 0, (1, 2, 1), top=200)]
    [found] = attach_boxes([f("a@example.com")], words)
    assert len(found.boxes) == 2


def test_does_not_match_inside_other_numbers():
    # Found on samples/mixed.png: the SSN digits also appear inside a tracking
    # number once spaces are removed. Only the real SSN should be boxed.
    words = [w("1234", 0, (1, 1, 1)), w("5678", 50, (1, 1, 1)), w("9012", 100, (1, 1, 1)),
             w("123-45-6789", 0, (1, 2, 1), top=200)]
    [found] = attach_boxes([f("123-45-6789")], words)
    assert len(found.boxes) == 1
    assert found.boxes[0][1] > 150  # the box is on the SSN line, not the tracking line


def test_glued_prefix_still_found():
    # OCR sometimes glues a label onto the value; loose fallback still finds it.
    [found] = attach_boxes([f("jane@example.com")], [w("Email:jane@example.com", 0, (1, 1, 1))])
    assert len(found.boxes) == 1


def test_merge_prefers_rule_on_duplicate():
    merged = merge([f("415-555-0198")], [f("415 555 0198", "llm"), f("Jane Sample", "llm")])
    assert [x.source for x in merged] == ["rule", "llm"]
