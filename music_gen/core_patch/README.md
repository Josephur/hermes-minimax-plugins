# Music Generation Core Patch

This patch adds the temporary Hermes core category needed by `music_gen/minimax`:

- `agent/music_gen_provider.py`
- `agent/music_gen_registry.py`
- `tools/music_generation_tool.py`
- `toolsets.py` entry for `music_gen`
- `PluginContext.register_music_gen_provider`
- `hermes tools` provider picker glue

The scripts are placeholders in this first implementation pass. They currently perform checks and explain the manual copy/edit steps. The provider, registry, and tool files in this folder are ready to copy into a Hermes install.

## Manual Apply

From this directory, copy:

```text
agent/music_gen_provider.py -> <hermes-agent>/agent/music_gen_provider.py
agent/music_gen_registry.py -> <hermes-agent>/agent/music_gen_registry.py
tools/music_generation_tool.py -> <hermes-agent>/tools/music_generation_tool.py
```

Then apply the snippets:

- `toolsets.py.snippet`
- `hermes_cli/plugins.py.snippet`
- `hermes_cli/tools_config.py.snippet`

Restart Hermes after patching.
