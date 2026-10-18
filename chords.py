"""Parse chord names (e.g. "Am7", "F#sus4", "C/G") into MIDI note numbers."""
import re

NOTE_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

_ROOT_RE = re.compile(r"^([A-G])([#b♯♭]?)(.*)$")
_BASS_RE = re.compile(r"^(.*?)/([A-G])([#b♯♭]?)$")

# One piece of a chord suffix, tried in this order (so "maj" wins over "m", "69" over "6").
_PIECE_RE = re.compile(
    r"maj|Maj|M|Δ|△"           # major (applies to a following 7, 9, 11 or 13)
    r"|min|m|-"                 # minor
    r"|dim|°|o|ø"               # diminished / half-diminished
    r"|aug|\+"                  # augmented
    r"|sus2|sus4|sus"
    r"|add(?:2|4|6|9|11|13)"
    r"|b5|#5|b9|#9|#11|b13"     # alterations
    r"|69|13|11|9|7|6|5|4|2"    # numbers
)


class ChordError(ValueError):
    pass


def _pitch_class(letter, accidental):
    pc = NOTE_SEMITONES[letter]
    if accidental in ("#", "♯"):
        pc += 1
    elif accidental in ("b", "♭"):
        pc -= 1
    return pc % 12


def _intervals(suffix):
    """Semitone intervals above the root for a chord suffix such as "m7b5" or "7sus2,13"."""
    suffix = suffix.replace("6/9", "69")
    for ch in "(),":
        suffix = suffix.replace(ch, "")
    third, fifth = 4, 7
    sus = None
    major = minor = dim = half_dim = False
    seventh = None   # 10 (minor/dominant), 11 (major), 9 (diminished)
    top = None       # highest stacked extension: 9, 11 or 13
    extras = set()
    power = False
    pos = 0
    while pos < len(suffix):
        m = _PIECE_RE.match(suffix, pos)
        if not m:
            raise ChordError(suffix)
        p, pos = m.group(), m.end()
        if p in ("maj", "Maj", "M", "Δ", "△"):
            major = True
        elif p in ("min", "m", "-"):
            minor = True
        elif p in ("dim", "°", "o"):
            dim = True
        elif p == "ø":
            half_dim = True
        elif p in ("aug", "+"):
            fifth = 8
        elif p.startswith("sus"):
            sus = 2 if p == "sus2" else 5
        elif p.startswith("add"):
            extras.add({"2": 2, "4": 5, "6": 9, "9": 14, "11": 17, "13": 21}[p[3:]])
        elif p in ("b5", "#5"):
            fifth = 6 if p == "b5" else 8
        elif p in ("b9", "#9", "#11", "b13"):
            extras.add({"b9": 13, "#9": 15, "#11": 18, "b13": 20}[p])
        elif p == "5":
            power = True
        elif p == "4" or p == "2":
            extras.add(5 if p == "4" else 2)
        elif p == "6":
            extras.add(9)
        elif p == "69":
            extras.update((9, 14))
        else:  # 7, 9, 11, 13
            seventh = 11 if major else 10
            top = int(p) if p != "7" else top
    if dim or half_dim:
        minor, fifth = True, 6
    if dim and seventh is not None:
        seventh = 9
    if half_dim and seventh is None:
        seventh = 10
    third = 3 if minor else 4
    if power:
        return {0, 7}
    intervals = {0, fifth}
    intervals.add(sus if sus is not None else third)
    if seventh is not None:
        intervals.add(seventh)
    if top:
        intervals.add(14)
        if top >= 11:
            intervals.add(17 if top == 11 else 21)
            if top == 11 and sus is None and not minor:
                intervals.discard(third)  # a dominant 11th clashes with the major third
    intervals |= extras
    return intervals


def parse_chord(token):
    """Return (root_pc, intervals, bass_pc or None) for a chord name."""
    bass = None
    body = token
    m = _BASS_RE.match(token)
    if m:
        body, bass = m.group(1), _pitch_class(m.group(2), m.group(3))
    m = _ROOT_RE.match(body)
    if not m:
        raise ChordError(token)
    letter, acc, suffix = m.groups()
    try:
        intervals = _intervals(suffix)
    except ChordError:
        raise ChordError(token) from None
    return _pitch_class(letter, acc), tuple(sorted(intervals)), bass


def voicing(token):
    """Return ascending MIDI notes for an open, guitar-like voicing of the chord.

    Like a real guitar chord, the low strings carry only the root and fifth; the
    remaining tones sit an octave or more up, since thirds and sevenths packed
    into the bass register sound muddy.
    """
    root, intervals, bass = parse_chord(token)
    root_note = 40 + (root - 40) % 12  # root in the low guitar range, E2..D#3
    notes = {root_note}
    if 11 not in intervals:  # a doubled root would sit a semitone above a major seventh
        notes.add(root_note + 12)
    fifths = [i for i in intervals if i in (6, 7, 8)]
    for i in intervals:
        if i in (0, 12):
            continue
        note = root_note + (i if i in fifths else 12 + i % 12)
        notes.add(note - 12 if note > 67 else note)
    if len(intervals) == 3 and 12 not in intervals and fifths:
        notes.add(root_note + 12 + fifths[0])  # triads: double the fifth on top
    if bass is not None:
        low = min(notes) - 1
        bass_note = low - (low - bass) % 12
        if bass_note < 40:
            bass_note += 12
        notes.add(bass_note)
    return sorted(notes)


_SEPARATORS = re.compile(r"[\s|;]+")
# A comma separates chords unless it is part of a chord name, as in "A7sus2,13".
_CHORD_COMMA = re.compile(r",(?=[A-G]|\s|$)")
_NOISE = re.compile(r"^[-–—>→=.·_]+$")


def split_tokens(text):
    text = _CHORD_COMMA.sub(" ", text)
    return [t for t in _SEPARATORS.split(text) if t and not _NOISE.match(t)]
