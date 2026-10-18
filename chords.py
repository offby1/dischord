"""Parse chord names (e.g. "Am7", "F#sus4", "C/G") into MIDI note numbers."""
import re

NOTE_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# quality suffix -> semitone intervals above the root
QUALITIES = {
    "": (0, 4, 7),
    "m": (0, 3, 7),
    "min": (0, 3, 7),
    "-": (0, 3, 7),
    "maj": (0, 4, 7),
    "M": (0, 4, 7),
    "5": (0, 7, 12),
    "6": (0, 4, 7, 9),
    "m6": (0, 3, 7, 9),
    "7": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11),
    "M7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10),
    "min7": (0, 3, 7, 10),
    "mmaj7": (0, 3, 7, 11),
    "dim": (0, 3, 6),
    "dim7": (0, 3, 6, 9),
    "m7b5": (0, 3, 6, 10),
    "aug": (0, 4, 8),
    "+": (0, 4, 8),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "sus": (0, 5, 7),
    "7sus4": (0, 5, 7, 10),
    "add9": (0, 4, 7, 14),
    "madd9": (0, 3, 7, 14),
    "9": (0, 4, 7, 10, 14),
    "m9": (0, 3, 7, 10, 14),
    "maj9": (0, 4, 7, 11, 14),
}

_CHORD_RE = re.compile(r"^([A-Ga-g])([#b♯♭]?)([^/]*)(?:/([A-Ga-g])([#b♯♭]?))?$")


class ChordError(ValueError):
    pass


def _pitch_class(letter, accidental):
    pc = NOTE_SEMITONES[letter.upper()]
    if accidental in ("#", "♯"):
        pc += 1
    elif accidental in ("b", "♭"):
        pc -= 1
    return pc % 12


def parse_chord(token):
    """Return (root_pc, intervals, bass_pc or None) for a chord name."""
    m = _CHORD_RE.match(token)
    if not m:
        raise ChordError(token)
    letter, acc, quality, bass_letter, bass_acc = m.groups()
    # Only an uppercase letter starts a chord, so "a" or "bad" aren't read as chords.
    if letter.islower():
        raise ChordError(token)
    if quality not in QUALITIES:
        raise ChordError(token)
    root = _pitch_class(letter, acc)
    bass = _pitch_class(bass_letter, bass_acc) if bass_letter else None
    return root, QUALITIES[quality], bass


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


_SEPARATORS = re.compile(r"[\s,|;]+")
_NOISE = re.compile(r"^[-–—>→=.·_]+$")


def split_tokens(text):
    return [t for t in _SEPARATORS.split(text) if t and not _NOISE.match(t)]
