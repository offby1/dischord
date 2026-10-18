# Dischord

A Discord bot that plays chords.

@-mention the bot with chord names and it replies with an MP3 of them strummed:

    @Dischord Am F C G7
    @Dischord A5 | D5 | E5

`demo.mp3` is what the bot sends for the input `A5 D E A5`.

Understands major/minor/dim/aug/sus chords, power chords (`A5`), sixths, sevenths, ninths, elevenths and thirteenths,
`6/9`, `add9`, alterations such as `b5`, `#11` and `b9` (for example `Cmaj7`, `A7sus2,13`, `C7#11/F#`, `E7(b9)`),
`Cadd9`, `C9`, `Cm7b5`, slash chords like `D/F#`, and sharps/flats (`F#`, `Bb`). Chords can be
separated by spaces, commas or `|`. At most 16 per message. `@Dischord help` shows the syntax.

The bot needs no privileged intents (a message that mentions the bot includes its text) and only
needs these channel permissions: View Channels, Send Messages, Attach Files, Read Message History.

## Run

    uv venv && uv pip install -r requirements.txt   # or: pip install -r requirements.txt
    export DISCORD_TOKEN=...   # from the Bot tab of the Developer Portal; never commit it
    python bot.py

## Run with Docker

    echo 'DISCORD_TOKEN=...' > .env && chmod 600 .env   # never commit this; it is in .gitignore
    docker compose up -d --build
    docker compose logs -f

To update after a `git pull`, run `docker compose up -d --build` again. The container needs no
published ports (it only makes an outbound connection to Discord), restarts itself unless stopped,
runs as a non-root user with a read-only filesystem, and is capped at 256 MB of memory.

## Test

    uv pip install pytest && pytest

## Credits

`icon.svg` uses glyphs from the [Bravura](https://github.com/steinbergmedia/bravura) music font
(SIL Open Font License 1.1).
