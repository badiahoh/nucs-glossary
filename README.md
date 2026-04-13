# Nucs AI — Terminology Glossary

Internal glossary of nuclear medicine, theranostics, regulatory, and Nucs AI terms.
Self-contained static page hosted on GitHub Pages, with data sourced from Notion.

**Live URL:** https://badiahoh.github.io/nucs-glossary/

## Architecture

```
[Notion DB]  ──sync.py──▶  [terms.json]  ──fetched by──▶  [index.html]
   ▲                            ▲                              ▲
team edits             regenerated on demand            served via GitHub Pages
                                                        (or iframed anywhere)
```

Everything is portable. Move the repo, swap the host, embed elsewhere — only one or two values change.

## Files

| File | Purpose |
|---|---|
| `index.html` | The page (HTML + CSS + vanilla JS, fetches `terms.json`) |
| `terms.json` | Data — auto-generated from Notion |
| `assets/` | Logo + Axiforma fonts (travel with the page, no external deps) |
| `sync.py` | Regenerates `terms.json` from the Notion DB |
| `requirements.txt` | Python deps for `sync.py` (`requests`) |

## Editing terms

Edit the **Notion database** ([Terminology](https://www.notion.so/940438d6b6b24518b12871b28fb8715e)) — never edit `terms.json` by hand.

Properties:
- **Term** — the headword
- **Definition** — concise plain-language explanation
- **Category** — must match one of the 16 select options (controls which tab it appears under)
- **Synonyms** — comma-separated alternative names, abbreviations, common misspellings, related terms (these power the smart search)

## Syncing changes to the live page

**Easiest:** ask Claude (in this workspace) — "sync the glossary." Claude reads Notion via its connector, regenerates `terms.json`, commits, and pushes. Live within ~1 minute (GitHub Pages build).

**Manually (no Claude):**
```bash
# One-time setup:
# 1. Create a Notion integration: https://www.notion.so/my-integrations
# 2. Open Terminology DB in Notion → ... → Connections → add the integration
# 3. Save the secret token

export NOTION_TOKEN="secret_xxxxxxxxxx"
pip install -r requirements.txt
python sync.py
git commit -am "Sync glossary"
git push
```

## Embedding

The page is designed to be iframed. Anywhere you want it:

```html
<iframe src="https://badiahoh.github.io/nucs-glossary/"
        style="width:100%;height:100vh;border:0"
        title="Nucs AI Glossary"></iframe>
```

Currently embedded at: Webflow Test Site → `/internal/glossary` (unlisted).

## Moving the repo

When transferring from personal to org account (e.g., `badiahoh/nucs-glossary` → `nucs-ai/nucs-glossary`):

1. **GitHub:** Settings → Danger Zone → Transfer ownership. URLs auto-redirect.
2. **Update embed URL** wherever it's iframed (Webflow page settings).
3. **Or set up a CNAME** like `glossary.nucs.ai` pointing at GitHub Pages — then the embed URL never has to change again.

## Moving the Notion DB

If the Notion database moves to a different page or workspace, only one place needs updating:
- `sync.py` → `DATABASE_ID` constant at the top

The DB ID is in the Notion URL. The integration may need to be re-added on the new location.

## Local development

Open `index.html` in a browser directly (or via a static server like `python -m http.server`). It loads `terms.json` from the same directory — no build step.
