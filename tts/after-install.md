# MiniMax TTS Installed

Make sure the plugin is enabled, then select MiniMax TTS as your Hermes text-to-speech provider:

```bash
hermes plugins enable minimax-tts --no-allow-tool-override
```

```bash
hermes config set tts.provider minimax-tts
hermes config set tts.model speech-2.8-hd
hermes config set tts.voice English_Graceful_Lady
hermes config set tts.output_format mp3
```

The provider is named `minimax-tts` because Hermes reserves the built-in name `minimax`.

MiniMax TTS has been confirmed working with API credits or a MiniMax Plus or better token plan.
