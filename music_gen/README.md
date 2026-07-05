# Hermes Music Generation Plugins

This folder contains Music Generation backends for Hermes Agent.

Current backend:

```text
minimax/
```

Music Generation is a new Hermes category. Until Hermes core ships `music_gen`, apply the compatibility patch in `core_patch/` to your local Hermes install before installing the backend.

## Windows Quick Start

```powershell
cd D:\hermes-minimax-plugins\music_gen\core_patch
.\apply_patch.ps1 --check
.\apply_patch.ps1 --apply
hermes plugins install owner/hermes-minimax-plugins/music_gen/minimax --enable
hermes plugins enable music_gen/minimax --no-allow-tool-override
hermes config set music_gen.provider minimax
hermes config set music_gen.model music-2.6-free
```

## Linux/macOS/WSL Quick Start

```bash
cd ~/hermes-minimax-plugins/music_gen/core_patch
./apply_patch.sh --check
./apply_patch.sh --apply
hermes plugins install owner/hermes-minimax-plugins/music_gen/minimax --enable
hermes plugins enable music_gen/minimax --no-allow-tool-override
hermes config set music_gen.provider minimax
hermes config set music_gen.model music-2.6-free
```

Set `MINIMAX_API_KEY` in the Hermes env file shown by `hermes config env-path`.
