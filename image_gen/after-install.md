# MiniMax Image Generation Installed

Select MiniMax as the Hermes image generation provider:

```bash
hermes config set image_gen.provider minimax
hermes config set image_gen.model image-01
hermes config set image_gen.use_gateway false
```

If Hermes asks whether this plugin should be allowed to override tools, answer no. This plugin registers an image generation provider and does not need tool override privileges.

The plugin requires `MINIMAX_API_KEY`. If you did not enter it during install, add it to the Hermes env file shown by:

```bash
hermes config env-path
```
