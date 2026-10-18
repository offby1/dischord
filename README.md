# Dischord

A Discord bot that plays chords.

@-mention the bot with chord names and it replies with an MP3 of them strummed:

    @Dischord Am F C G7
    @Dischord A5 | D5 | E5

`demo.mp3` is what the bot sends for the input `A5 D E A5`.

Understands `C`, `Cm`, `C7`, `Cmaj7`, `Cm7`, `Csus2`, `Csus4`, `Cdim`, `Caug`, `C5` (power chord),
`Cadd9`, `C9`, `Cm7b5`, slash chords like `D/F#`, and sharps/flats (`F#`, `Bb`). Chords can be
separated by spaces, commas or `|`. At most 16 per message. `@Dischord help` shows the syntax.

The bot needs no privileged intents (a message that mentions the bot includes its text) and only
needs these channel permissions: View Channels, Send Messages, Attach Files, Read Message History.

## Run

    uv venv && uv pip install -r requirements.txt   # or: pip install -r requirements.txt
    export DISCORD_TOKEN=...   # from the Bot tab of the Developer Portal; never commit it
    python bot.py

## Test

    uv pip install pytest && pytest

## Credits

`icon.svg` uses glyphs from the [Bravura](https://github.com/steinbergmedia/bravura) music font
(SIL Open Font License 1.1).
