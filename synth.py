"""Render a chord progression to MP3 with a plucked-string (Karplus-Strong) model."""
import numpy as np
import lameenc

from chords import voicing

SAMPLE_RATE = 44100
STRUM_DELAY = 0.03   # seconds between successive strings in a strum
CHORD_SECONDS = 1.5  # time from one chord's strum to the next
TAIL_SECONDS = 1.5   # let the last chord ring out
DECAY = 0.996
RELEASE_SECONDS = 0.05  # how quickly a chord is damped when the next one is strummed


def _pluck(freq, seconds, rng):
    period = int(round(SAMPLE_RATE / freq))
    length = int(seconds * SAMPLE_RATE)
    y = np.zeros(length + 1)  # y[0] stays 0 so y[n - period - 1] is always valid
    noise = rng.uniform(-1, 1, period)
    noise = (noise + np.roll(noise, 1)) / 2  # soften the pick attack
    y[1:period + 1] = noise
    for n in range(period + 1, length + 1, period):
        m = min(period, length + 1 - n)
        y[n:n + m] = DECAY * 0.5 * (y[n - period:n - period + m] + y[n - period - 1:n - period - 1 + m])
    return y[1:]


def render_wav(chord_names):
    rng = np.random.default_rng(0)
    total = int((CHORD_SECONDS * len(chord_names) + TAIL_SECONDS) * SAMPLE_RATE)
    mix = np.zeros(total)
    for i, name in enumerate(chord_names):
        start = int(i * CHORD_SECONDS * SAMPLE_RATE)
        for j, note in enumerate(voicing(name)):
            freq = 440.0 * 2 ** ((note - 69) / 12)
            offset = start + int(j * STRUM_DELAY * SAMPLE_RATE)
            last = i == len(chord_names) - 1
            # Damp each chord as the next one starts so their notes don't ring together and clash.
            ring = CHORD_SECONDS + TAIL_SECONDS if last else CHORD_SECONDS - j * STRUM_DELAY + RELEASE_SECONDS
            tone = _pluck(freq, ring, rng)
            if not last:
                release = int(RELEASE_SECONDS * SAMPLE_RATE)
                tone[-release:] *= np.linspace(1, 0, release)
            end = min(total, offset + len(tone))
            mix[offset:end] += tone[:end - offset]
    mix /= max(np.abs(mix).max(), 1e-9)
    fade = int(0.05 * SAMPLE_RATE)
    mix[-fade:] *= np.linspace(1, 0, fade)
    return (mix * 0.8 * 32767).astype(np.int16)


def render_mp3(chord_names):
    pcm = render_wav(chord_names)
    enc = lameenc.Encoder()
    enc.set_bit_rate(128)
    enc.set_in_sample_rate(SAMPLE_RATE)
    enc.set_channels(1)
    enc.set_quality(2)
    return bytes(enc.encode(pcm.tobytes()) + enc.flush())
