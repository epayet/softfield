from runner.i18n import catalogue_problems, parse_po

PO = """\
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Send"
msgstr "Envoyer"

msgid "Waiting to deliver"
msgstr ""

#, fuzzy
msgid "Thinking of you"
msgstr "Je pense à vous"

msgctxt "reaction"
msgid "Love"
msgstr "J'adore"

msgid ""
"A long line "
"split in two"
msgstr ""
"Une longue ligne "
"coupée en deux"

msgid "%(n)s moment"
msgid_plural "%(n)s moments"
msgstr[0] "%(n)s moment"
msgstr[1] ""
"""


def test_parse_po():
    entries = {e.msgid: e for e in parse_po(PO)}
    assert set(entries) == {
        "Send",
        "Waiting to deliver",
        "Thinking of you",
        "Love",
        "A long line split in two",
        "%(n)s moment",
    }
    assert entries["Send"].translated and not entries["Send"].fuzzy
    assert not entries["Waiting to deliver"].translated
    assert entries["Thinking of you"].fuzzy
    assert entries["A long line split in two"].translated
    assert not entries["%(n)s moment"].translated  # one plural form is missing


def test_catalogue_problems():
    assert catalogue_problems(PO, "fr") == [
        "fr: missing French translation: 'Waiting to deliver'",
        "fr: fuzzy translation needs checking: 'Thinking of you'",
        "fr: missing French translation: '%(n)s moment'",
    ]
