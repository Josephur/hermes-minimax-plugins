# MiniMax TTS for Hermes Agent

This plugin adds MiniMax text-to-speech to Hermes through the TTS provider plugin interface.

The provider name is `minimax-tts`, not `minimax`, because Hermes already reserves `minimax` for its built-in TTS handler. Plugin providers cannot shadow built-in provider names.

## Install

From GitHub:

```bash
hermes plugins install owner/hermes-minimax-plugins/tts --enable
hermes plugins enable minimax-tts
```

Replace `owner` with the GitHub account or organization that hosts this repository.

Then select the provider:

```bash
hermes config set tts.provider minimax-tts
hermes config set tts.model speech-2.8-hd
hermes config set tts.voice English_Graceful_Lady
hermes config set tts.output_format mp3
```

The plugin requires `MINIMAX_API_KEY`. The installer should prompt for it because `plugin.yaml` declares it in `requires_env`. If you set it manually, put it in the Hermes env file shown by:

```bash
hermes config env-path
```

## Optional Settings

You can keep provider-specific settings in `config.yaml`:

```yaml
tts:
  provider: minimax-tts
  model: speech-2.8-hd
  voice: English_Graceful_Lady
  output_format: mp3
  minimax_tts:
    speed: 1.0
    vol: 1.0
    pitch: 0
    emotion: neutral
```

Environment overrides are also supported:

```text
MINIMAX_TTS_MODEL=speech-2.8-hd
MINIMAX_TTS_VOICE_ID=English_Graceful_Lady
MINIMAX_TTS_BASE_URL=https://api.minimax.io/v1/t2a_v2
MINIMAX_GROUP_ID=...
```

## Streaming

The plugin includes a `stream()` method using MiniMax WebSocket TTS. Current Hermes CLI voice mode does not call generic provider streams yet, so normal Hermes usage is file-based synthesis through `synthesize()`.

Streaming requires the optional Python package `websockets`. File-based synthesis only needs `requests`, which Hermes already uses.

MiniMax TTS has been confirmed working with API credits or a MiniMax Plus or better token plan.

## Notes

This plugin uses MiniMax system voices and cloned voice IDs if you provide one as `tts.voice`. It does not manage MiniMax voice cloning workflows.
