# AGENTS.md - Moldau Workshop Documentation

## Quick Start

This is a documentation repository for a vocational electronics prototyping workshop in Moldova (SAM Prototypenbau). It's not a code project—primary outputs are Markdown documents and generated HTML.

## Key Files

| File | Purpose |
|------|---------|
| `md2html.py` | Converts `.md` → print-ready `.html` |
| `Aktuell/Planung/Geraetelisten_Prototypenbau_Verifiziert.md` | Equipment list with prices (€, MDL) |
| `Aktuell/Planung/Geraetelisten_Prototypenbau_Multi.md` | Trilingual DE/EN/RO version |

## Running md2html.py

```bash
# Single file
python md2html.py "Aktuell/Planung/Geraetelisten.md"

# Output to specific directory
python md2html.py datei.md -o output/

# All files in folder
python md2html.py Aktuell/Planung/
```

## Important Patterns

- **Web searches** for Moldova suppliers: use `smadshop.md`, `max.od`, `mobishop.md`, `zorte.md`, `table.md` as search terms
- **Prices**: 1 EUR = 20 MDL (April 2026 exchange rate)
- **Equipment list**: Items with MDL sources preferred; € items = import from AT/DE

## Repo Structure

```
Moldau/
├── md2html.py                    # Main tool
├── Aktuell/
│   ├── Planung/              # Equipment lists, planning docs
│   ├── Projekte/            # Student project specs by class
│   └── Vorlagen/            # Templates
├── docs/                     # Jekyll site for public docs
└── Lehrplan/                # Curriculum docs
```

## What NOT to Do

- Don't run tests (there are none)
- Don't lint/typecheck (not applicable)
- Don't commit unless explicitly asked by user
- Don't create new files without asking first