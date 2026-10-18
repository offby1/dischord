import pytest

from bot import chords_from_message
from chords import ChordError, parse_chord, split_tokens, voicing
from synth import render_mp3


def pcs(token):
    return {n % 12 for n in voicing(token)}


def test_major_minor_seventh():
    assert pcs("C") == {0, 4, 7}
    assert pcs("Am") == {9, 0, 4}
    assert pcs("G7") == {7, 11, 2, 5}


def test_accidentals():
    assert parse_chord("Bb")[0] == 10
    assert parse_chord("F#m")[0] == 6


def test_power_chord_has_no_third():
    assert pcs("A5") == {9, 4}


def test_slash_chord_bass_is_lowest():
    notes = voicing("C/E")
    assert notes[0] % 12 == 4 and min(notes) == notes[0]


def test_rejects_non_chords():
    for bad in ["hello", "H", "Cxyz", "a", "C/", "bad"]:
        with pytest.raises(ChordError):
            parse_chord(bad)


def test_split_and_message():
    assert split_tokens("Am | F, C -> G7") == ["Am", "F", "C", "G7"]
    assert chords_from_message("<@123> Am F C G7") == (["Am", "F", "C", "G7"], [])
    assert chords_from_message("<@!123> Am hello") == (["Am"], ["hello"])


def test_mp3_is_produced():
    data = render_mp3(["A5", "D"])
    assert len(data) > 10_000
    assert data[:3] == b"ID3" or data[0] == 0xFF


def test_help_request():
    from bot import HELP, MAX_CHORDS, SHORT_HELP, is_help_request
    assert is_help_request("<@1> help")
    assert is_help_request("<@!1>  Help?")
    assert is_help_request("<@1> ?")
    assert not is_help_request("<@1> Am F C")
    assert not is_help_request("<@1>")
    text = HELP.format(name="ChordBot", max=MAX_CHORDS)
    assert len(text) < 2000  # Discord's message limit
    assert "{" not in text and "D/F#" in text
    assert "ChordBot help" in SHORT_HELP.format(name="ChordBot")


def intervals(token):
    return set(parse_chord(token)[1])


def test_extended_chord_names():
    assert intervals("C6/9") == {0, 4, 7, 9, 14}
    assert intervals("C7#11") == {0, 4, 7, 10, 18}
    assert intervals("A7sus2,13") == {0, 2, 7, 10, 14, 21}
    assert intervals("Cm(maj7)") == {0, 3, 7, 11}
    assert intervals("E7(b9)") == {0, 4, 7, 10, 13}
    assert intervals("Cdim7") == {0, 3, 6, 9}
    assert intervals("Bm7b5") == {0, 3, 6, 10}
    assert parse_chord("C7#11/F#")[2] == 6
    assert parse_chord("Fmaj7/G")[2] == 7


def test_comma_inside_chord_name():
    assert split_tokens("Cmaj7 A7sus2,13 C7#11/F# Fmaj7/G C6/9") == [
        "Cmaj7", "A7sus2,13", "C7#11/F#", "Fmaj7/G", "C6/9"]
    assert split_tokens("Am,F,C,G7") == ["Am", "F", "C", "G7"]


def test_scale_degrees_are_rejected():
    chords, bad = chords_from_message("<@1> b3 b1 b7 b6 #4 5 6 7 1 2 #2 3")
    assert chords == [] and len(bad) == 12


def test_every_extended_chord_renders():
    assert len(render_mp3(["Cmaj7", "A7sus2,13", "C7#11/F#", "Fmaj7/G", "C6/9"])) > 10_000
