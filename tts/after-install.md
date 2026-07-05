# MiniMax TTS Installed

Select MiniMax TTS as your Hermes text-to-speech provider:

```bash
hermes config set tts.provider minimax-tts
hermes config set tts.model speech-2.8-hd
hermes config set tts.voice English_expressive_narrator
hermes config set tts.output_format mp3
```

The provider is named `minimax-tts` because Hermes reserves the built-in name `minimax`.

MiniMax TTS has been confirmed working with API credits or a MiniMax Plus or better token plan.
