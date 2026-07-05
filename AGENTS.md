# Hermes MiniMax Plugins

This repository contains standalone MiniMax plugins for Hermes Agent.

Do not modify Hermes Agent core files. Each plugin must stay installable through `hermes plugins install` from its own subdirectory.

Available plugins:

```text
image_gen/
tts/
```

The image generation plugin registers the Hermes image generation provider named `minimax`.

The TTS plugin registers the Hermes text-to-speech provider named `minimax-tts`. Do not rename it to `minimax`; Hermes reserves that built-in provider name and plugin registration will be ignored.

Install command shape:

```bash
hermes plugins install owner/hermes-minimax-plugins/image_gen --enable
hermes plugins install owner/hermes-minimax-plugins/tts --enable
hermes plugins enable minimax-tts --no-allow-tool-override
```

After installation, users should select the providers with:

```bash
hermes config set image_gen.provider minimax
hermes config set image_gen.model image-01
hermes config set image_gen.use_gateway false
hermes config set tts.provider minimax-tts
hermes config set tts.model speech-2.8-hd
hermes config set tts.voice English_Graceful_Lady
```

The plugins require `MINIMAX_API_KEY`. Keep credentials in Hermes `.env`; keep behavior settings in Hermes `config.yaml` via `hermes config set`.

Keep instructions cross-platform. Avoid absolute Windows-only or Linux-only paths except where documenting manual fallback installation.
