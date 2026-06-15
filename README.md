# 📚 BookToss v2

> Rebuild from scratch — searching multiple Seoul libraries at once with an AI agent.
> **This version swaps the OpenAI GPT-4o-mini brain for Upstage Solar.**

This branch (`v2-solar`) starts from an empty root and is built one step at a time
as a learning exercise. The original hackathon project is preserved for reference
under [`docs/v1/`](docs/v1/).

## Status

🚧 Building. See progress below.

| Step | What | Status |
|------|------|--------|
| 0 | Clean slate: orphan branch, v1 archived under `docs/v1/` | ✅ |

## Stack (planned)

- **LLM:** Upstage Solar (`solar-pro2`) via its OpenAI-compatible endpoint
- **Agent:** browser-use (drives each library's site)
- **Pipeline:** LangGraph (`resolve_catalog → search_book → parse_html`)
- **App:** Streamlit

## v1 reference

`docs/v1/` holds the original `app.py`, the `00_src/` LangGraph pipeline, the
`catalog_index.yaml` library map, and the hackathon write-up. We mine it for the
parts worth keeping (library URL config, HTML parsing rules) and rebuild the rest.
