"""Discord bot: @-mention it with chord names and it replies with an MP3 of them strummed."""
import asyncio
import io
import os
import re

import discord

from chords import ChordError, parse_chord, split_tokens
from synth import render_mp3

MAX_CHORDS = 16
SHORT_HELP = "Mention me with some chords, e.g. `@{name} Am F C G7`. Say `@{name} help` for the full syntax."

HELP = """**Chord bot**
Mention me with some chords and I'll reply with an MP3 of them strummed, one chord about every 1.5 seconds.
Example: `@{name} Am F C G7`

**Chord syntax**
\u2022 A chord is a **capital letter A-G**, an optional `#` or `b`, then optional parts: `C`, `F#`, `Bb`
\u2022 Quality: `m` (minor), `maj`, `dim`, `aug` (or `+`), `sus2`, `sus4` -- e.g. `Am`, `Dsus4`, `Bdim`
\u2022 Numbers: `5` (power chord, root and fifth only), `6`, `7`, `9`, `11`, `13`, `6/9` -- e.g. `A5`, `G7`, `Cmaj7`, `Em9`
\u2022 Extras: `add9`, `add11`, and alterations `b5 #5 b9 #9 #11 b13` -- e.g. `Cadd9`, `Bm7b5`, `C7#11`, `E7(b9)`
\u2022 Slash chords put a different note in the bass: `D/F#`, `C7#11/F#`
\u2022 Separate chords with spaces, commas or `|` -- `Am | F | C | G7` works fine
\u2022 I know chord names only, not scale degrees or Nashville numbers like `1 4 5`.

More about how chord names work: <https://en.wikipedia.org/wiki/Chord_notation> (I understand the common ones, not every symbol on that page).

**Tips**
\u2022 Repeat a chord to strum it again: `A5 A5 D5 E5`
\u2022 Up to {max} chords per message.
\u2022 Chords are voiced like open guitar chords, so `E` sounds like the open E shape.
\u2022 If I don't understand something, I'll tell you which word tripped me up.
\u2022 I only listen when I'm mentioned, and ignore everything else."""

_DEGREE = re.compile(r"^[b#]?\d+$")
_MENTION = re.compile(r"<@[!&]?\d+>")


def is_help_request(content):
    tokens = split_tokens(_MENTION.sub(" ", content))
    return bool(tokens) and tokens[0].lower().strip("?!.") in ("help", "h", "usage", "syntax") or tokens == ["?"]


def chords_from_message(content):
    """Return (chords, bad_tokens) from the text of a message, with mentions removed."""
    tokens = split_tokens(_MENTION.sub(" ", content))
    chords, bad = [], []
    for tok in tokens:
        try:
            parse_chord(tok)
            chords.append(tok)
        except ChordError:
            bad.append(tok)
    return chords, bad


intents = discord.Intents.default()  # no privileged intents: mentions still carry their text
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author.bot or client.user not in message.mentions:
        return
    if is_help_request(message.content):
        await message.reply(HELP.format(name=client.user.name, max=MAX_CHORDS), mention_author=False)
        return
    chords, bad = chords_from_message(message.content)
    if bad:
        shown = ", ".join(f"`{t[:20]}`" for t in bad[:5])
        note = " Those look like scale degrees, but I only know chord names." if all(_DEGREE.match(t) for t in bad) else ""
        await message.reply(f"I couldn't read {shown} as a chord.{note} " + SHORT_HELP.format(name=client.user.name),
                            mention_author=False)
        return
    if not chords:
        await message.reply(SHORT_HELP.format(name=client.user.name), mention_author=False)
        return
    if len(chords) > MAX_CHORDS:
        await message.reply(f"That's a lot of chords! I'll do at most {MAX_CHORDS} at a time.",
                            mention_author=False)
        return
    async with message.channel.typing():
        mp3 = await asyncio.to_thread(render_mp3, chords)
    await message.reply(file=discord.File(io.BytesIO(mp3), filename="chords.mp3"), mention_author=False)


if __name__ == "__main__":
    client.run(os.environ["DISCORD_TOKEN"])
