# Streamlit Chat (Embed-Ready)

This app is now a **single-screen chat interface** intended to be embedded into the static site homepage via an `<iframe>`.

## What changed

- Multipage Streamlit navigation was removed.
- Chat UI was rebuilt into an iMessage-style thread (blue user bubbles, dark gray assistant bubbles).
- The assistant is restricted to markdown content inside the repository `content/` directory.
- `streamlit.toml` disables sidebar page navigation (`showSidebarNavigation = false`).

## Security scope

The content service now enforces a strict content boundary:

- Accessible files: `content/**/*.md`
- Not accessible: source code, `.env`, secrets, and any path outside `content/`

If `CONTENT_DIR` points outside `content/`, startup fails with a validation error.

## Local run

```bash
cd streamlit
source .venv/bin/activate
streamlit run src/app.py
```

## Embed from static site

Use an iframe URL like:

```text
https://YOUR-STREAMLIT-APP.streamlit.app/?embed=true
```

The root static `index.html` is already set up to embed this app.

## Cross-repo article regeneration

This repo includes a workflow that dispatches an event to the website repo when `content/**` changes on `main`:

- Workflow: `.github/workflows/dispatch-website-regeneration.yml`
- Event sent to: `sgoley/sgoley.github.io`
- Event type: `streamlit-content-updated`

Required secret in this repo:

- `WEBSITE_REPO_DISPATCH_TOKEN` (token able to dispatch events to `sgoley/sgoley.github.io`)

## Attribution

Highly inspired by [openrouter-streamlit-chat](https://github.com/a0w3b/openrouter-streamlit-chat) by [Anssi Ovaska](https://github.com/a0w3b).
