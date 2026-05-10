# Building This Website Chat

This post explains how the website assistant works.

## Stack

- Streamlit for the UI
- OpenRouter as the LLM backend
- Markdown files as the content source

## Interaction model

The assistant can:

1. Look up relevant articles by keyword.
2. Fetch article content by slug.
3. Answer questions grounded in those article files.
