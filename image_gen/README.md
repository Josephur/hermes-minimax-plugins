# Hermes MiniMax Image Generation Plugin

This folder is the `image_gen` plugin subdirectory for the `hermes-minimax-plugins` repository. It adds MiniMax image generation support to Hermes Agent without modifying the Hermes source tree.

The provider uses MiniMax `image-01` through `https://api.minimax.io/v1/image_generation`.

Supported Hermes modes:

- Text-only `image_generate` calls use MiniMax text-to-image.
- Calls with `image_url` or `reference_image_urls` use MiniMax reference-image generation through `subject_reference`.
- MiniMax supports one reference image per request; this plugin returns a clear error if more than one is supplied.

## Confirmed Access

This plugin has been confirmed working with MiniMax API credits. It should also work with MiniMax Plus or a higher token plan that includes access to the MiniMax image generation API.

## GitHub Install

From the repository root layout, install this plugin subdirectory with:

```bash
hermes plugins install owner/hermes-minimax-plugins/image_gen --enable
```

Replace `owner` with the GitHub account or organization that hosts the repository. This command works on Windows, Linux, and macOS when `hermes` is on PATH.

The install command should prompt for `MINIMAX_API_KEY` because `plugin.yaml` declares it as required. If you set the key manually, put it in the Hermes env file shown by:

```bash
hermes config env-path
```

Then select the provider:

```bash
hermes config set image_gen.provider minimax
hermes config set image_gen.model image-01
hermes config set image_gen.use_gateway false
```

When asked whether to allow tool override privileges, answer no. This plugin does not need to override built-in tools.

## Manual Windows Install

Open PowerShell and find your Hermes config path:

```powershell
hermes config path
hermes config env-path
```

For the standard Windows installer, the Hermes home is usually:

```text
%LOCALAPPDATA%\hermes
```

Create the plugin folder:

```powershell
New-Item -ItemType Directory -Force "$env:LOCALAPPDATA\hermes\plugins\image_gen\minimax"
```

Copy these files into it:

```text
%LOCALAPPDATA%\hermes\plugins\image_gen\minimax\plugin.yaml
%LOCALAPPDATA%\hermes\plugins\image_gen\minimax\__init__.py
```

If `hermes config path` points somewhere else, use that config file's parent directory as the Hermes home, then create:

```text
<hermes-home>\plugins\image_gen\minimax\
```

Enable and select the provider:

```powershell
hermes plugins enable image_gen/minimax
hermes config set image_gen.provider minimax
hermes config set image_gen.model image-01
hermes config set image_gen.use_gateway false
```

When asked whether to allow tool override privileges, answer no.

## Manual Linux / macOS Install

Find your Hermes paths:

```bash
hermes config path
hermes config env-path
```

For a normal install, create:

```bash
mkdir -p ~/.hermes/plugins/image_gen/minimax
```

Copy these files into it:

```text
~/.hermes/plugins/image_gen/minimax/plugin.yaml
~/.hermes/plugins/image_gen/minimax/__init__.py
```

If `hermes config path` points somewhere else, use that config file's parent directory as the Hermes home, then create:

```text
<hermes-home>/plugins/image_gen/minimax/
```

Enable and select the provider:

```bash
hermes plugins enable image_gen/minimax
hermes config set image_gen.provider minimax
hermes config set image_gen.model image-01
hermes config set image_gen.use_gateway false
```

When asked whether to allow tool override privileges, answer no.

## Verify

List enabled user plugins:

```bash
hermes plugins list --plain --no-bundled
```

You should see the MiniMax plugin enabled.

Confirm image generation config:

```bash
hermes config show
```

For GitHub install, the enabled plugin entry may be `minimax`. For manual nested install, it may be `image_gen/minimax`. In both cases the important image generation config is:

```yaml
image_gen:
  provider: minimax
  model: image-01
  use_gateway: false
```

Start a new Hermes session and ask it to generate an image. The result is saved under Hermes' image cache, usually:

```text
<hermes-home>/cache/images/
```

## Optional Overrides

The plugin supports these optional environment variables:

```env
MINIMAX_IMAGE_MODEL=image-01
MINIMAX_IMAGE_BASE_URL=https://api.minimax.io/v1/image_generation
```

Most users should not need them.

## Notes

- The plugin reads local reference images only after Hermes' file-safety check.
- Local reference images are sent to MiniMax as data URIs.
- Public `http`, `https`, and `data:` image references are passed through directly.
- Generated images are saved as JPEG files in Hermes' image cache.
