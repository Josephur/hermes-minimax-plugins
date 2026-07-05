# MiniMax Music Generation for Hermes

This backend registers the `minimax` provider for Hermes Music Generation.

Music Generation is not yet a stock Hermes category. Until upstream Hermes ships it, apply the compatibility patch in `../core_patch` first.

## Install

```bash
hermes plugins install owner/hermes-minimax-plugins/music_gen/minimax --enable
hermes plugins enable minimax-music --no-allow-tool-override
```

Then configure:

```bash
hermes config set music_gen.provider minimax
hermes config set music_gen.model music-2.6-free
```

The plugin requires `MINIMAX_API_KEY` in the Hermes env file shown by:

```bash
hermes config env-path
```

## Models

- `music-2.6-free` - free original music model, default
- `music-2.6` - paid original music model
- `music-cover-free` - free cover model, requires `reference_audio_url`
- `music-cover` - paid cover model, requires `reference_audio_url`

## Usage

Ask Hermes for music after enabling the `music_gen` toolset, for example:

```text
Generate an instrumental lo-fi hip-hop track with warm vinyl texture and soft piano.
```

The tool returns `MEDIA:<local_path>` for the downloaded MP3.

