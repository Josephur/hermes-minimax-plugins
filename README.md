# Hermes MiniMax Plugins

Standalone MiniMax provider plugins for Hermes Agent.

This repository is organized by plugin category. The current plugins are:

```text
image_gen/
tts/
```

`image_gen` adds MiniMax `image-01` support to Hermes image generation without modifying Hermes Agent source code.

`tts` adds MiniMax text-to-speech support through the Hermes TTS provider plugin interface.

## Install Image Generation Plugin

Use the plugin subdirectory when installing from GitHub:

```bash
hermes plugins install owner/hermes-minimax-plugins/image_gen --enable
```

Replace `owner` with the GitHub account or organization that hosts this repository.

After install, select MiniMax as the image generation provider:

```bash
hermes config set image_gen.provider minimax
hermes config set image_gen.model image-01
hermes config set image_gen.use_gateway false
```

The install command should prompt for `MINIMAX_API_KEY` because the plugin manifest declares it as required. If you set it manually, put it in the Hermes env file shown by:

```bash
hermes config env-path
```

This works on Windows, Linux, and macOS as long as `hermes` is on PATH.

## Install Text-to-Speech Plugin

Use the plugin subdirectory when installing from GitHub:

```bash
hermes plugins install owner/hermes-minimax-plugins/tts --enable
```

Replace `owner` with the GitHub account or organization that hosts this repository.

After install, select MiniMax as the text-to-speech provider:

```bash
hermes config set tts.provider minimax-tts
hermes config set tts.model speech-2.8-hd
hermes config set tts.voice English_expressive_narrator
hermes config set tts.output_format mp3
```

The TTS provider is named `minimax-tts` because Hermes reserves the built-in provider name `minimax`.

MiniMax TTS has been confirmed working with API credits or a MiniMax Plus or better token plan.

## Repository Layout

```text
hermes-minimax-plugins/
  README.md
  AGENTS.md
  image_gen/
    plugin.yaml
    __init__.py
    README.md
    after-install.md
  tts/
    plugin.yaml
    __init__.py
    README.md
    after-install.md
```

Future MiniMax plugins should be added as sibling folders at the repository root.
